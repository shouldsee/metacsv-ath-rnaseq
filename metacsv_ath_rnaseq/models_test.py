
# from meta import fetch_ncbi_sra_samples
from models import LocalSample
import xmltodict
from models import tree_from_dict
from _fetch import fetch_ncbi_sra_samples


def test_main():
	index = 'ERS214143,ERS214131,DRS007602,DRS007600,DRS007601'.split(',')
	buf = fetch_ncbi_sra_samples(index,  'fg368@cam.ac.uk')
	# jdata = xmltodict.parse(buf)
	jdata = xmltodict.parse( buf,force_list=lambda path,key,value: True)

	samples = jdata['EXPERIMENT_PACKAGE_SET'][0]['EXPERIMENT_PACKAGE']
	samples = [ LocalSample.from_ncbi_efetch({'SAMPLE':sample['SAMPLE']}) for sample in samples]

	for sample in samples:
		sample_restored = LocalSample.from_simple_dict(sample.to_simple_dict())
		assert  sample_restored== sample

	x = tree_from_dict(dict(a={}))
	x['a']['b']

	print('[passed]%s'%__file__)
if __name__ == '__main__':
	test_main()
