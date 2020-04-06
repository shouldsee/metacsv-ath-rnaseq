
'''
current.csv is bootstrapped from NCBI annotation
'''
import pandas as pd
# import pandas as import pdb; pdb.set_trace()

df = pd.read_csv("current.csv",index_col=None,header=0)
print(df.head().to_dict(orient='records')[0:1])

from metacsv_ath_rnaseq.models import LocalSample
from metacsv_ath_rnaseq.header import dict_dump_dir, dict_load_dir, Path
def df_stand(df):
	return df.reset_index().replace({'' :pd.np.nan,None:pd.np.nan}, regex=False).dropna(subset=['SAMPLE_ID'])
df  = df_stand(df.set_index('SAMPLE_ID')).fillna('NA')
lst = df.to_dict(orient='records')

from collections import OrderedDict
with Path('.').makedirs_p():
	out = OrderedDict()
	for x in lst[:]:
		y =  LocalSample.from_simple_dict(x)
		d = y.SAMPLE_ATTRIBUTES
		if 'genotype/variation' in d:
			d['genotype_variation'] = d.pop('genotype/variation')
		# x = y.dump_dir(x['SAMPLE_ID'])
		out[x['SAMPLE_ID']] = y.dict()
#		out[x['SAMPLE_ID']] = {}
	dict_dump_dir(out,'DATABASE')

print('[done]')


# from pprint import pprint
# x.dump_dir('_temp_file')
# y = LocalSample.from_dir('_temp_file')
# assert x==y,(x,y)
# print('[done]')
# import pdb; pdb.set_trace()
