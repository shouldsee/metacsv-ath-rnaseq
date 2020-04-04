set -eux

branch=$(python - $@<<EOF
import sys
from pprint import pprint
args = sys.argv
import re
if '--file' in args:
	i = sys.argv.index('--file')
	branch = open(args[i+1],'r').read().splitlines()[0]
	branch = re.sub('[^0-9a-zA-Z\-_]','-',branch)
	print(branch)
EOF
)
branch=${branch:-bash-autopr-$(date -u +%y-%m-%d-%H-%M-%S-%N)}
export GITHUB_TOKEN=${1:-$GITHUB_TOKEN}

echo $GITHUB_TOKEN >/dev/null
git config credential.helper 'store --file .cred'
echo https://${GITHUB_TOKEN}:x-oauth-basic@github.com >.cred

DIR=$PWD
git config user.email metacsv-bot@protonmail.com
git config user.name metacsv-bot
git checkout -b "$branch"
git commit ./root.hand_patch.csv ./current.csv -m "$branch"
$DIR/bin/hub pull-request --base shouldsee:master -p $@
git checkout master
rm -f .cred
