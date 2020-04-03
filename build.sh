set -euxo pipefail
DIR=$PWD

mkdir -p _build/
cd _build
curl -LC- -o pandoc.css https://gist.github.com/killercup/5917178/raw/40840de5352083adb2693dc742e9f75dbb18650f/pandoc.css
# pandoc --standalone --css https://gist.githubusercontent.com/killercup/5917178/raw/40840de5352083adb2693dc742e9f75dbb18650f/pandoc.css --from gfm --to html README.md >index.html
pandoc --standalone --css pandoc.css --from gfm --to html $DIR/README.md >$DIR/index.html

head $DIR/index.html
cd $DIR
echo [build_succ]
