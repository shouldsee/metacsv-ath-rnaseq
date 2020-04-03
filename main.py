 ### reference: https://www.ncbi.nlm.nih.gov/books/NBK25499 

from path import Path
import pickle
from spiper.types import Flow,Node, File, LinkFile
import pandas as pd
import lxml.etree 
from metacsv_ath_rnaseq.models import LocalSample

from eutils._internal.client import Client, ESearchResult
import io,os
import warnings
def fetch_ncbi_sra_samples(index, email, api_key= None):
	'''
	Take a list of SRA PRIMARY_ID and returns xml output
	'''

	ec = Client(api_key=(api_key or os.environ.get("NCBI_API_KEY", None)))
	ec._qs.email = email 

	esr = ec._qs.esearch(
		dict(db='sra',
		rettype='xml',
		retmax = len(index),	
		term=' OR '.join(['%s [ACCN]'%x for x in  index])))
	esr = ESearchResult(esr)

	if len(esr.ids)!=len(index):
		warnings.warn('[WARN] id/acc length mismathcing %d/%d'%(len(esr.ids),len(index)))
	ids = esr.ids

	esr = ec._qs.efetch(dict(
		id=','.join(map(str,ids)),
		db='sra',
		retmax=len(ids),
		))
	return io.BytesIO(esr)
	

def _read_pandas(input_pk,**kw):
	if input_pk.endswith('pk'):
		df = pd.read_pickle(input_pk,**kw)
	elif input_pk.endswith('csv'):
		df = pd.read_csv(input_pk,index_col=[0],**kw)
	elif input_pk.endswith('tsv'):
		df = pd.read_csv(input_pk,index_col=[0],sep='\t',**kw)
	elif input_pk.endswith('list'):
		df = pd.read_csv(input_pk,index_col=[0],header=None).index
	else:
		assert 0, (input_pk,)
	return df


# def xml_tostring(self, encoding='utf8',pretty_print=True,**kw):
# 	if not isinstance(self, (lxml.etree._Element,lxml.etree._ElementTree)):
# 		self = self._xml_root
# 	else:
# 		pass
# 	return lxml.etree.tostring(self, pretty_print=pretty_print,encoding=encoding,**kw).decode(encoding)

# def _pprint(self):
# 	print(xml_tostring(self,pretty_print=True))

# from eutils._internal.xmlfacades.base import Base
# class ESummaryResult(Base):
# 	_root_tag = 'eSummaryResult'
# class EFetchResult(Base):
# 	_root_tag = 'eFetchResult'

def fetch_AccList_as_Xml(self,prefix,input=File,_output=['xml']):
	print('[fetching] %s sra records'%len(list(open(input,'r').read().rstrip().splitlines())))
	index = _read_pandas(input,header=None).index
	esr   = fetch_ncbi_sra_samples(index, 'fg368@cam.ac.uk')
	with open(self.output.xml,'wb') as f:
		f.write(esr.read())


### [ToDo]: embedded flow in spiper is buggy
# @Flow
def fetch_AccList_as_SimpleCsv(self, prefix, input = File, _output=[
	'csv']):
	import os,io
	import warnings
	from eutils._internal.client import Client, ESearchResult
	import xmltodict
	import json
	# if not self.runner.is_meta_run:
		# print('[fetching] %s sra records'%len(list(open(input,'r').read().rstrip().splitlines())))
	# index = _read_pandas(input,header=None).index
	# curr = self.runner(fetch_AccList_as_Xml, self.prefix_named, input)
	print('[fetching] %s sra records'%len(list(open(input,'r').read().rstrip().splitlines())))

	index = _read_pandas(input,header=None).index
	esr   = fetch_ncbi_sra_samples(index, 'fg368@cam.ac.uk')
	jdata = xmltodict.parse( esr,force_list=lambda path,key,value: True)
	if 1:
	# if not self.runner.is_meta_run:
		samples = jdata['EXPERIMENT_PACKAGE_SET'][0]['EXPERIMENT_PACKAGE']
		samples = [ LocalSample.from_ncbi_efetch(expt_package) for expt_package in samples]

		run_ids = sum([x.dict()['RUN_ID_LIST'] for x in samples],[])
		missing = [x for x  in index if x not in run_ids]
		assert len(missing)==0,misisng

		df = pd.concat([pd.Series(x.to_simple_dict()) for x in samples],axis=1).T
		df = df.drop_duplicates(subset=['SAMPLE_ID'])
		# .set_index('ID')
		df.to_csv(self.output.csv, index=0)
		print('[fetching] got %s records'%len(df) )
	return self


def patch_by_hand( self,prefix, old_csv= File, new_csv = File, _output=['csv']):
	old = _read_pandas(old_csv)
	new = _read_pandas(new_csv)
	for k in new.index:
		old.loc[k] = new.loc[k]
	old.to_csv(self.output.csv, index=1)
	# assert 0

def patch_by_script(self,prefix,old_csv=File,   script=File, _output=['csv','log']):
	res = LoggedShellCommand([script,'>',self.output.csv],self.output.log)



import lxml.etree as etree
from spiper.types import LinkFile
@Flow
def main(self, prefix, csv_file = File,  
	script = File,
	hand_patch_csv = File, _output=['csv']):
	test_csv_file = fn = csv_file+'.test.csv'
	
	if not test_csv_file.isfile():
		with open(csv_file,'r') as f:
			with open(fn,'w') as fo:
				fo.write('\n'.join(f.read().splitlines()[:100]))
	self.config_runner(tag='test')(fetch_AccList_as_SimpleCsv,       prefix, test_csv_file) 
	
	curr = self.config_runner(tag='production')(fetch_AccList_as_SimpleCsv, prefix,  csv_file) 
	if not script.endswith('NULL'):
		curr = self.config_runner(tag='production')(patch_by_script,               prefix,  csv_file,         script)
	curr = self.config_runner(tag='production')(patch_by_hand,                 prefix,  curr.output.csv,  hand_patch_csv)
	self.runner(LinkFile, self.output.csv, curr.output.csv)
	return self

if __name__ == '__main__':	
	from spiper.runner import get_changed_files,cache_run
	from pprint import pprint
	import sys
	tups = (main,  
		'$PWD/_build/root', 
		'$PWD/metacsv_ath_rnaseq/root.dump_columns.csv',
		'NULL',
		'$PWD/metacsv_ath_rnaseq/root.hand_patch.csv',)
	runner = get_changed_files
	pprint(runner(*tups))
	runner = cache_run
	if '--run' in sys.argv:
		curr = runner(*tups)
		runner(LinkFile,'current.csv',curr.output.csv)
		# for runner in [get_changed_files, ]