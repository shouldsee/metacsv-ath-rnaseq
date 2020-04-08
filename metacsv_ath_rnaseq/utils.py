import time
from metacsv_ath_rnaseq.header import dict_load_dir
import subprocess
import requests
import tempfile
# import urllib.request
import requests
from path import Path

def dict_from_db_branch(user,repo,sha):
	'''
	download 
	'''
	t0 = time.time()
	with Path(tempfile.mkdtemp(sha)).realpath() as tdir:
		debug = 0
		if debug:
			obj = dict_load_dir('/tmp/shouldsee-metacsv-ath-rnaseq-c7d8315/DATABASE')
			return obj

		url = 'http://github.com/{user}/{repo}/tarball/{sha}'.format(**locals())
		with open('_TEMP.tar.gz','wb') as f: f.write(requests.get(url).content)
		# assert 0
		# urllib.request.urlretrieve(url,'_TEMP.tar.gz')
#		subprocess.check_output('pigz -dc _TEMP.tar.gz | tar -xf - -C .', shell=True)
		subprocess.check_output('cat _TEMP.tar.gz |tar -xzf - -C .', shell=True)
#		subprocess.check_output('pigz -dc _TEMP.tar.gz | tar -xf - -C .', shell=True)
		obj = dict_load_dir(tdir.glob('{user}-{repo}-*/DATABASE'.format(**locals()))[0])
	tdir.rmtree()
	print('[runtime]%.3fs'%(time.time()-t0))
	return obj



import requests
import re,json
def resolve_repo_sha(user,repo,sha):
	if re.match('[0-9a-fA-F]{30}',sha) is not None:
		return sha
	else:
		# url="https://api.github.com/repos/shouldsee/metacsv-ath-rnaseq/git/refs"
		# x = json.loads(requests.get(url).text)
		# x = [y["object"]["sha"] for y in x if y["ref"]=="refs/heads/{sha}".format(sha=sha)][0]

		url="https://api.github.com/repos/{user}/{repo}/git/refs/heads/{sha}".format(user=user,repo=repo,sha=sha)
		x = json.loads(requests.get(url).text)
		x = x["object"]["sha"]
		return x
