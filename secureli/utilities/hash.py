import hashlib


def hash_config(config: str) -> str:
    """
    Creates an MD5 hash from a config string
    :return: A hash string
    """
    config_hash = hashlib.md5(config.encode("utf8"), usedforsecurity=False).hexdigest()

    return config_hash
