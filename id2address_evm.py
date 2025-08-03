from eth_typing.encoding import HexStr
from eth_utils.address import to_checksum_address
from eth_utils.crypto import keccak
from web3 import Web3


def get_create2_address(
    factory_address: str,
    salt: int,
    bytecode_hash: str,
) -> str:
    factory_address = Web3.to_bytes(hexstr=HexStr(factory_address))
    salt = salt.to_bytes(32, "big")
    bytecode_hash = Web3.to_bytes(hexstr=HexStr(bytecode_hash))

    data = b"\xff" + factory_address + salt + bytecode_hash
    address_bytes = keccak(data)[12:]  # Take the last 20 bytes
    return to_checksum_address(address_bytes)


factory_address = "0x06bcEa7a0cf5AA9A28cB3c6C8e799Ac4D44024e3"
byte_code_hash = "0x2da6a0b42d3d9a39b48fa6b598ed1e3db10547faf2922de05a9953ef7de23de6"

for salt in (1, 123456789, 0x5fCeb18CF62bF791d7Aa0931D3159f95650A0061):
    evm_address = get_create2_address(factory_address, salt, byte_code_hash)
    print(f"salt: {salt}, evm address: {evm_address}")
