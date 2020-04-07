from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response, JSONResponse, StreamingResponse
from pydantic import BaseModel
import pandas as pd
from path import Path
DIR = Path('.').realpath()
from collections import OrderedDict
import subprocess
app = FastAPI()
router = APIRouter()

PREFIX = "/metacsv-ath-rnaseq"
# app.mount(PREFIX)
app.mount(PREFIX+"/static", StaticFiles(directory="."), name="static");
# router.mount("/static", StaticFiles(directory="."),);
# app.mount("/static", StaticFiles(directory="."), name="static")
@router.get("/edit")
def edit():
	with open(DIR/'edit.html','r') as f:
		return HTMLResponse(f.read())

from typing import Any,List
import tzlocal
import datetime
import joblib
(DIR /'_server').makedirs_p()
memory = joblib.Memory(DIR / '_server/cache/',bytes_limit = 1024 * 1024 * 1024 )
def date_format_iso(obj=None):
    if obj is None:
        obj = datetime.datetime.utcnow()
    local_tz = tzlocal.get_localzone() 
    s  = obj.replace(tzinfo=local_tz).isoformat()
    return s


from jinja2 import Template, StrictUndefined
def jinja2_format(s,**context):
	# d = context.copy()
	d = {}
	# d = __builtins__.copy()
	d.update(context)
	# .update(__builtins__)
	return Template(s,undefined=StrictUndefined).render(**d)

import requests
import re,json
def resolve_sha(sha):
	if re.match('[0-9a-fA-F]{40}',sha) is not None:
		return sha
	else:
		url="https://api.github.com/repos/shouldsee/metacsv-ath-rnaseq/git/refs"
		x = json.loads(requests.get(url).text)
		x = [y["object"]["sha"] for y in x if y["ref"]=="refs/heads/{sha}".format(sha=sha)][0]
		return x

@memory.cache
def _get_json(sha):
	from metacsv_ath_rnaseq.header import dict_load_dir
	import subprocess
	import requests
	import tempfile
	import urllib.request
	with Path(tempfile.mkdtemp(sha)).realpath() as tdir:
		debug = 0
		if debug:
			obj = dict_load_dir('/tmp/shouldsee-metacsv-ath-rnaseq-c7d8315/DATABASE')
			return obj

		url = 'http://github.com/shouldsee/metacsv-ath-rnaseq/tarball/{sha}'.format(**locals())
		# _shell([f'curl -sL {url} | tar -xzf - -C $PWD'])

		urllib.request.urlretrieve(url,'_TEMP.tar.gz')
#		subprocess.check_output('pigz -dc _TEMP.tar.gz | tar -xf - -C .', shell=True)
		subprocess.check_output('cat _TEMP.tar.gz |tar -xzf - -C .', shell=True)
#		subprocess.check_output('pigz -dc _TEMP.tar.gz | tar -xf - -C .', shell=True)

		obj = dict_load_dir(tdir.glob('shouldsee-metacsv-*/DATABASE')[0])
	tdir.rmtree()
	return obj


@router.get("/json/{sha}")
def get_json(sha):
	sha = resolve_sha(sha)

	import time
	t0 = time.time()

	import tempfile
	from path import Path
	obj = _get_json(sha, )
	print('[runtime]%.3fs'%(time.time()-t0))
	return obj


@router.get("/simple_json/{sha}")
def get_simple_json(sha):
	sha = resolve_sha(sha)

	import tempfile
	from path import Path
	from metacsv_ath_rnaseq.models import LocalSample
	from collections import OrderedDict
	obj = _get_json(sha)
	obj = OrderedDict([(k, LocalSample.parse_obj(x).to_simple_dict()) for k,x in obj.items()])
	return obj

def rec_to_df(obj):
	from metacsv_ath_rnaseq.models import LocalSample
	obj = [LocalSample.parse_obj(x) for x in obj.values()]
	df = pd.concat([pd.Series(x.to_simple_dict()) for x in obj],axis=1).T
	return df

@router.get("/csv/{sha}")
def get_csv(sha):
	sha = resolve_sha(sha)

	import io
	import tempfile
	from path import Path
	from metacsv_ath_rnaseq.models import LocalSample
	import pandas as pd
	obj = _get_json(sha)

	csvBuffer = io.StringIO()
	df = rec_to_df(obj)
	df.to_csv(csvBuffer,index=0)
	csvBuffer.seek(0);
	return Response(csvBuffer.read())

class csvData(BaseModel):
	data:List[Any]
	type:str
	columns:List[str]
	email: str
	pr_tag: str
	gh_token: str = None
	github_sha: str


@router.post("/auto_pr")
def auto_pull_request( dat:csvData):
	import os
	from pprint import pprint
	from collections import OrderedDict
	import requests,io
	from metacsv_ath_rnaseq.header import dict_load_dir, dict_dump_dir
	import re
	GH_TOKEN = dat.gh_token or os.environ.get('GH_TOKEN', None)
	_DIR =  DIR
	isotime  = date_format_iso()
	pr_title ='{dat.pr_tag}_{dat.email}_{isotime}'
	pr_title = pr_title.format(**locals())
	branch = re.sub('[^0-9a-zA-Z\-_]','-',pr_title)
	base_branch='bysha1_{dat.github_sha}'.format(**locals())

	if 0:
		oldDf = pd.read_csv( io.BytesIO(get_csv(dat.github_sha).body), index_col=[0],header=0)

	with Path('_pr_temp.{dat.github_sha}'.format(**locals())).rmtree_p().makedirs_p() as tdir:
		CMD = [
			'set -euxo pipefail;',
			'git init .',
			'&& git remote add origin https://github.com/shouldsee/metacsv-ath-rnaseq',
			'&& git fetch origin {dat.github_sha}'.format(**locals()),
			'&& git reset --hard FETCH_HEAD 2>ERROR',
		]	
		_shell(CMD)
		oldDf = rec_to_df( dict_load_dir('DATABASE')).set_index('SAMPLE_ID')
		newDf = pd.DataFrame( dat.data, None, dat.columns).set_index('SAMPLE_ID')		
		# newRecs = df_to_rec(df_stand(newDf))
		oldDf  = df_stand(oldDf.reset_index());
		newDf  = df_stand(newDf.reset_index());
		newRecs= df_to_rec(newDf)
		labels = df_compare(oldDf,newDf)

		if not len(labels):
			print('[no_record_changed]')
			##### No records changed. return respose 
			return Response('[nothing_changed]')

		CMD = [
		jinja2_format('''
		GH_TOKEN={{GH_TOKEN}}
		base_branch={{base_branch}}
		echo https://${GH_TOKEN}:x-oauth-basic@github.com >.cred;
		git config credential.helper 'store --file .cred'
		git config user.email metacsv-bot@protonmail.com
		git config user.name metacsv-bot

		set -euxo pipefail;
		git checkout -B ${base_branch} && git push origin ${base_branch} 2>ERROR
		''',**locals())
		]
		_shell(CMD)

		with Path('DATABASE'):
			for SAMPLE_ID,label in labels.items():
				if label in ['edited','added']:
					dict_dump_dir( newRecs[SAMPLE_ID], SAMPLE_ID)
				elif label == 'deleted':
					Path('SAMPLE_ID').rmtree()
				else:
					assert 0,(label,)			

		pr_msg_file = '_pr.message'
		meta = pd.DataFrame([],None,columns=['value'])

		with open(pr_msg_file,'w') as f:
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
			pd.Series(labels).to_frame('STATUS').merge(left_index=True,right_index=True,how='left',right=newDf.set_index('SAMPLE_ID')).to_html(f)
			f.write('\n\n')


		CMD = '''
		{
			GH_TOKEN={{GH_TOKEN}}
			branch={{branch}}
			DIR={{_DIR}}
			# base_branch={{base_branch}}
			base_branch=data
			pr_msg_file={{pr_msg_file}}
			HUB_VERBOSE=1

			set -euxo pipefail;
			export GITHUB_TOKEN=${GH_TOKEN}
			git checkout -B "${branch}"
			git add DATABASE
			git commit -m "${branch}"
			${DIR}/bin/hub pull-request --base shouldsee:${base_branch} -p --file ${pr_msg_file}
		} 2>ERROR

		rm -f .cred
		'''
		CMD = [jinja2_format(CMD,**locals())]
		_shell(CMD)

	tdir.rmtree()
	print('[auto_pr]Done')
	return Response('[auto_pr]%s'%pr_title)

def _shell(CMD,**kw):
	return subprocess.check_output(' '.join(CMD),shell=True,executable='bash',**kw)

def df_to_rec(df):
	from metacsv_ath_rnaseq.models import LocalSample
	from collections import OrderedDict
	out = OrderedDict()
	# df = df_stand(df)
	for x in df.to_dict(orient='records'):
		y =  LocalSample.from_simple_dict(x)
		out[x['SAMPLE_ID']] = y.dict()		
	return out

def df_stand(df):
	return df.replace({'' :pd.np.nan,None:pd.np.nan}, regex=False).dropna(subset=['SAMPLE_ID']).fillna('NA')
def df_compare(oldDf,newDf):
	from collections import OrderedDict
	# oldDf = oldDf.reset_index().replace({'' :pd.np.nan,None:pd.np.nan}, regex=False).dropna(subset=['SAMPLE_ID'])
	# newDf = newDf.reset_index().replace({'' :pd.np.nan,None:pd.np.nan}, regex=False).dropna(subset=['SAMPLE_ID'])
	assert all(newDf.columns == oldDf.columns), (newDf.head(),colDf.head())
	dfDiff   = pd.concat([oldDf,newDf]).drop_duplicates(keep=False).sort_values('SAMPLE_ID')
	countDict= dfDiff[['SAMPLE_ID']].groupby('SAMPLE_ID').apply(len).to_dict()
	labels = OrderedDict()
	if 1:
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
	return labels

@router.post("/auto_pr2")
def auto_pull_request2( dat:csvData):
	import os
	from pprint import pprint
	from collections import OrderedDict
	import requests,io


	GH_TOKEN = os.environ.get('GH_TOKEN')
	edit_csv = 'root.hand_patch.csv'
	subprocess.check_output('git pull origin master',shell=True)
	subprocess.check_output(f'git checkout -f {dat.github_sha}',shell=True)
	# oldCsv = io.BytesIO(requests.get(f'https://raw.githubusercontent.com/shouldsee/metacsv-ath-rnaseq/{dat.github_sha}/current.csv').content)
	oldCsv = 'current.csv'
	oldDf = pd.read_csv( oldCsv,index_col=[0],header=0)
	newDf = pd.DataFrame( dat.data, None, dat.columns).set_index('SAMPLE_ID')


	oldDf = df_stand(oldDf.reset_index());
	newDf = df_stand(newDf.reset_index());
	labels = df_compare(oldDf,newDf)

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
		import sys
		editDf.fillna("NA").to_csv(edit_csv, index=1)
		subprocess.check_output(f'{sys.executable} main.py patch_by_hand 2>ERROR',shell=True)

		isotime  = date_format_iso()
		pr_title ='{dat.pr_tag}_{dat.email}_{isotime}'
		pr_title = pr_title.format(**locals())
		pr_msg_file = '_pr.message'
		branch = re.sub('[^0-9a-zA-Z\-_]','-',pr_title)

		meta = pd.DataFrame([],None,columns=['value'])
		# .set_index()
		with open(pr_msg_file,'w') as f:
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
			pd.Series(labels).to_frame('STATUS').merge(left_index=True,right_index=True,how='left',right=newDf.set_index('SAMPLE_ID')).to_html(f)
			f.write('\n\n')


	subprocess.check_output(' '.join(['HUB_VERBOSE=1','bash','autopr.sh',GH_TOKEN,
		'--file',pr_msg_file,
		'2>ERROR','1>STDOUT']),shell=True)
	print('[auto_pr]Done')
	return Response('[auto_pr]%s'%pr_title)

app.include_router(router,prefix=PREFIX)
