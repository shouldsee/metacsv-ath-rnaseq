
def test_main():
	from pprint import pprint
	from header import dict_dump_dir,dict_load_dir,Path
	d = {
	'a':{'b':list(range(5))},
	'x':['something', {'other':'stuff'}]
	}
	fn = '_temp_dir'
	dict_dump_dir(d,fn)
	d_load = dict_load_dir(fn)
	assert d == d_load, pprint((d,d_load))

# if __name__ == '__main__':
# 	test_main()