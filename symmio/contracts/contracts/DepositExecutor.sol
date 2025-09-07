// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "./DepositParser.sol";
import "./DepositVerifier.sol";
import "./ISymmio.sol";

contract DepositExecutor {
    address public owner;
    ISymmio public symmio;
    DepositVerifier public verifier;
    DepositParser public parser;

    mapping(bytes32 => bool) public usedDeposits;
    mapping(bytes32 => bool) public validPairs;

    event DepositProcessed(string chain, bytes32 token, address user, uint256 amount);
    event DepositIgnored(string chain, bytes32 token, address user, string reason);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    event PairUpdated(string chain, bytes32 token, bool valid);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor(
        address _symmio,
        address _verifier,
        address _parser
    ) {
        owner = msg.sender;
        symmio = ISymmio(_symmio);
        verifier = DepositVerifier(_verifier);
        parser = DepositParser(_parser);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid owner");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    function setPairValid(string calldata chain, bytes32 token, bool valid) external onlyOwner {
        bytes32 key = keccak256(abi.encodePacked(chain, token));
        validPairs[key] = valid;
        emit PairUpdated(chain, token, valid);
    }

    function setSymmio(address _symmio) external onlyOwner {
        symmio = ISymmio(_symmio);
    }

    function isValidPair(string memory chain, bytes32 token) public view returns (bool) {
        return validPairs[keccak256(abi.encodePacked(chain, token))];
    }

    function getDepositKey(string memory chain, bytes32 txHash, uint8 vout) public pure returns (bytes32) {
        return keccak256(abi.encodePacked(chain, txHash, vout));
    }

    function executeDeposit(bytes calldata txData) external {
        require(verifier.verifyDeposit(txData), "Invalid deposit");

        DepositParser.DepositTransaction memory txObj = parser.parseDepositTx(txData);
        for (uint256 i = 0; i < txObj.deposits.length; i++) {
            DepositParser.Deposit memory d = txObj.deposits[i];
            // Validate token pair
            if (!isValidPair(txObj.chain, d.tokenContract)) {
                emit DepositIgnored(txObj.chain, d.tokenContract, d.user, "Invalid pair");
                continue;
            }

            // Check replay protection
            bytes32 key = getDepositKey(txObj.chain, d.txHash, d.vout);
            if (usedDeposits[key]) {
                emit DepositIgnored(txObj.chain, d.tokenContract, d.user, "Already used");
                continue;
            }
            usedDeposits[key] = true;
            require(d.decimal <= 18, "Token decimals > 18");
            uint256 amount18 = d.decimal == 18 ? d.amount : d.amount * 10 ** (18 - d.decimal);
            symmio.virtualDepositAndAllocateFor(d.user, amount18);
            emit DepositProcessed(txObj.chain, d.tokenContract, d.user, amount18);
        }
    }
}
