from struct import unpack
from typing import Any

from eth_account.messages import encode_defunct
from frost_lib.curves import secp256k1_evm as curve
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


KEY = VerifyingData(
    header={"version": 0, "ciphersuite": "FROST-secp256k1-SHA256-v1"},
    verifying_shares={
        "0000000000000000000000000000000000000000000000000000000000000001": "0339469c66213e1264cbdf2a4faa2c82654269b3fc61ede089698b15bf2aed114b",
        "0000000000000000000000000000000000000000000000000000000000000002": "03f063313f92fe4ed08bfa6fbcb78bead0d54d21f6eff1144436f9b58b98421693",
        "0000000000000000000000000000000000000000000000000000000000000003": "033a2a65cb0ed78232df2100eecfd85bbcb6d206aa8beae33cbb0b089f56240bce",
    },
    verifying_key="0272bd8a7ce4e81f9dea3c43f88eafe7ac96ad795e70544a31b5a2fb9d7ea5c674",
)

deposit_shield_address = "0x786bd69517Bc30eE2fC13FeDA8B1aE0e6feDbad6"


def verify_deposit_tx(tx: bytes) -> bool:
    """Verify deposit transaction."""
    msg = tx[:-129]
    frost_sig, ecdsa_sig = unpack(">64s 65s", tx[-129:])

    chain = msg[2:5]
    chain = chain.upper().decode()

    if curve is None:
        raise DepositChainNotFound()

    # Verify FROST signature
    try:
        frost_verified = curve.verify_group_signature(
            frost_sig.hex(),
            msg,
            KEY,
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
    tx = b"\x01dsep \x14\x00\x01 ~e3\r{TF\x0cWr\x83\xff\x89\x8a\x81\xc6\xb0f\n\x8d\x18q\xe6Y/\xbedU\xca\xa2@o\x8c\xbc\xf0\xb3B\xf6\xa9\x97\x87O\x8b\xf1C\n\xdeQ8\xe1Z\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x155\xb0\x06h\xdas\xea\x14_\xce\xb1\x8c\xf6+\xf7\x91\xd7\xaa\t1\xd3\x15\x9f\x95e\n\x04I\x00\xf9\x19\x1e\x14\x0c\xde\xeb\xb5\x14\x00]Q\xc7\xce\xfcJ\xa3\x19\xa2\xd8\r%w\xc0D-\xa0\xe2\x96\xc1\\\xaa\xb5\x03CL\xd7\x96Y\x17Y\x98\x00\x8be\xcd\x9a\x0b[\xb6\xaa1W\xa6e2\xb2\x7f\xdc\xb82\xb0\xcb\xc9S\xb5\xcb\x12I8\xf1v\xa49\xa1x\xe4\xa6\xe5\xc4\xa3\x02*\xf9\xcb\xeb\xaa\xfc\xaf,%\x08\x8a82\xdfD~,\x83S\xad\xfa\xb5-=\x93\x1f\x94&Y\x01?\xac\xc0\xee(bc%|\xec\x18f\xd65\xc3\xe2\x1b"
    verified = verify_deposit_tx(tx)
    print(f"verified: {verified}")
