from struct import unpack
from typing import Any

from eth_account.messages import encode_defunct
from frost_lib.curves import secp256k1_evm, secp256k1_tr
from pydantic import BaseModel
from web3 import Web3


class FROSTVerificationError(Exception):
    pass


class ECDSAVerificationError(Exception):
    pass


class DepositChainNotFound(Exception):
    pass


class VerifyingData(BaseModel):
    header: dict[str, Any]
    verifying_shares: dict[str, str]
    verifying_key: str


KEYS = {
    "secp256k1_tr": VerifyingData(
        header={"version": 0, "ciphersuite": "FROST-secp256k1-SHA256-TR-v1"},
        verifying_shares={
            "0000000000000000000000000000000000000000000000000000000000000001": "030345e6ef7403cb1ff17828d29c67580c7ce2d8240210e4ef354eece60dd72d51",
            "0000000000000000000000000000000000000000000000000000000000000002": "03d0d3d8d7bca5dc70bd69f2ccd5790c0c76b56e859b232b86901bbc22f88a8de2",
            "0000000000000000000000000000000000000000000000000000000000000003": "030f7c59900251eaaa126d3f0a7f0aff171a1da9164e5db21290bdc4da99f39f18"
        },
        verifying_key="0234f60a2a259cdacdfe4c597254754e71e25e75ce90746041c1d99bb83377277f",
    ),
    "secp256k1_evm": VerifyingData(
        header={"version": 0, "ciphersuite": "FROST-secp256k1-SHA256-v1"},
        verifying_shares={
            "0000000000000000000000000000000000000000000000000000000000000001": "03528e5a8879b132aead053dc4c90c32fee2f20c9d2e68c540b2586819fcf088fd",
            "0000000000000000000000000000000000000000000000000000000000000002": "02db508eecea73b7e2cd13c12a28750cca37c407d77fc943a3348d2ab20c421af8",
            "0000000000000000000000000000000000000000000000000000000000000003": "02b79733a4a77c67ed878cd244c3d4c684b751a246c6e23ef729f3e87a6bcd71d6"
        },
        verifying_key="0310c0ebbcfa925561364fa44eed5429916f69d62234ccee556f96774091d18af6",
    ),
}

deposit_shield_address = "0x786bd69517Bc30eE2fC13FeDA8B1aE0e6feDbad6"


def verify_deposit_tx(tx: bytes) -> bool:
    """Verify deposit transaction."""
    msg = tx[:-129]
    frost_sig, ecdsa_sig = unpack(">64s 65s", tx[-129:])

    chain = msg[2:5]
    chain = chain.upper().decode()

    if chain == "BTC":
        curve, keys = secp256k1_tr, KEYS["secp256k1_tr"]
    elif chain in ("SEP",):
        curve, keys = secp256k1_evm, KEYS["secp256k1_evm"]
    else:
        raise ValueError(f"invalid chain={chain}")

    if curve is None:
        raise DepositChainNotFound()

    # Verify FROST signature
    try:
        frost_verified = curve.verify_group_signature(
            frost_sig.hex(),
            msg,
            keys,
        )
    except ValueError as e:
        print(f"FROST signature verification failed: {e}")
        raise FROSTVerificationError()

    # Verify ECDSA signature
    try:
        eth_signed_message = encode_defunct(tx[:-129])
        w3 = Web3()
        recovered_address = w3.eth.account.recover_message(
            eth_signed_message, signature=ecdsa_sig
        )
        ecdsa_verified = recovered_address.lower() == deposit_shield_address.lower()
    except ValueError as e:
        print(f"ECDSA signature verification failed: {e}")
        raise ECDSAVerificationError()

    return frost_verified and ecdsa_verified


if __name__ == "__main__":
    tx = b'\x01dsep\x00\x01\xcdC\xb5\xa8L\xb3\x1a\xf9]\xa4\xaf\xb1\x15\x94\xe13\xccU\x02\x82\xb9\x9eX2\xecs\xa4\xd8S\x8fQQo\x8c\xbc\xf0\xb3B\xf6\xa9\x97\x87O\x8b\xf1C\n\xdeQ8\xe1Z\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01^\xf3\xc0\x06h\xb9\xc6M\x14_\xce\xb1\x8c\xf6+\xf7\x91\xd7\xaa\t1\xd3\x15\x9f\x95e\n\x04L\x00\x00\x1f8\x86<+Vg\xbc\xe9\xe1.\xbb\xbaA\x06\x97\x94\xe1@\x9b6\x95\xb4\xc1\xbf\xaf0\xa7\xc8\x97\xa3<")\xff\xda\x95\x08\x1aw\xe9 \xebI\xeb\xfa\x1a\xdd*0\xd7\xf0w\xd3\xd9PL\x99\xef\x01m\x1a\xcf\xcd\x0cs.\xef\xad\x89\\\x12\xae4N\xd0\xc1+\x83\xaa\xe8\xdb\x06#\xf7\x9c-\xf4\xd5\x0e\x02\x97\xce\xeb\xc8A"\xd7\xe5\xe1\xd0\xef\x99\x893\xcc\xd6\xee\xbfL\xc1=L\x08#{EH\x99)\xaf\x88\xcc\xaf\n\x01U\x1c'
    verified = verify_deposit_tx(tx)
    print(f"verified: {verified}")
