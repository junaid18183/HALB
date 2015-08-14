from distutils.core import setup
from glob import glob
import platform,sys

##################################################################################
#This Portion tries to to install the required packages on Ubuntu and Centos/Redhat Based Systems
packages = ['keepalived','haproxy']
if platform.system() == 'Linux':
        name=platform.dist()[0]
        if name == 'Ubuntu':
		import apt
		cache = apt.cache.Cache()
		cache.update()
		for package in packages:
		        pkg = cache[package]
		        if pkg.is_installed:
                		print "%s is already installed" %(package)
		        else:
                		pkg.mark_install()

		try:
		        cache.commit()
		except Exception, arg:
		        print >> sys.stderr, "Sorry, package installation failed [{err}]".format(err=str(arg))

#If System is Centos/Redhat use YUM

        elif name =='centos' or  name == 'redhat' :
		import yum
		yb=yum.YumBase()
		#yb.conf.cache = 1
		#installed = yb.rpmdb.returnPackages()
		#print installed
		for package in packages:
	        	if yb.rpmdb.searchNevra(name=package):
        	        	print "%s is installed" %(package)
		        else:
        		        print "Installing %s" %(package)
                		yb.install(name=package)
	                	yb.resolveDeps()
		       	        yb.buildTransaction()
			yb.processTransaction()
else:
	print "This system does not seems to be Linux, so exiting"

##################################################################################


setup(
    name='HALB',
    version='0.1.3',
    url='https://github.com/junaid18183/HALB',
    author='Juned Memon',
    author_email='junaid18183@gmail.com',
    license='LICENSE.txt',
    description='Haproxy and Keepalived base multiple HA on same server',
    packages=['halb'],
    scripts=glob("bin/*"),
    include_package_data=True,
    package_dir={'halb':'halb'},
    data_files=[
		('/etc/HALB', ['conf/halb.conf']),
		('/etc/HALB/DATA/dat', ['example/dat/example.vig','example/dat/real.dat','example/dat/vip.dat']),
	       ],
    long_description=open('README.md').read(),
    install_requires=[
        "argparse",
	"ConfigParser",
    ],
)
