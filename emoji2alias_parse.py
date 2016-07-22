#! /usr/bin/python


import os
import re
import sys


source = "emoji2alias.data"

if not os.path.isfile(source):
    print "Can't find %s. Exiting." % source
    sys.exit(0)


try:
    with open(source) as f:
        content = f.readlines()
        for i in content:
            if len(i) == 1:
                continue
            x = re.split('^(\w+).*# (.*)',i)
            print "    u'\\U%s': u'[%s]'," % (x[1].zfill(8), x[2].lower())

except IOError as e:
    print "Nope!  %s" % e
    sys.exit(1)

