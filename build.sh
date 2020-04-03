set -euxo pipefail
DIR=$PWD

mkdir -p _build/
cd _build
## ref: https://devilgate.org/blog/2012/07/02/tip-using-pandoc-to-create-truly-standalone-html-files/#fnref1
## pandoc -s -S --toc -H pandoc.css -A footer.html README -o example3.html
curl -LC- -o pandoc.css.temp https://gist.github.com/killercup/5917178/raw/40840de5352083adb2693dc742e9f75dbb18650f/pandoc.css
{
	echo '<style type="text/css">' 
	cat pandoc.css.temp 
	echo '</style>'
} > pandoc.css

pandoc --standalone --include-in-header pandoc.css --from gfm --to html $DIR/README.md >$DIR/index.html
head $DIR/index.html

cd $DIR
echo [build_succ]
