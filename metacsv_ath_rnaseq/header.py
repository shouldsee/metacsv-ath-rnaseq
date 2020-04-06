import os
from path import Path as _Path
from collections import OrderedDict

class RoutineTypeUndefined(Exception):
	pass

class Path(_Path):
	def check_writable(self):
		self.access(os.W_OK)
		return self
	def dump_dict(obj):
		return dict_dump_dir(obj, self)

def dict_dump_dir(obj, fn):
	this = dict_dump_dir
	if isinstance(obj, (dict,list)):
		fn = Path(fn).check_writable().makedirs_p()
		with open(fn/'_dir_type','w') as f:
			f.write(obj.__class__.__name__)
		if isinstance(obj, dict):
			for k,v in obj.items():
				this(v, fn / k)
		elif isinstance(obj, list):
			for k,v in enumerate(obj):
				this(v, fn / str(k))				
	elif isinstance(obj, (str,int,float)):
		with open( fn,'w') as f: 
			f.write('%s,%s'%( obj.__class__.__name__, str(obj)))
	else:
		assert 0,("type not understood",type(obj),fn)


def safe_eval(s):
	return eval(s)

# def common_open(fn,*a):


def dict_load_dir(fn):
	this = dict_load_dir
	fn = Path(fn)
	if not fn.exists():
		raise Exception("Path %s does not exists" % fn)
	elif fn.isfile():
		with fn.open('r') as f:
			buf = f.read()
			cls, buf = buf.split(',',1)
			cls = safe_eval(cls)
			obj = cls(buf)
	elif fn.isdir():
		typename = open(fn/'_dir_type','r').read().strip()
		cls = safe_eval(typename)
		fs = [x for x in fn.listdir() if x.basename()!='_dir_type']
		if cls == list:
			obj = [None] * len(fs)
			[obj.__setitem__( int( x.basename()),  this(x) ) for x in fs]
		elif issubclass( cls, dict):
			obj = cls()
			[obj.__setitem__( x.basename(),  this(x) ) for x in fs ]
		else:
			raise RoutineTypeUndefined(cls)
	return obj