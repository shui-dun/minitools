import hashlib

def sha256(text):
    """
    计算文本的sha256值
    """
    hash_object = hashlib.sha256()
    hash_object.update(text.encode())
    return hash_object.hexdigest()

if __name__ == '__main__':
    print(sha256('test'))