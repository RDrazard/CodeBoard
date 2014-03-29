#!/usr/bin/python

import os

def xfile(afile, global_vars=None, local_vars=None):
	with open(afile) as f:
		code = compile(f.read(), "somefile.py", 'exec')
		exec(code, global_vars, local_vars)

virtenv = os.environ['APPDIR'] + '/virtenv/'
os.environ['PYTHON_EGG_CACHE'] = os.path.join(virtenv, 'lib/python3.3/site-packages')
virtualenv = os.path.join(virtenv, 'bin/activate_this.py')
try:
    xfile(virtualenv, dict(__file__=virtualenv))
except IOError:
    pass

from twtapp import application
