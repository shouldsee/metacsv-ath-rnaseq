

import urllib.request
import os 
from path import Path
def fetch_remote(url, dir, basename):
	if basename is None:
		basename = os.path.basename(url)
	if dir is None:
		dir = '.'
	dir =Path(dir).realpath().makedirs_p()

	urllib.request.urlretrieve(url, os.path.join(dir,basename))
	return os.path.join(dir,basename)
	# return (url, dir, basename)

[
fetch_remote("https://code.jquery.com/jquery-3.3.1.slim.min.js", 'js', None),
fetch_remote("https://cdn.jsdelivr.net/npm/handsontable@latest/dist/handsontable.full.js", 'js', None),
fetch_remote("https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css", 'css', None),
# fetch_remote("https://handsontable.com/static/css/main.css", 'css', 'handsontable-main.css'),
fetch_remote("https://cdn.jsdelivr.net/npm/handsontable@latest/dist/handsontable.full.min.css","css",None),
fetch_remote("https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" ,"js", None),
fetch_remote("https://cdnjs.cloudflare.com/ajax/libs/jquery/3.4.1/jquery.slim.min.js","js",None),
fetch_remote("https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js","js",None)
]

