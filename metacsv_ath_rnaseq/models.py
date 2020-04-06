
import warnings
from typing import List,Dict
from collections import OrderedDict
from pydantic import BaseModel
from collections import defaultdict
from metacsv_ath_rnaseq.header import dict_dump_dir, dict_load_dir

def tree(): return defaultdict(tree)
def tree_from_dict(data):
	'''
	Recursively casting dict to trees
	ToDo: cast list to safe list as well
	'''

	if isinstance(data,list):
		d = [None] * len(data)
		for k, v in enumerate(data):
			d[k] = tree_from_dict(v)
	elif isinstance(data,dict):		
		d = tree()
		for k,v in data.items():
			# d[k] = _cast(v)
			d[k] = tree_from_dict(v)
	else:
		d = data
	return d

class NcbiSample(BaseModel):
	'''
	Plan to describe the NCBI sra sample 
	'''
	pass

class LocalSample(BaseModel):
	_ = '''
	'''
	SAMPLE_ID:                str	
	RUN_ID_LIST: List[str] = None
	SAMPLE_ATTRIBUTES: Dict[str,str] =None

	@property
	def WORDS(self) -> str:
		words = self.SAMPLE_ATTRIBUTES.values() + [self.SAMPLE_ID]
		return ' '.join(words)
	@property
	def tag_source_name(self) -> str:
		return self.SAMPLE_ATTRIBUTES.get('source_name','NA')
	@property
	def tag_tissue(self) -> str:
		return self.SAMPLE_ATTRIBUTES.get('tissue','NA')
	@property
	def tag_age(self) -> str:
		return self.SAMPLE_ATTRIBUTES.get('age','NA')

	@property
	def tags(self) -> str:
		return ' '.join(['[{0}:{1}]'.format(k,v) for k,v in self.SAMPLE_ATTRIBUTES.items()])
	@property
	def RUN_ID_LIST_CONCAT(self) -> str:
		return ' '.join(self.RUN_ID_LIST)

	@classmethod
	def parse_tags(cls, buf, strict=0) -> Dict[str,str]:
		'''
		Dirty parsing
		'''
		dct = OrderedDict()
		import re
		lst = re.split('\[([a-zA-Z\-_ ]*):', buf)
		k = None
		for i, ele in enumerate(lst[1:]):
			if (i % 2)   == 0:
				k = ele
			elif (i % 2) == 1:
				ele = ele.strip()
				assert ele.endswith(']'),ele
				v = ele[:-1]
				dct[k] = v
				k = None
		assert k is None,(buf)
		return dct


		sp = buf.strip().split('[')
		dct = {}
		for ele in sp:
			if not ele:
				continue
			ele = ele.strip()
			if not ele.endswith(']'):
				msg = 'parse_tags() failed:%s'%buf
				if strict:
					raise Exception(msg)
				else:
					warnings.warn(msg)
				continue					
			k,v = ele[:-1].strip().split(':',1)
			dct[k] = v
		return dct

	def to_simple_dict(self):
		return OrderedDict([
			('SAMPLE_ID',           self.SAMPLE_ID),
			('RUN_ID_LIST_CONCAT',  self.RUN_ID_LIST_CONCAT),
			('tag_tissue',          self.tag_tissue),
			('tag_source_name',     self.tag_source_name),
			('tag_age',             self.tag_age),
			('tags',                self.tags),
		])

	@classmethod
	def from_simple_dict(cls, data):
		out_data = data.copy()
		out_data['SAMPLE_ATTRIBUTES'] = cls.parse_tags(data['tags'])
		out_data['RUN_ID_LIST'] = data['RUN_ID_LIST_CONCAT'].split()
		if data.get('tag_tissue','NA') not in ['NA','']:
			out_data['SAMPLE_ATTRIBUTES']['tissue'] = data['tag_tissue']
		if data.get('tag_source_name','NA') not in ['NA','']:
			out_data['SAMPLE_ATTRIBUTES']['source_name'] = data['tag_source_name']
		if data.get('tag_sge','NA') not in ['NA','']:
			out_data['SAMPLE_ATTRIBUTES']['age'] = data['tag_age']
		return cls.parse_obj(out_data)

	@classmethod
	def normalise_words(cls,words):
		lst = []
		for x in words:
			lst.append(cls.normalise_word(x))
		return lst

	@classmethod
	def normalise_word(cls, x):
		x = x.strip(',')
		if x in ['seedlings','seedling']:
			x = 'seedling'
		if x in ['rosettes','rosette']:
			x = 'rosette'
		if x in ['leaves', 'leaf', 'leafs']:
			x = 'leaf'		
		return x

	@classmethod
	def from_ncbi_efetch(cls, expt_package):
		data = expt_package
		data0 = data

		data = tree_from_dict(data)
		out_data = {}
		# if 'SAMPLE_ATTRIBUTES' not in data['SAMPLE']:
		# 	assert 0
		# data = tree(data)
		assert len(data['SAMPLE']) == 1
		out_data['SAMPLE_ID']                = data['SAMPLE'][0]['IDENTIFIERS'][0]['PRIMARY_ID'][0]
		out_data['RUN_ID_LIST']       = [x['IDENTIFIERS'][0]['PRIMARY_ID'][0] for x in data['RUN_SET'][0]['RUN']]
		out_data['SAMPLE_ATTRIBUTES'] = {
			cls.normalise_word(x['TAG'][0]): cls.normalise_word(x['VALUE'][0])
			for x in data['SAMPLE'][0]['SAMPLE_ATTRIBUTES'][0]['SAMPLE_ATTRIBUTE']
			}
		return cls.parse_obj(out_data)

	def dump_dir(self, fn):
		dict_dump_dir(self.dict(), fn)

	@classmethod
	def from_dir(cls,fn):
		d = dict_load_dir(fn)
		d = cls.parse_obj(d)
		return d




