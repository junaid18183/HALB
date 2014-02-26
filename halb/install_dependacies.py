#! /usr/bin/python

import yum
yb=yum.YumBase()
#yb.conf.cache = 1
#installed = yb.rpmdb.returnPackages()
#print installed

packages = ['keepalived','haproxy']

for package in packages:
        if yb.rpmdb.searchNevra(name=package):
                print "%s is installed" %(package)
        else:
                print "Installing %s" %(package)
                yb.install(name=package)
                yb.resolveDeps()
                yb.buildTransaction()
yb.processTransaction()
