// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract DepositParser {
    struct Deposit {
        bytes32 txHash;
        address tokenContract;
        uint256 amount;
        uint8 decimal;
        uint32 time;
        address user;
        uint8 vout;
    }

    struct DepositTransaction {
        uint8 version;
        bytes1 operation;
        string chain;
        Deposit[] deposits;
    }

    function parseDepositTx(bytes calldata txData) external pure returns (DepositTransaction memory parsed) {
        require(txData.length >= 7, "Invalid tx header");

        uint8 version = uint8(txData[0]);
        bytes1 operation = txData[1];
        string memory chain = string(abi.encodePacked(txData[2], txData[3], txData[4]));
        uint16 count = (uint16(uint8(txData[5])) << 8) | uint8(txData[6]);

        uint256 offset = 7;
        uint256 depositSize = 111;
        require(txData.length >= offset + count * depositSize, "Invalid deposit count or data");

        Deposit[] memory deposits = new Deposit[](count);
        for (uint16 i = 0; i < count; i++) {
            uint256 pos = offset + i * depositSize;
            deposits[i] = parseDeposit(txData, pos);
        }

        parsed = DepositTransaction({
            version: version,
            operation: operation,
            chain: chain,
            deposits: deposits
        });
    }

    function parseDeposit(bytes calldata data, uint256 pos) internal pure returns (Deposit memory d) {
        d.txHash = bytes32(data[pos:pos + 32]);
        pos += 32;

        d.tokenContract = bytesToAddress(data[pos:pos + 20]);
        pos += 20;

        d.amount = bytesToUint(data[pos:pos + 32]);
        pos += 32;

        d.decimal = uint8(data[pos]);
        pos += 1;

        d.time = bytesToUint32(data[pos:pos + 4]);
        pos += 4;

        uint8 saltLen = uint8(data[pos]);
        pos += 1;
        require(saltLen == 20, "Invalid salt length");
        d.user = bytesToAddress(data[pos:pos + 20]);
        pos += 20;

        d.vout = uint8(data[pos]);
    }

    function bytesToAddress(bytes calldata b) internal pure returns (address addr) {
        require(b.length == 20, "Invalid address length");
        assembly {
            addr := shr(96, calldataload(b.offset))
        }
    }

    function bytesToUint(bytes calldata b) internal pure returns (uint256 result) {
        require(b.length == 32, "Invalid uint256 length");
        assembly {
            result := calldataload(b.offset)
        }
    }

    function bytesToUint32(bytes calldata b) internal pure returns (uint32 result) {
        require(b.length == 4, "Invalid uint32 length");
        assembly {
            result := shr(224, calldataload(b.offset))
        }
    }
}
