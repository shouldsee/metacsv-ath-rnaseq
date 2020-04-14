import smhasher
import numbers
try:
    ## py2
    unicode
except:
    ## py3
    unicode = str
    basestring = (str, bytes)
# from path import Path
def hash_str(s):
    return smhasher.murmur3_x86_64(s)
def hash_tree(o):
    '''
    PY3 turns on hash randomisation by default. 
    Here a deterministic hash function is used to replace default hash function

    '''
    assert 0,'Obsolete'
    if hasattr(o,'_hash_method'):
        return o._hash_method()
    elif o is None:
        return None.__hash__()
    elif isinstance(o,dict):
        return hash_tree(tuple(sorted(o.items())))
    elif isinstance(o,(bytes,str)):
        return hash_str(o)
    elif isinstance(o, list):
        return hash_tree(tuple(o))
    elif isinstance(o, tuple):
        return tuple.__hash__(tuple(map(hash_tree,o))) 
    elif isinstance(o, numbers.Number):
        return o.__hash__()
    elif isinstance(o, frozenset):
        return hash_tree(tuple(sorted(x for x in o)))
    elif isinstance(o,set):
        return hash_tree(frozenset(o))
    else:
        assert 0,('Unable to hash',type(o),repr(o))
hash_nr = _hash = hash_tree
