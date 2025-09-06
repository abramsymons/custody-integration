from aptos_sdk import ed25519
from aptos_sdk.account_address import AccountAddress


from zexfrost.custom_types import PublicKeyPackage


verifying_key = PublicKeyPackage.model_validate({
    "header": {
        "version": 0,
        "ciphersuite": "FROST-ED25519-SHA512-v1"
    },
    "verifying_shares": {
        "0000000000000000000000000000000000000000000000000000000000000001": "f71b6a3d148db6d6c8dcda46d25620ea029959b7321d93de381c89b9ead0eb4d",
        "0000000000000000000000000000000000000000000000000000000000000002": "69b02cb070decdf156243d772e4f72cffcb3341caa796893e4229152af48a6d1",
        "0000000000000000000000000000000000000000000000000000000000000003": "c6768aaffc14e9486ce8712da724ee0873e185d6c9d70311d9af4adbde9dc139"
    },
    "verifying_key": "0243320c99839580a4b1aff327be6d512df8fbc522b7e8ee21d620b3641fb147"
})

def compute_apt_tweaked_pubkey(pubkey_package: PublicKeyPackage, salt: str) -> PublicKeyPackage:
    assert salt.startswith("0x"), "salt should be a hexstr"
    tweak_by = bytes.fromhex(salt[2:])
    from frost_lib import ed25519 as frost
    pubkey_package_tweaked = frost.pubkey_package_tweak(pubkey_package, tweak_by)
    return pubkey_package_tweaked


def compute_apt_address(salt: str) -> str:
    """Compute Aptos address from public key package and salt."""
    sender = compute_apt_tweaked_pubkey(verifying_key, salt)
    sender_pub = ed25519.PublicKey.from_str(sender.verifying_key)
    tweaked_address = AccountAddress.from_key(sender_pub)
    return str(tweaked_address)

if __name__ == "__main__":
    address = compute_apt_address("0x7314b5cb4E67450EF311a1a5e0c79f0D7424072e")
    print(address)