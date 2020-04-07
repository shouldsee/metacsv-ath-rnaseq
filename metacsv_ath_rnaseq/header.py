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
	def scandir(self,):
		return os.scandir(self)

def dict_dump_dir(obj, fn):
	this = dict_dump_dir
	if isinstance(obj, (dict,list)):
		fn = Path(fn).check_writable().makedirs_p()
		with open(fn/'_dir_type','w') as f:
			f.write(obj.__class__.__name__)
		if isinstance(obj, dict):
			if isinstance(obj, OrderedDict):
				with open(fn/'_dir_order','w') as f:
					f.write('\n'.join(obj.keys()))
			for k,v in obj.items():
				this(v, fn / k)
		elif isinstance(obj, (tuple,list)):
			for k,v in enumerate(obj):
				this(v, fn / str(k))				
	elif isinstance(obj, (str,int,float)):
		with open( fn,'w') as f: 
			f.write('%s,%s'%( obj.__class__.__name__, str(obj)))
	else:
		assert 0,("type not understood",type(obj),fn)


types = [
	('str',str),
	('int',int),
	('float',float),
	('list',list),
	('tuple',tuple),
	('dict',dict),
	('OrderedDict',OrderedDict),
]
types = dict(types)
def safe_eval(s,types=types):
	return types[s]
	# return eval(s)

# def common_open(fn,*a):

from tarfile import TarInfo, TarFile
class TarPath(object):
	def __init__(self, data):
		self.type  =  type(other)
		self.data  =  data
		# elif isinstance(self.data, TarFile):
		# 	return True
		# elif isinstance(self.data, TarInfo):
		# 	return True


# def PathLike(obj):
# 	if isinstance(obj,(TarFile,TarInfo)):
# 		return TarPath(obj)
# 	else:
# 		return obj


class PathLike(object):
	def __repr__(self):
		return 'PathLike(data={self.data!s}, type={self.type.__name__!s})'.format(**locals())
	def __str__(self):
		return self.data.__str__()
	def __init__(self, obj):
		self.index      =  None
		self.tarfile    =  None
		if isinstance(obj,(TarFile,TarInfo)):
			if isinstance(obj, TarFile):
				self.index = {info.name: PathLike(info) for info in obj.getmembers()}
				for info, v in self.index.items():
					v.tarfile = self
				# for info in self.index:
				# 	info.tarfile = self
			obj = obj
		else:
			obj = Path(obj)
		self.type       =  type(obj)
		self.data       =  obj
		self.cls        =  PathLike
		# self.tarfile    =  getattr(self.data,'tarfile',None)
		# self.data.index = None

	def extractfile(self,*a):
		return self.data.extractfile(*a)

	def exists(self):
		if isinstance(self.data, Path):
			return self.data.exists()
		elif isinstance(self.data, TarFile):
			return True
		elif isinstance(self.data, TarInfo):
			return True
		else:
			assert 0,(self.type,self.data)

	def open(self, *args):
		if isinstance(self.data, Path):
			return self.data.open(*args)
		elif isinstance(self.data, TarFile):
			assert 0
		elif isinstance(self.data, TarInfo):
			assert 'rb' in args,(self, args)
			return self.tarfile.extractfile(self.data)
			# .open(*args)
		else:
			assert 0,(self.type,self.data)

	def isfile(self):
		if isinstance(self.data, Path):
			return self.data.isfile()
		elif isinstance(self.data, TarFile):
			return False
		elif isinstance(self.data, TarInfo):
			return self.data.isfile()
		else:
			assert 0,(self.type,self.data)

	def isdir(self):
		if isinstance(self.data, Path):
			return self.data.isdir()
		elif isinstance(self.data, TarFile):
			return True
		elif isinstance(self.data, TarInfo):
			return self.data.isdir()
		else:
			assert 0,(self.type,self.data)

	def basename(self):
		if isinstance(self.data, Path):
			return os.path.basename(self.data)
		elif isinstance(self.data, TarInfo):
			return self.cls(os.path.basename(self.data.name))
		else:
			assert 0,(self.type,self.data)

	def listdir(self):
		if isinstance(self.data, Path):
			return self.data.listdir()
		elif isinstance(self.data, TarFile):
			fs = []
			for k, info in self.index.items():
				if not os.path.dirname(k):
					fs.append(info)
			return fs					
		elif isinstance(self.data, TarInfo):
			fs = []
			for k, info in self.tarfile.index.items():
				if os.path.dirname(k)== self.data.name:
					fs.append(info)
			return fs
		else:
			assert 0,(self.type,self.data)
	def scandir(self,):
		return os.scandir(self.data)
	def __truediv__(self,other):
		if isinstance(self.data, Path):
			return self.data / other
		elif isinstance(self.data, TarFile):
			return self.index[other]
		elif isinstance(self.data, TarInfo):
			name = self.data.name+'/'+other
			return self.tarfile.index[name]

from pprint import pprint
import os
def _path_join(fn,x):
	return "%s/%s"%(fn,x)
def dict_load_dir(fn):
	fn = Path(fn)
	if not fn.exists():
		raise Exception("Path %s does not exists" % fn)
	elif fn.isfile():
		with fn.open('rb') as f:
			buf = f.read().decode()

			cls, buf = buf.split(',',1)
			cls = safe_eval(cls)
			obj = cls(buf)
	elif fn.isdir():
		with Path(_path_join(fn,'_dir_type')).open('rb') as f:
			typename = f.read().decode().strip()
			cls = safe_eval(typename)
		# fs = list(fn.scandir())
		# fs = [Path(x.name) for x in fs]		
		fs = [Path(x.name) for x in fn.scandir()]
		fs = [x for x in fs if x not in ['_dir_type','_dir_order']]
		if cls == list:
			obj = [None] * len(fs)
			for x in fs:
				_x = _path_join(fn,x)
				v =  dict_load_dir( _x)
				obj.__setitem__( int( x ), v )
		elif issubclass( cls, dict):
			obj = cls()
			# if issubclass(cls, OrderedDict):
			if cls is OrderedDict:
				with (fn/'_dir_order').open('rb') as f:
					od = f.read().decode().splitlines()
					assert set(fs) == set(od),pprint((fs,od))
					fs = od
			for x in fs:
				_x = _path_join(fn,x)
				v = dict_load_dir(_x)
				obj.__setitem__( x,  v )
		else:
			raise RoutineTypeUndefined(cls)
	return obj

def reloader():
	from importlib import reload; import metacsv_ath_rnaseq.header; reload(metacsv_ath_rnaseq.header); from metacsv_ath_rnaseq.header import dict_load_dir 
	# %lprun -f dict_load_dir dict_load_dir("/tmp/shouldsee-metacsv-ath-rnaseq-c7d8315/DATABASE/")
	# %lprun -f dict_load_dir dict_load_dir("/tmp/shouldsee-metacsv-ath-rnaseq-c7d8315/DATABASE/")
