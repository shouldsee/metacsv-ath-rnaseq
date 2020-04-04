from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from pydantic import BaseModel
import pandas as pd

import subprocess
app = FastAPI()
app.mount("/static", StaticFiles(directory="."), name="static")

from typing import Any,List
import tzlocal
import datetime
def date_format_iso(obj=None):
    if obj is None:
        obj = datetime.datetime.utcnow()
    local_tz = tzlocal.get_localzone() 
    s  = obj.replace(tzinfo=local_tz).isoformat()
    return s


class csvData(BaseModel):
	data:List[Any]
	type:str
	columns:List[str]
	email: str
	pr_tag: str
	gh_token: str = None
	github_sha: str



@app.post("/auto_pr")
# async 
def auto_pull_request( dat:csvData):
	import os
	from pprint import pprint
	from collections import OrderedDict
	import requests,io
	GH_TOKEN = os.environ.get('GH_TOKEN')
	# sha1 = subprocess.check_output('git rev-parse --verify HEAD',shell=True).strip()
	# if sha1
	# print(newDf).head()
	edit_csv = 'root.hand_patch.csv'
	subprocess.check_output('git pull origin master',shell=True)
	subprocess.check_output(f'git checkout -f {dat.github_sha}',shell=True)
	# oldCsv = io.BytesIO(requests.get(f'https://raw.githubusercontent.com/shouldsee/metacsv-ath-rnaseq/{dat.github_sha}/current.csv').content)
	oldCsv = 'current.csv'
	oldDf = pd.read_csv( oldCsv,index_col=[0],header=0)
	newDf = pd.DataFrame( dat.data, None, dat.columns).set_index('SAMPLE_ID')
	def df_stand(df):
		return df.reset_index().replace({'' :pd.np.nan,None:pd.np.nan}, regex=False).dropna(subset=['SAMPLE_ID'])
	oldDf = df_stand(oldDf);
	newDf = df_stand(newDf);
	# oldDf = oldDf.reset_index().replace({'' :pd.np.nan,None:pd.np.nan}, regex=False).dropna(subset=['SAMPLE_ID'])
	# newDf = newDf.reset_index().replace({'' :pd.np.nan,None:pd.np.nan}, regex=False).dropna(subset=['SAMPLE_ID'])
	assert all(newDf.columns == oldDf.columns), (newDf.head(),colDf.head())

	dfDiff   = pd.concat([oldDf,newDf]).drop_duplicates(keep=False).sort_values('SAMPLE_ID')
	countDict= dfDiff[['SAMPLE_ID']].groupby('SAMPLE_ID').apply(len).to_dict()
	labels = OrderedDict()
	if 1:
	# import pdb, traceback, sys	
	# try:
		for SAMPLE_ID, count in countDict.items():
			if count == 2:
				labels[SAMPLE_ID] = 'edited'
			elif count == 1:
				if SAMPLE_ID in oldDf['SAMPLE_ID'].values:
					labels[SAMPLE_ID] = 'deleted'
				elif SAMPLE_ID in newDf['SAMPLE_ID'].values:
					labels[SAMPLE_ID] = 'added'
				else:
					assert 0,(SAMPLE_ID,count)
			else:
				assert 0,(SAMPLE_ID,count)

	# except:
	# 	extype, value, tb = sys.exc_info()
	# 	traceback.print_exc()
	# 	pdb.post_mortem(tb)
	newDf_indexed = newDf.set_index('SAMPLE_ID')
	editDf = pd.read_csv( edit_csv, index_col=[0],header=0)
	editDf = df_stand(editDf).set_index('SAMPLE_ID')
	for SAMPLE_ID,label in labels.items():
		if label   in ['edited','added']:
			editDf.loc[SAMPLE_ID,:] = newDf_indexed.loc[SAMPLE_ID]
		elif label == 'deleted':
			_ = '''
			Fragile. needs a pointer that delete a record using hand_patch
			'''
			if 'SAMPLE_ID' in editDf.index.values:
				del editDf.loc[SAMPLE_ID]
		else:
			assert 0,(label,)	
	if not len(labels):
		print('[no_record_changed]')
		##### No records changed. return respose 
		return Response('[nothing_changed]')
	else:
		editDf.fillna("NA").to_csv(edit_csv, index=1)

		from spiper.runner import force_run
		from path import Path
		from main import patch_by_hand
		curr = force_run(patch_by_hand, '_temp', 'current.csv', edit_csv)
		curr.output.link(Path('current.csv').unlink_p())

		isotime  = date_format_iso()
		pr_title ='{dat.pr_tag}_{dat.email}_{isotime}'
		pr_title = pr_title.format(**locals())
		prm_file = '_pr.message'

		meta = pd.DataFrame([],None,columns=['value'])
		# .set_index()
		with open(prm_file,'w') as f:
			f.write('%s\n\n'%pr_title)
			f.write('### Changed Rows \n')
			pd.Series(labels).to_frame('STATUS').to_html(f)
			f.write('\n\n')
			f.write('### Pull Request Meta \n')
			# f.write('--------------------------\n')
			meta.loc['isotime'] = isotime
			meta.to_html(f)
			f.write('\n\n')
			f.write('### New rows details \n')
			pd.Series(labels).to_frame('STATUS').merge(left_index=True,right_index=True,how='left',right=newDf_indexed).to_html(f)
			f.write('\n\n')

	subprocess.check_output(' '.join(['HUB_VERBOSE=1','bash','autopr.sh',GH_TOKEN,
		'--file',prm_file,
		'2>ERROR','1>STDOUT']),shell=True)
	print('[auto_pr]Done')
	return Response('[auto_pr]%s'%pr_title)
