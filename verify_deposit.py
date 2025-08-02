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
            "0000000000000000000000000000000000000000000000000000000000000001": "031dd603239a4f497cc72fcceb709cc23fd5a12b51800809f23961d1feb437153a",
            "0000000000000000000000000000000000000000000000000000000000000002": "02fe7f8e444fbf7f4a01850813a58bcfa20a49dc4c608f28ffca7a54acd7c547ea",
            "0000000000000000000000000000000000000000000000000000000000000003": "0389ebb2b0626a54ca0169284d55f35c05293cbf3cd93ef073ba92018214e9b1f0",
        },
        verifying_key="03fba30c7f6d8560c86845c74e38f64b8c8dfb2f95c46333b11890185d069db91b",
    ),
    "secp256k1_evm": VerifyingData(
        header={"version": 0, "ciphersuite": "FROST-secp256k1-SHA256-v1"},
        verifying_shares={
            "0000000000000000000000000000000000000000000000000000000000000001": "026e13aad444b45b14502c3187c8962ffa6f90dbdd9fb29b396c6bd2dc8ca56696",
            "0000000000000000000000000000000000000000000000000000000000000002": "02aefc98957b6804a92feb682a7808a5a92cf0a50fc024f22f0f8e2c0f466dd059",
            "0000000000000000000000000000000000000000000000000000000000000003": "039f7fcdaa63ba90e9e505ee7f7072fb26137a2f900bdd6a6768be2cff9f48ed6a",
        },
        verifying_key="0361a7241715d3d5d80b0c0cd3811765b1d2e38050b8a3f2d73e2488c93e4a0b64",
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
    tx = b"\x01dsep\x00\x01\xd6\x8aA\xdf\xae\xefsh\xb2\x8b\x82\xd7\xb1*\x17}?Jk\x1e\t\xb1\xba\xfdg%&V\xa5\xa1\x982o\x8c\xbc\xf0\xb3B\xf6\xa9\x97\x87O\x8b\xf1C\n\xdeQ8\xe1Z\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x06\x14e\x80\x06h\x82\x06\xd0\x00\x00\x00\x00\x00\x00\x00\x16\x00 \xf5\nX\xfc\xe6\xf7a\x9d\x9fx\n\x8b\xeb4\xc7</\xe9\xb5\x8e\x96\xa8s\x03C\x99|\xa4\xe6\xcce\x83],\xe3\xf85\xea\x9a\xd4\x89a\xf9\x15\xad/#(cA\xa2\x94\xd3\xa1\xbe2\x9c\x80e\x1dG\xd4Y\x08\xbcl\xde\x065\x1e\xe8\xb5?\xd7\x19B\xba\x17\x81-\x15\xae\x84\xe4\xa7\xcdPy\xef\x13\xf3XI\xe3\xdci\xfe\x83\x0bc\xc6,f\xf5\xf0\x9f1J\xa6\x04\x8cyQ\x9c\xba?\x04\x16q\xc3\x9c6\xc6\xa5\xeb.\xf2\x1c"
    verified = verify_deposit_tx(tx)
    print(f"verified: {verified}")
