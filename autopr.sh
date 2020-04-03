set -eux
export GITHUB_TOKEN=${1:-$GITHUB_TOKEN}
echo $GITHUB_TOKEN >/dev/null
git config credential.helper 'store --file .cred'
echo https://${GITHUB_TOKEN}:x-oauth-basic@github.com >.cred


DIR=$PWD
git config user.email metacsv-bot@protonmail.com
git config user.name metacsv-bot
branch=autopr-$(date -u +%y-%m-%d-%H-%M-%S-%N)
git checkout -b $branch
git commit ./root.hand_patch.csv -m $branch
$DIR/bin/hub pull-request --base shouldsee:master -m $branch -p
git checkout master
rm -f .cred