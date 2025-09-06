// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "./ISymmio.sol";

contract Symmio is ISymmio {
    address public executor;
    address public owner;

    mapping(address => uint256) public balances;

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyExecutor() {
        require(msg.sender == executor, "Not executor");
        _;
    }

    function setExecutor(address _executor) external onlyOwner {
        executor = _executor;
    }

    function virtualDepositFor(address user, uint256 amount) external onlyExecutor {
        balances[user] += amount;
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Zero address");
        owner = newOwner;
    }
}
