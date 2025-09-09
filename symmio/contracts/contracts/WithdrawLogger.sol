// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract WithdrawLogger {
    struct WithdrawInfo {
        uint256 id;
        bytes32 token;
        uint256 amount;
        bytes32 destination;
        address user;
    }

    address public owner;

    mapping(uint256 => WithdrawInfo[]) private withdrawalsByChain;
    mapping(uint256 => uint256) public nextIdByChain;

    event WithdrawalLogged(
        uint256 chainId,
        uint256 id,
        bytes32 token,
        uint256 amount,
        bytes32 destination,
        address user
    );

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not the contract owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    // Log a withdrawal — only callable by the owner
    function logWithdrawal(
        uint256 chainId,
        bytes32 token,
        uint256 amount,
        bytes32 destination,
        address user
    ) external onlyOwner {
        uint256 newId = nextIdByChain[chainId];

        withdrawalsByChain[chainId].push(WithdrawInfo({
            id: newId,
            token: token,
            amount: amount,
            destination: destination,
            user: user
        }));

        emit WithdrawalLogged(
            chainId,
            newId,
            token,
            amount,
            destination,
            user
        );

        nextIdByChain[chainId]++;
    }

    function getWithdrawals(
        uint256 chainId,
        uint256 fromIndex,
        uint256 toIndex
    ) external view returns (WithdrawInfo[] memory) {
        WithdrawInfo[] storage all = withdrawalsByChain[chainId];
        require(toIndex > fromIndex, "Invalid range");
        require(toIndex <= all.length, "Range out of bounds");

        WithdrawInfo[] memory result = new WithdrawInfo[](toIndex - fromIndex);
        for (uint256 i = fromIndex; i < toIndex; i++) {
            result[i - fromIndex] = all[i];
        }
        return result;
    }

    function getWithdrawCount(uint256 chainId) external view returns (uint256) {
        return withdrawalsByChain[chainId].length;
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "New owner is the zero address");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }
}
