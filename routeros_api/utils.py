def get_bytes(string: bytes | str) -> bytes:
    if hasattr(string, 'encode'):
        return string.encode()
    else:
        return string
