// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./ISchnorrSECP256K1Verifier.sol";

contract DepositVerifier {
    ISchnorrSECP256K1Verifier public schnorrVerifier;

    address public shieldSigner;
    bytes public frostPublicKey;

    constructor(
        address _schnorrVerifier,
        address _shieldSigner,
        bytes memory _frostPublicKey
    ) {
        schnorrVerifier = ISchnorrSECP256K1Verifier(_schnorrVerifier);
        shieldSigner = _shieldSigner;
        frostPublicKey = _frostPublicKey;
    }

    /// @dev Verifies both the Schnorr and ECDSA signatures of a deposit transaction
    function verifyDeposit(
        bytes calldata txData
    ) external view returns (bool) {
        require(txData.length > 129, "Invalid tx length");

        bytes memory message = txData[:txData.length - 129];
        bytes memory schnorrSig = txData[txData.length - 129 : txData.length - 65];
        bytes memory ecdsaSig = txData[txData.length - 65 :];

        // Schnorr verify
        bytes32 msgHash = keccak256(message);
        bool frostValid = schnorrVerifier.verifySignature(frostPublicKey, schnorrSig, uint256(msgHash));
        require(frostValid, "FROST verification failed");

        // ECDSA verify
        address signer = getSigner(message, ecdsaSig);
        require(signer == shieldSigner, "ECDSA signature invalid");

        return true;
    }

    function getSigner(
        bytes memory rawMsg,
        bytes memory signature
    ) public pure returns (address recoveredSigner) {
        // Signature consists of r, s, and v
        require(signature.length == 65, "Invalid signature length");

        bytes32 r;
        bytes32 s;
        uint8 v;

        // Extract r, s, v from the signature
        assembly {
            r := mload(add(signature, 0x20))
            s := mload(add(signature, 0x40))
            v := byte(0, mload(add(signature, 0x60)))
        }

        // Adjust v for compatibility with `ecrecover`
        if (v < 27) {
            v += 27;
        }

        // Ensure v is valid
        require(v == 27 || v == 28, "Invalid v value");

        // Recover the signer address
        bytes32 msgHash = keccak256(
            abi.encodePacked(
                "\x19Ethereum Signed Message:\n",
                uintToString(rawMsg.length),
                rawMsg
            )
        );
        recoveredSigner = ecrecover(msgHash, v, r, s);
    }

    function uintToString(uint256 v) internal pure returns (string memory) {
        if (v == 0) return "0";
        uint256 maxlength = 100;
        bytes memory reversed = new bytes(maxlength);
        uint256 i = 0;
        while (v != 0) {
            uint8 remainder = uint8(v % 10);
            v = v / 10;
            reversed[i++] = bytes1(48 + remainder);
        }
        bytes memory s = new bytes(i);
        for (uint256 j = 0; j < i; j++) {
            s[j] = reversed[i - j - 1];
        }
        return string(s);
    }
}
