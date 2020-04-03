
from eutils._internal.client import Client, ESearchResult
import io,os
import warnings
import pandas as pd


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

