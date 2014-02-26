from distutils.core import setup
from glob import glob
import os,sys

setup(
    name='HALB',
    version='0.1.1',
    url='https://github.com/junaid18183/HALB',
    author='Juned Memon',
    author_email='junaid18183@gmail.com',
    license='LICENSE.txt',
    description='Haproxy and Keepalived base multiple HA on same server',
    packages=['halb'],
    scripts=glob("bin/*"),
    include_package_data=True,
    package_dir={'halb':'halb'},
    #data_files=[('config',['conf/config.py'])], #This installs in /usr/config
    #data_files=['conf/config.py'],  #This installs in /usr
    #data_files=[(os.path.join(sys.prefix, 'juned', 'halb'), glob("conf/*"))],
    data_files=[
		('/etc/HALB', ['conf/halb.conf']),
		('/etc/HALB/DC1/dat', ['example/dat/example.vig','example/dat/real.dat','example/dat/vip.dat']),
	       ],
    long_description=open('README.md').read(),
    install_requires=[
        "argparse",
	"ConfigParser",
    ],
)
