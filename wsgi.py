#!/usr/bin/python

import os

def xfile(afile, globalz=None, localz=None):
    with open(afile, "r") as fh:
        exec(fh.read(), globalz, localz)

virtenv = os.environ['APPDIR'] + '/virtenv/'
os.environ['PYTHON_EGG_CACHE'] = os.path.join(virtenv, 'lib/python3.3/site-packages')
virtualenv = os.path.join(virtenv, 'bin/activate_this.py')
try:
    xfile(virtualenv, dict(__file__=virtualenv))
except IOError:
    pass

from twtapp import application
