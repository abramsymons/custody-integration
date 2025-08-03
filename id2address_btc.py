import hashlib

from bitcoinutils.keys import PublicKey
from bitcoinutils.utils import tweak_taproot_pubkey


def get_taproot_address(master_public: PublicKey, salt: int) -> str:
    tweak_int = calculate_tweak(master_public, salt)
    tweak_and_odd = tweak_taproot_pubkey(master_public.key.to_string(), tweak_int)
    pubkey = tweak_and_odd[0][:32]
    is_odd = tweak_and_odd[1]

    prefix = "03" if is_odd else "02"
    compressed_pubkey = prefix + pubkey.hex()
    public_key = PublicKey(compressed_pubkey)
    taproot_address = public_key.get_taproot_address()
    return taproot_address.to_string()


def calculate_tweak(pubkey: PublicKey, salt: int) -> int:
    key_x = pubkey.to_bytes()[:32]
    salt_bytes = salt.to_bytes(32, byteorder="big")
    tweak = tagged_hash(key_x + salt_bytes, "TapTweak")
    tweak_int = int.from_bytes(tweak, byteorder="big")
    return tweak_int


def tagged_hash(data: bytes, tag: str) -> bytes:
    tag_digest = hashlib.sha256(tag.encode()).digest()
    return hashlib.sha256(tag_digest + tag_digest + data).digest()


taproot_verifying_key = PublicKey(
    "03fba30c7f6d8560c86845c74e38f64b8c8dfb2f95c46333b11890185d069db91b"
)

for salt in (1, 123456789, 0x5fCeb18CF62bF791d7Aa0931D3159f95650A0061):
    taproot_address = get_taproot_address(taproot_verifying_key, salt)
    print(f"salt: {salt}, btc address: {taproot_address}")
