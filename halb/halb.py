import shutil,re,os,pprint,commands
from time import strftime
#from config import * 
from ConfigParser import SafeConfigParser

parser = SafeConfigParser()
parser.read('/etc/HALB/halb.conf')

HAPLB_HOME=parser.get('halb', 'HAPLB_HOME')
DC=parser.get('halb', 'DC')
HAPROXY=parser.get('halb', 'HAPROXY')
KEEPALIVE_CONF=parser.get('halb', 'KEEPALIVE_CONF')
VIP_DEVICE=parser.get('halb', 'VIP_DEVICE')


HAPLB_BASE=HAPLB_HOME+DC
HA_DAT=HAPLB_BASE+"/dat/"
HA_CONF=HAPLB_BASE+"/haproxy/"
HA_STATUS_DIR=HAPLB_BASE+"/status/"
HA_BIN=HAPLB_BASE+"/bin/"
VIP=HA_DAT+"vip.dat"
REAL=HA_DAT+"real.dat"


for directory in HA_DAT,HA_CONF,HA_STATUS_DIR,HA_BIN:
	if not os.path.exists(directory):
	    os.makedirs(directory)

##########################################################
#### Now I am not using template and so this function#######
def genconf(vig_name):
	tpl_path="template/"
	file="/tmp/haproxy.tmp"
	shutil.copy2(tpl_path+'haproxy.http.begin.tpl', file)
	cmd = "sed -i 's/$name/"+vig_name+"/g' "+file
	os.system (cmd)

##########################################################
def addheader(vig_name,maxconn=25000,contimeout=5000,clitimeout=50000,srvtimeout=50000,auth='admin'):
	header ="""
global
        log 127.0.0.1   local0
        log 127.0.0.1   local1 notice
        #log loghost    local0 info
        maxconn 25000
        #debug
        #quiet
        #user prod
        #group prod
        # Otherwise add users
        stats socket /var/run/%s.sock level admin

defaults
        log     global
        mode    http
        option  tcplog
        option  dontlognull
        option 	httpclose
        retries 3
        option 	redispatch
        maxconn 	%d
        timeout connect      %d
        timeout client      %d # maximum inactivity time on the client side
        timeout server      %d # maximum inactivity time on the server side
        stats enable
        stats auth admin:%s ##Auth user pass

#begin block end
""" % (vig_name,maxconn,contimeout,clitimeout,srvtimeout,auth)

	return  header
##########################################################

def addvip(vip_name,vip,port,vip_maxconn,vip_mode):
	block = """
#Configuration for %s

 listen VIP:%s:%s:%s
    bind %s:%s
    log    global
    maxconn %s
    mode %s
    option forwardfor
    balance leastconn
""" % ( vip_name,vip_name,vip,port,vip,port,vip_maxconn,vip_mode)

	return block
##########################################################

def addbackend(oos,name,ip,port):
	backend = "\t%s server REAL:%s:%s:%s %s:%s check\n" % (oos,name,ip,port,ip,port)
	return backend

##########################################################
def get_vip_data(vig_name):
        VIG=HA_DAT+vig_name+".vig"
        vips={}
	real={}
	try:
	   f_VIG=open(VIG,"r")
           for vig_line in f_VIG:
                if re.search("vip=", vig_line):
                        vig_line=vig_line.split() ###sample line="data_sid_sortdb: vip=data_sid_sortdb name=data_sid_sortdb dns=data_sid_sortdb loc=cs"
                        vip_name=vig_line[0][:-1]
                        vig_dns=re.sub("dns=","",vig_line[3])
                        vips[vip_name]={}
                        vips[vip_name]["vig_dns"]=vig_dns
                        f_VIP=open(VIP,"r")
                        for vip_line in f_VIP:
                                if re.search(vip_name, vip_line):
                                        vip=vip_line.split("=")[2][:-1] ### striping last character since new line
                                        vips[vip_name]["vip"]=vip
                        f_VIP.close

                elif re.search("port=", vig_line):
                        vig_line=vig_line.split()   ###sample line="data_sid_sortdb: port=9004 vip_mode=http vip_maxconn=25000
                        vip_name=vig_line[0][:-1]
                        vip_port=re.sub("port=","",vig_line[1])
                        vip_mode=re.sub("vip_mode=","",vig_line[2])
                        vip_maxconn=re.sub("vip_maxconn=","",vig_line[3])
                        vips[vip_name]["vip_mode"]=vip_mode
                        vips[vip_name]["vip_maxconn"]=vip_maxconn
                        vips[vip_name]["vip_port"]=vip_port

       
	   f_VIG.close()
	   return vips
	except IOError as e:
                print "I/O error({0}): {1}".format(e.errno, e.strerror)
                exit(2)
###########################################################
def get_real_data(vig_name,vip_name):
        VIG=HA_DAT+vig_name+".vig"
        real={}
        f_VIG=open(VIG,"r")
        for vig_line in f_VIG:
	    	if re.search(vip_name+": real=", vig_line):
                	vig_line=vig_line.split()###sample line="data_sid_sortdb: real=ggvaapp23:9004 #is"
	                vip_name=vig_line[0][:-1]
        	        backend=re.sub("real=","",vig_line[1])
                	backend,backend_port=backend.split(":")
			real[backend]={}
			real[backend]["name"]=backend
                	real[backend]["port"]=backend_port
	                f_REAL=open(REAL,"r")
        	        for real_line in f_REAL:
                		if re.search("name="+backend, real_line):
                        		ip=real_line.split()[4]
                        		ip=ip.split("=")[1]
	                        	real[backend]["ip"]=ip
        	        f_REAL.close()

        f_VIG.close()
	#print real
        return real
###########################################################
def gen_conf (vig_name):
	cfg=HA_CONF+vig_name+".cfg"
        binary=HA_BIN+"haproxy_"+vig_name
	if not os.path.isfile(binary):
		shutil.copy2(HAPROXY,binary)
		print "The Haproxy binary for this vig is %s " %binary
	if os.path.isfile(cfg):
		cfg_back=cfg+".bak"
		shutil.copy2(cfg,cfg_back)
		print "Preserved the backup of %s at %s" %(cfg,cfg_back)
	if os.path.isfile(HA_DAT+vig_name+".vig"):
		print "Generating Configuration of %s at %s" % (vig_name,cfg) 
        	fo = open(cfg, "wb")
        	header=addheader(vig_name,auth='Super$ecRet')
        	fo.write(header);
		print "Written Header section successfully"
        	vips=get_vip_data(vig_name)
		for vip_name in vips:
			print "\tAdding VIP section for %s" % (vip_name)
        		vip_block=addvip(vip_name,vips[vip_name]["vip"],vips[vip_name]["vip_port"],vips[vip_name]["vip_maxconn"],vips[vip_name]["vip_mode"])
        		fo.write(vip_block)
			real=get_real_data(vig_name,vip_name)
			for backend in real: 
				print "\t\tAdding Backend %s for %s" % (backend,vip_name)
				oos=""
				status=get_server_status(vig_name,backend)
				if status == 'oos':
					oos = "#oos"
				backend_block=addbackend(oos,backend,real[backend]["ip"],real[backend]["port"])
	        		fo.write(backend_block)
				update_status_file(vig_name,backend,status)
		print "Completed."
        	fo.close()
	else:
		print "Error:vig file %s.vig does not exist." %(HA_DAT+vig_name)
	 	exit(2)
##########################################################
def ha_vig_start(vig_name):
		binary=HA_BIN+"haproxy_"+vig_name
		cfg=HA_CONF+vig_name+".cfg"
		pid="/var/run/"+vig_name+".pid"
		ha_vig_configtest(vig_name)
	        cmd=binary+" -D -f "+cfg+" -p "+pid
		status, output = commands.getstatusoutput(cmd)
		if not status == 0 :
                       	print "Error starting the configuration %s" %(cfg)
		else:
			print "Haproxy Configuration started successfully."
##########################################################
def ha_vig_stop(vig_name):
	cmd="cat /var/run/"+vig_name+".pid | xargs kill"
	print "Stopping the Haproxy Process for %s." %(vig_name)
	status, output = commands.getstatusoutput(cmd)
	if status == 0 :
		os.remove("/var/run/"+vig_name+".pid")
		print "Done"
	else:
		print "There seems to be problem Stopping Haproxy process for %s" %(vig_name)
	#print vig_name,command
	
##########################################################
def ha_vig_configtest(vig_name):
	binary=HA_BIN+"haproxy_"+vig_name
        cfg=HA_CONF+vig_name+".cfg"
        pid="/var/run/"+vig_name+".pid"
	cmd=binary+" -c -q -f "+cfg
        status, output = commands.getstatusoutput(cmd)
        if not status == 0 :
	        print "Errors in configuration file %s" %(cfg)
		exit
	else:
		print "Configtest Passed Successfully"
	return status	
##########################################################
def ha_vig_reload(vig_name):
	binary=HA_BIN+"haproxy_"+vig_name
        cfg=HA_CONF+vig_name+".cfg"
        pid="/var/run/"+vig_name+".pid"
        ha_vig_configtest(vig_name)
	print "Reloading the Haproxy Process for %s." %(vig_name)
        cmd=binary+" -D -f "+cfg+" -p "+pid+" -sf $(cat "+pid +")"
	print "Reloading the Haproxy Process for %s." %(vig_name)
        if not status == 0 :
           print "Error starting the configuration %s" %(cfg)
        else:
     	   print "Done."

	
##########################################################
def ha_vig_restart(vig_name):
	ha_vig_configtest(vig_name)
	print "Restarting the Haproxy Process for %s." %(vig_name)
	ha_vig_stop(vig_name)
	ha_vig_start(vig_name)
##########################################################
def ha_vig_status(vig_name):
	cfg=HA_CONF+vig_name+".cfg"
	pid="/var/run/"+vig_name+".pid"
	cmd="pgrep -f " +pid+"$"
	status, output = commands.getstatusoutput(cmd)
	if not status == 0 :
           print "Haproxy Process not running for %s" %(cfg)
        else:
           print "Haproxy for %s is running (pid=%s)" %(vig_name,output)
##########################################################
def keep_init_header(vig_name,state,vip_dev,virtual_router_id,priority):
	header ="""
# %s

	vrrp_script chk_%s { # Requires keepalived-1.1.13
        	script "killall -0 haproxy_%s" # widely used idiom
	        interval 5 # check every 2 seconds
        	weight 2 # add 2 points of prio if OK
	        fall 2    # requires 2 failures for KO
        	rise 2   # requires 2 successes for OK
		}
	vrrp_instance VI_%s {
        	state %s
		interface %s
	        virtual_router_id %s
        	priority %d
	        advert_int 1
        	smtp_alert
	        authentication {
        		auth_type PASS
		        auth_pass 1111
		        }

	virtual_ipaddress {
""" % (vig_name,vig_name,vig_name,vig_name,state,vip_dev,virtual_router_id,priority)

        return  header
##########################################################
def keep_init_footer(vig_name):
        header ="""
		}
	track_script {
        	chk_%s
		}
		}
## conf end for %s
""" % (vig_name,vig_name)
        return  header	  

##########################################################
def find_virtual_router_id(vig_name):
	VIG=HAPLB_BASE+"/dat/"+vig_name+".vig"
        try:
        	f_VIG=open(VIG,"r")
	        for line in f_VIG:
        	        if re.search("keepalived", line):
                	        i=line.split('vid=')[1]###keepalived: vid=3,4" or ###keepalived: vid=5"
				id=i.split(',')[0]
		f_VIG.close()
        except IOError as e:
                print "I/O error({0}): {1}".format(e.errno, e.strerror)
                exit(2)
        return id
##########################################################
def keep_init_gen (vig_name,state):
	if state == 'MASTER':
		priority=101
	if state == 'BACKUP':
		priority=100
        #cfg="/tmp/juned.cfg"
        cfg=KEEPALIVE_CONF
        if os.path.isfile(cfg):
                cfg_back=cfg+".back-"+strftime("%d-%b-%Y")
                shutil.copy2(cfg,cfg_back)
                print "Preserved the backup of %s at %s" %(cfg,cfg_back)
		virtual_router_id=find_virtual_router_id(vig_name)
                fo = open(cfg, "a")
                header=keep_init_header(vig_name,state,VIP_DEVICE,virtual_router_id,priority)
                fo.write(header);
                print "Written Header section successfully"
		vips=get_vip_data(vig_name)
		for vip_name in vips:
			data="\t\t%s dev %s"%(vips[vip_name]["vip"],VIP_DEVICE)
			fo.write(data);
		print "Written VIP data successfully"
                footer=keep_init_footer(vig_name)
		fo.write(footer)
		print "Written Footer section successfully"
##########################################################
def is_valid_backend (vig_name,server):
        VIG=HA_DAT+vig_name+".vig"
	present=False
        try:
                f_VIG=open(VIG,"r")
                for line in f_VIG:
                        if re.search(server, line):
                                present=True
                f_VIG.close()
        except IOError as e:
                print "I/O error({0}): {1}".format(e.errno, e.strerror)
                exit(2)
	return present
##########################################################
def change_status (vig_name,server,status):
	#First confirm that the server is present in vig file
        present=is_valid_backend(vig_name,server)
	if present :
		update_status_file(vig_name,server,status)
	else :
		print "Server not present in VIG file"
#Done
##########################################################
def update_status_file(vig_name,server,status):
	if not os.path.exists(HA_STATUS_DIR+vig_name):
       		os.makedirs(HA_STATUS_DIR+vig_name)

	old_status = get_server_status(vig_name,server)
	if old_status == status :
		print "Server %s is already in %s state" %(server,status)
	else :
		status_file=HA_STATUS_DIR+vig_name+"/"+server
		try:
        		status_f = open(status_file, "wb")
			status_f.write(status)
			print "Server %s is  set to %s" %(server,status)	
        	        status_f.close()
	        except IOError as e:
        	        print "I/O error({0}): {1}".format(e.errno, e.strerror)
                	exit(2)
        return True
##########################################################
def get_server_status(vig_name,server):
        status_file=HA_STATUS_DIR+vig_name+"/"+server
        if not os.path.exists(status_file):
		return "is"
        try:
                status_f = open(status_file, "r")
		for line in status_f:
	                status=line
                status_f.close()
        except IOError as e:
                print "I/O error({0}): {1}".format(e.errno, e.strerror)
                exit(2)
        return status
##########################################################
def update_server_status(status_file,status,server):
	try:
                        status_f = open(status_file, "wb")
                        status_f.write(status)
                        print "Server %s is  set to %s" %(server,status)
                        status_f.close()
        except IOError as e:
                        print "I/O error({0}): {1}".format(e.errno, e.strerror)
                        exit(2)
        return True
##########################################################
