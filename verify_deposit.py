from struct import unpack
from typing import Any

from eth_account.messages import encode_defunct
from frost_lib.curves import secp256k1_evm, secp256k1_tr, ed25519
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
            "0000000000000000000000000000000000000000000000000000000000000001": "02759da1d09403158e43fb6427884f94d3d0f74bda020eb2c6323608a78eb357ee",
            "0000000000000000000000000000000000000000000000000000000000000002": "02d88a09e81b662c86c52e474579497fc4f44e405ec369199514e670792057d599",
            "0000000000000000000000000000000000000000000000000000000000000003": "03f2ef0088e6fc5d21ef18d4d212163cdce6525638123e004609b6feaf18981446"
        },
        verifying_key="0367e79f1483c900ff4eb46cdf31f263c4b34be7594e52d4f2a84ef7328324c556",
    ),
    "secp256k1_evm": VerifyingData(
        header={"version": 0, "ciphersuite": "FROST-secp256k1-SHA256-v1"},
        verifying_shares={
            "0000000000000000000000000000000000000000000000000000000000000001": "02e2a72e964c746d72538a42a712b240ad680f0e8d1d240a4c68a7b054cfc1a085",
            "0000000000000000000000000000000000000000000000000000000000000002": "023f3a1322b880be0f073d30a5df1b0edc9518e64762320534c1e51bb743470876",
            "0000000000000000000000000000000000000000000000000000000000000003": "03a4b318d6605669cf5bd297dfe2d6dc86ac42180db6dd161a6568b17fc6e4542d"
        },
        verifying_key="026915bee07d2a4d4218f62b138ed1da3129567e633c93578d9fbba29a1a852967",
    ),
    "ed25519": VerifyingData(
        header={"version": 0, "ciphersuite": "FROST-ED25519-SHA512-v1"},
        verifying_shares={
            "0000000000000000000000000000000000000000000000000000000000000001": "f71b6a3d148db6d6c8dcda46d25620ea029959b7321d93de381c89b9ead0eb4d",
            "0000000000000000000000000000000000000000000000000000000000000002": "69b02cb070decdf156243d772e4f72cffcb3341caa796893e4229152af48a6d1",
            "0000000000000000000000000000000000000000000000000000000000000003": "c6768aaffc14e9486ce8712da724ee0873e185d6c9d70311d9af4adbde9dc139"
        },
        verifying_key="0243320c99839580a4b1aff327be6d512df8fbc522b7e8ee21d620b3641fb147",
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
        curve, keys = secp256k1_evm, KEYS["secp256k1_evm"]
    elif chain in ("SEP",):
        curve, keys = secp256k1_evm, KEYS["secp256k1_evm"]
    elif chain in ("APT",):
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
    tx = b'\x01dapt  \x00\x01\xb1.\xa2\xbd\x1b\x83\xa1\xdcH\x1e\x18pz\xd0\xcfP"P\x1fP@\xb0\xbcj\xb6XBX\x8e\xfd\x0e\x0b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\xf5\xe1\x00\x08h\xbcEd\x14_\xce\xb1\x8c\xf6+\xf7\x91\xd7\xaa\t1\xd3\x15\x9f\x95e\n\x04\\\x00\x85A\x8c\x96\xc2:\x89\xbct\x06\xcca&U\x0f\xb9Pq\x1a\xbe8X\x99\x00\xdd]\xcaF\xc8cI5\xb6\xc1\xe0\xe3Oo\xc1\xa5\x7f\xf3\xa8c\x0f}\xbd{!\xd8\xe6W\x0e=\xc4\xf4\xd27/\x00\xbd01>\xfd\xb7\x10\xcb\x89+\x96z\xacj?`\x89\xd6\xe6\xbe\xf5\x8a\xe7\x93\x8byR\xb2\xfa@\x16\xa3\x01c?\x00RG\xcdh\xa3 \x14\x10\x9e\xed\xda\x96\x1d\xf8op\xd2\x83\x9b\x8a\xca\xbcW\xd0\x81\xf3]R\x11;\xf6\xd1\x1c'
    verified = verify_deposit_tx(tx)
    print(f"verified: {verified}")
