from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response, JSONResponse, StreamingResponse, RedirectResponse
from pydantic import BaseModel
import pandas as pd
from path import Path
from collections import OrderedDict
import subprocess
from metacsv_ath_rnaseq.models import LocalSample

'''
git fetch origin refs/heads/master:refs/remotes/origin/master
'''
def read_close(fn,encoding=None):
	with open(fn,"rb") as f:
		return f.read().decode(encoding) if encoding else f.read().decode()

DIR = Path('.').realpath()
DEFAULT_BRANCH="data"

PREFIX = "/metacsv-ath-rnaseq"
app = FastAPI(
	openapi_url=PREFIX+"/openapi.json",
	docs_url=PREFIX+"/docs",
	)
@app.get(PREFIX) 
def homepage(): return RedirectResponse(PREFIX+'/docs')	

router = APIRouter(
	)
app.mount(PREFIX+"/static", StaticFiles(directory="."), name="static");
from fastapi.openapi.utils import get_openapi
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
    	title = "metacsv-ath-rnaseq",
        # title="Custom title",
        version=read_close("VERSION").strip(),
        description='''

<img width="16" height="16" src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png"></img>[Github](https://github.com/shouldsee/metacsv-ath-rnaseq)

This project aims to provide a better API for retriving meta-data for public Ath-RNASEQ datasets, thus enabling better 
understanding of the plant transcriptome.

## Download Data

Choose one of:

1. Using hosted api endpoint at `/csv/`,`/simple_json/`,`/db_json/`
1. Use `metacsv_ath_rnaseq.utils.dict_from_db_branch(user, repo, sha)`
1. Or clone the github branch `shouldsee/metacsv-ath-rnaseq:data` and 
load using `metacsv_ath_rnaseq.header.dict_from_dir("./DATABASE")`

## Edit Data

The github branch `shouldsee/metacsv-ath-rnaseq/data` is the current merging head getting updated. 
It has a directory "/DATABASE/" which is a file-based database that may be updated through one of:

1. Manually edit using the `/edit` endpoint
1. POST request the `/auto_pr` endpoint (not documented)
1. Manually create a PR to "shouldsee/metacsv-ath-rnaseq:data" after editing the "./DATABASE" directory in your branch.


## Install python package:

- Require Python >= 3.6 (check `pip -V` )
- `pip install metacsv-ath-rnaseq@https://github.com/shouldsee/metacsv-ath-rnaseq/tarball/master`

 ''',
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema
app.openapi = custom_openapi

# @app.get(PREFIX)
# def _():
# 	return RedirectResponse(PREFIX+'/docs')
	# return RedirectResponse(app.url_path_for(PREFIX+'/docs'))
	# from pprint import pprint
	# pprint(router.routes)
	# import pdb; pdb.set_trace()
	# return RedirectResponse()
	# return RedirectResponse(app.url_path_for("/docs"))
@router.get("/edit",
	# summary=
# response_model = HTMLResponse,
summary='An online csv-based editor using handsontable',
	
description=f'''
An online csv-based editor using handsontable <a href="{PREFIX}/edit">{PREFIX}/edit</a>
--------------------------------------------------

This editor allows user to filter for keywords, make modifications and create autopr.
'''
	)
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


from metacsv_ath_rnaseq.utils import resolve_repo_sha
def resolve_sha(sha):
	return resolve_repo_sha('shouldsee', 'metacsv-ath-rnaseq', sha)

from metacsv_ath_rnaseq.utils import dict_from_db_branch, UniqueGlobError
@memory.cache
def _get_json(sha):
	try:
		return dict_from_db_branch("shouldsee","metacsv-ath-rnaseq", sha, )
	except UniqueGlobError as e:
		raise HTTPException(status_code=500,detail=f'Cannot find /DATABASE/ from commit identified by {sha}')


@router.get("/db_json/{commit_sha_or_branch}",
    summary="Return a db-json-formatted database for github commit-sha1/branch-name {sha}",
    description='''
## Return a json-formatted database for a commit-sha1/branch-name

- `db_json` is the direct dump of the database according to its schema.
- `sha`: a github commit-sha1/branch-name that has a `/DATABASE/` directory
  - example: "branch"
    ''',
	)
def get_db_json(commit_sha_or_branch):
	sha = resolve_sha(commit_sha_or_branch)
	import tempfile
	from path import Path
	obj = _get_json(sha,)
	# 'shouldsee', 'metacsv_ath_rnaseq')
	return obj

@router.get("/db_json/{commit_sha_or_branch}/{SAMPLE_ID}",
    summary="Return a db-json-formatted record {sha}",
    description='''
## Return a db-json-formatted database for a commit-sha1/branch-name

- `db_json` is the direct dump of the database according to its schema.
- `sha`: a github commit-sha1/branch-name that has a `/DATABASE/` directory
  - example: "branch"
    ''',
    response_model = LocalSample,
	)
def get_db_json_record(commit_sha_or_branch,SAMPLE_ID):
	sha = resolve_sha(commit_sha_or_branch)
	import tempfile
	from path import Path
	obj = _get_json(sha, )[SAMPLE_ID]
	return obj




@router.get("/simple_json/{commit_sha_or_branch}",
    # response_model=Item,
    summary="Return a simple_json-formatted database for github commit-sha1/branch-name",
    description='''
## Return a simple_json-formatted database for a commit-sha1/branch-name

- `simple_json` is a view for `LocalSample` suitable for edit and not storage.
- `sha`: a github commit-sha1/branch-name that has a `/DATABASE/` directory
  - example: "branch"

    ''',
    # description="Create an item with all the information, name, description, price, tax and a set of unique tags",

	)
def get_simple_json(commit_sha_or_branch):
	sha = resolve_sha(commit_sha_or_branch)

	import tempfile
	from path import Path
	from metacsv_ath_rnaseq.models import LocalSample
	from collections import OrderedDict
	obj = _get_json(sha,)
	 # 'shouldsee','metacsv-ath-rnaseq')
	obj = OrderedDict([(k, LocalSample.parse_obj(x).to_simple_dict()) for k,x in obj.items()])
	return obj



@router.get("/simple_json/{commit_sha_or_branch}/{SAMPLE_ID}",
    # response_model=Item,
    summary="Return a simple_json-formatted database for github commit-sha1/branch-name {sha}",
    description='''
## Return a simple_json-formatted database for a commit-sha1/branch-name

- `simple_json` is a view for `LocalSample` suitable for edit and not storage.
- `sha`: a github commit-sha1/branch-name that has a `/DATABASE/` directory
  - example: "branch"

    ''',
    # description="Create an item with all the information, name, description, price, tax and a set of unique tags",

	)
def get_simple_json_record(commit_sha_or_branch,SAMPLE_ID):
	sha = resolve_sha(commit_sha_or_branch)

	import tempfile
	from path import Path
	from metacsv_ath_rnaseq.models import LocalSample
	from collections import OrderedDict
	# obj = _get_json(sha)
	# return  LocalSample.parse_obj(obj[SAMPLE_ID]).to_simple_dict
	# return {'type':type(obj)}
	obj = get_db_json_record(sha,SAMPLE_ID)
	# return obj
	return  LocalSample.parse_obj(obj).to_simple_dict()
	# return {'type':type(obj).__name__}
	# obj = LocalSample.parse_obj(obj).to_simple_dict()
	# return obj


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
	obj = _get_json(sha,)
	 # USER, REPO)

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
	try_push: int = 0


@router.post("/auto_pr",
	description='''
Private API for `/edit`
------------------------
	'''

	)
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
	new_branch = re.sub('[^0-9a-zA-Z\-_\@\.]','-',pr_title)
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
		git config user.name  metacsv-bot

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
			set -eux;
		# {
			GH_TOKEN={{GH_TOKEN}}
			new_branch={{new_branch}}
			DIR={{_DIR}}
			target_branch=data
			pr_msg_file={{pr_msg_file}}
			try_push={{dat.try_push}}
			HUB_VERBOSE=1

			# set -o pipefail;
			export GITHUB_TOKEN=${GH_TOKEN}
			git checkout -B "${new_branch}"
			git add DATABASE
			git commit -m "${new_branch}" 

			rm -f RET; touch RET;
			if [[ ${try_push} -eq 1 ]]
			then
			    { 
			    	git push origin ${new_branch}:${target_branch} && echo PUSH_SUC >>RET; 
			    } || { 
			    	echo PUSH_FAIL>> RET
			    	${DIR}/bin/hub pull-request --base shouldsee:${target_branch} -p --file ${pr_msg_file} && echo PR_SUC>>RET; 
			    }
			else
			    ${DIR}/bin/hub pull-request --base shouldsee:${target_branch} -p --file ${pr_msg_file} && echo PR_SUC>>RET; 
			fi
		# } 2>ERROR
		rm -f .cred
		'''
		CMD = [jinja2_format(CMD,**locals())]
		res = _shell(CMD).decode().rstrip().splitlines()[-1]
		# pprint(CMD[0].splitlines())
		with open('RET','r') as f:
			ret = f.read().splitlines()
	tdir.rmtree()
	print('[auto_pr]Done')
	if "PUSH_SUC" in ret or "PR_SUC" in ret:
		return Response("%r:%s"%(ret,pr_title))
	else:
		return Response("[errored]%r:%s"%(ret,pr_title))
	# if 'PUSH_SUC' in ret:
	# 	return Response('[pushed]%s'%pr_title)
	# elif 'PUSH_FAIL' in ret:
	# 	return Response('%r%s'%(ret,pr_title))
	# if res =='PR':
	# 	return Response('[auto_pr]%s'%pr_title)
	# elif res=='PUSHED':
	# 	return Response('[pushed]%s'%pr_title)
	# else:
	# 	raise HTTPException(500,{'res':res})
	# 	# %s'%pr_title)


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

app.include_router(router,prefix=PREFIX)
