import hashlib

from bitcoinutils.keys import PublicKey
from bitcoinutils.utils import tweak_taproot_pubkey
from utils import compute_tweak_by, encode_salt


def get_taproot_address(master_public: PublicKey, salt: int) -> str:
    tweak_by = compute_tweak_by(encode_salt(salt))
    tweak_int = calculate_tweak(master_public, tweak_by)
    tweak_and_odd = tweak_taproot_pubkey(master_public.key.to_string(), tweak_int)
    pubkey = tweak_and_odd[0][:32]
    is_odd = tweak_and_odd[1]

    prefix = "03" if is_odd else "02"
    compressed_pubkey = prefix + pubkey.hex()
    public_key = PublicKey(compressed_pubkey)
    taproot_address = public_key.get_taproot_address()
    return taproot_address.to_string()


def calculate_tweak(pubkey: PublicKey, tweak_by: bytes) -> int:
    key_x = pubkey.to_bytes()[:32]
    tweak = tagged_hash(key_x + tweak_by, "TapTweak")
    tweak_int = int.from_bytes(tweak, byteorder="big")
    return tweak_int


def tagged_hash(data: bytes, tag: str) -> bytes:
    tag_digest = hashlib.sha256(tag.encode()).digest()
    return hashlib.sha256(tag_digest + tag_digest + data).digest()


taproot_verifying_key = PublicKey(
    "0367e79f1483c900ff4eb46cdf31f263c4b34be7594e52d4f2a84ef7328324c556"
)

for salt in (1, 123456789, 0x5FCEB18CF62BF791D7AA0931D3159F95650A0061):
    taproot_address = get_taproot_address(taproot_verifying_key, salt)
    print(f"salt: {salt}, btc address: {taproot_address}")
