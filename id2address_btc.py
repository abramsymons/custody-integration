import hashlib

from bitcoinutils.keys import P2trAddress, PublicKey
from bitcoinutils.utils import tweak_taproot_pubkey


def get_taproot_address(master_public: PublicKey, user_id: int) -> str:
    tweak_int = calculate_tweak(master_public, user_id)
    tweak_and_odd = tweak_taproot_pubkey(master_public.key.to_string(), tweak_int)
    pubkey = tweak_and_odd[0][:32]
    is_odd = tweak_and_odd[1]

    prefix = "03" if is_odd else "02"
    compressed_pubkey = prefix + pubkey.hex()
    public_key = PublicKey(compressed_pubkey)
    taproot_address = public_key.get_taproot_address()
    return taproot_address.to_string()


def calculate_tweak(pubkey: PublicKey, user_id: int) -> int:
    key_x = pubkey.to_bytes()[:32]
    user_id_bytes = user_id.to_bytes(8, byteorder="big")
    tweak = tagged_hash(key_x + user_id_bytes, "TapTweak")
    tweak_int = int.from_bytes(tweak, byteorder="big")
    return tweak_int


def tagged_hash(data: bytes, tag: str) -> bytes:
    tag_digest = hashlib.sha256(tag.encode()).digest()
    return hashlib.sha256(tag_digest + tag_digest + data).digest()


taproot_verifying_key = PublicKey(
    "03fba30c7f6d8560c86845c74e38f64b8c8dfb2f95c46333b11890185d069db91b"
)

for user_id in range(100):
    taproot_address = get_taproot_address(taproot_verifying_key, user_id)
    print(f"user id: {user_id}, btc address: {taproot_address}")
