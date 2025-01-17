import hashlib
from typing import Any

import orjson


# FIXME: Remove after fixing 'pool_id' parsing
def get_pool_id(pool_id_dict: Any) -> str:
    dump = orjson.dumps(pool_id_dict)
    hash_object = hashlib.sha256(dump)
    return hash_object.hexdigest()[:16]
