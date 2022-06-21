import sys
import hashlib


def get_file_hash(filename, hash_name='sha256', buf_size=65535):
    hash = getattr(hashlib, hash_name)()
    with open(filename, 'rb') as f:
        while True:
            data = f.read(buf_size)
            if not data:
                break
            hash.update(data)
    return hash.hexdigest()
