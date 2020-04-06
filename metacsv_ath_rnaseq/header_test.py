
from header import dict_dump_dir,dict_load_dir,Path
from collections import OrderedDict
from pprint import pprint
import subprocess 
d = {
'a':{'b':list(range(5))},
'x':['something', {'other':'stuff'}],
'od':OrderedDict([('hi','hihi'),('blah','foo')]),
}
def test_main():
	fn = '_temp_dir'
	dict_dump_dir(d,fn)
	d_load = dict_load_dir(fn)
	assert d == d_load, pprint((d,d_load))

def test_tar():
	import tarfile
	# subprocess.check_output('tar -cvzf {fn}.tgz {fn}/*'.format(**locals()), shell=True)	
	with Path(fn) as _:
		subprocess.check_output('tar -cvzf ../{fn}.tgz *'.format(**locals()), shell=True)	

	d_load = dict_load_dir(tarfile.open(fn+'.tgz','r'))
	assert d == d_load, pprint((d,d_load))

if __name__ == '__main__':
	test_main()