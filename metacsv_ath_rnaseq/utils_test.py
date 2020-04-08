
# from metacsv.util
from utils import dict_from_db_branch
def test_get_json():
	obj = dict_from_db_branch( "shouldsee","metacsv-ath-rnaseq","data")
	assert len(obj)
	pass
