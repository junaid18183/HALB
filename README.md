HALB
===========

HALB is the wrapper script to install/setup/manage multiple haproxy configuration on the same server. Along with the Keepalived for easy failover. 

Dependencies
===========
Make sure you install the keepalived and haproxy.

> In redhat/centos systems you can
> install them using

    yum install -y keepalived 
    yum install -y heartbeat

Installation
============
You can install HALB using the pip/setuptools or install from tar.gz 

    pip install HALB
    python setup.py install 

This will install following files on your system

 - /usr/bin/lbtool  -- The actual wrapper lbtool script which you will be using
 - /etc/HALB/halb.conf -- The Configuration file for HALB to control the data location where HALB saves/checks for data.
 - /etc/HALB/DATA/*  -- Actual HALB files. 
 

The setup installs the sample configuration for you to start off present in /etc/HALB/DATA/{example.vig,real.dat,vip.dat}

Configuration
============
The Configuration file /etc/HALB/halb.conf controls follwing options

 - DC - the name of the DC, optional preset to DATA
 - HAPLB_HOME  - HOME for your HALB installation,the actual haproxy configuration is saved under this directory
 - HAPROXY -- PATH for haproxy binary 
 - KEEPALIVE_CONF -- Keepalived configuration file
 - VIP_DEVICE -- The device name to which keepalived will bind the the VIP

The lbtool will require following four directories under HAPLB_HOME/DC

 - dat - All .vig files, real.dat and
   vip.dat files are stored here  
 - bin - copies of haproxy binary for each
   individual haproxy  haproxy - home for all haproxy configuration  
   status - status directory for all backend nodes
----------
**Adding new configs:**

 - 
 - Create new vig file

Create new .vig file for the rotation under /etc/HALB/DATA/dat/ 
Ex: /etc/HALB/DATA/dat/test.vig (Replace test with the desired name)

    [root@lb1 lb]#  cat /etc/HALB/DATA/dat/test.vig
    keepalived: vid=51
    #Vip: www.test.com
    www.test.com: vip=www.test.com name=www.test.com dns=www.test.com
    www.test.com: port=80 vip_mode=http,https vip_maxconn=25000
    www.test.com: real=tiber1:80 #is

> The keepalived vid must be unique as
> its identification for vip group in
> keepalived configuration.
> 
> **Use Command to find the number of vid used in existing vig file.**

    grep -ir 'keepalived: vid='/etc/HALB/DATA/dat/*.vig | awk '{print $NF}'| sort

 - Add Vip info in vip.dat

Add vip information under /etc/HALB/DATA/dat/vip.dat 

    [root@lb1 lb]# cat /etc/HALB/DATA/dat/vip.dat
    www.test.com: vip=www.test.com ip=10.0.9.214

 - Add Vip info in vip.dat
Add real server information under /etc/HALB/DATA/dat/real.dat 

    [root@lb1 lb]# cat /etc/HALB/DATA/dat/real.dat
    tiber1: status=is name=tiber1 dns=tiber1.test.colo ip=10.0.7.54

> Before adding check if the ips/servers
> are present in the vip.dat and
> real.dat. If present then there is no
> need to add. Please avoid duplicate
> entries.

----------

> Use vig name as argument to lbtool

 


    [root@lb1 lb]# lbtool test
    example> help
    Valid Choices are :
                    exit|quit --> To exit the program
                    gen_conf|generate_conf --> To generate the Haproxy configuration
                    ha_vig --> start|stop|reload|restart|status the configuration."
                    gen_keep --> MASTER|BACKUP  genrates the Keepalived Configuration
                    is --> set the server status to In serving
                    oos --> set the server status to Out of serving
                    help --> show the valid commands.


For example below steps needs to be done in order


    [root@lb1 root]# lbtool test 
    
 

> Name of haproxy vig as argument to lb
> script.

    test >  generate_conf  
    
> Generates haproxy config file

    test >  gen_keep MASTER 
    

> Generates keepalived config for the
> new rotation.if role is MASTER it  the
> rotation will be active on this
> server. If BACKUP then it will receive
> traffic only when the MASTER server
> fails.

    

    test >  ha_vig start 
    

    Starts the haproxy config 

    test >  keep_init reload   
  
>  Reloads keepalived with newly updated
> config file.

    test > exit


**Adding new hosts to a config:**

Add new hosts to real.dat file. 

> Before adding check if the host is
> present in the file. If yes then do
> not add. We should avoid duplicate
> entries.

Add the host to the .vig file for the rotation. 

    [root@lb1 lb]# lb test 

> Name of haproxy vig as argument to lb
> script.

    test > is tiber1 

> Adds host tiber1 into rotation of
> haproxy config for test

    test >  generate_conf  
    test >  ha_vig restart 
    test > exit 

**Taking a host out of rotation:**


    [root@lb1 lb]# lb test
    test > oos tiber1 

  

> Takes host tiber1 out of rotation from
> haproxy config for test.

test >  generate_conf
test >  ha_vig restart
test > exit


#################################################
misc -
add net.ipv4.ip_nonlocal_bind = 1 in sysctl.conf so that keepalived can bind non local  ip's
