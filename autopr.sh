set -eux
GITHUB_TOKEN=${1:-$GITHUB_TOKEN}
echo $GITHUB_TOKEN >/dev/null

DIR=$PWD
git config user.email metacsv-bot@protonmail.com
git config user.name metacsv-bot
branch=autopr-$(date -u +%s%N)
git checkout -b $branch
git commit metacsv_ath_rnaseq/root.hand_patch.csv -m $branch
$DIR/bin/hub pull-request --base shouldsee:master -m $branch -p
git checkout master

