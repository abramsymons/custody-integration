from hashlib import sha3_256


def encode_salt(salt: int) -> bytes:
    length = (salt.bit_length() + 7) // 8
    return salt.to_bytes(length, byteorder="big", signed=False)


def compute_tweak_by(salt: bytes) -> bytes:
    return sha3_256(b"P" + salt).digest()
