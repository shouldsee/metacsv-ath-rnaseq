set -euxo pipefail
pandoc --from gfm --to html README.md >index.html
