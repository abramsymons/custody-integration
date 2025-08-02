// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface ISymmio {
    function deposit(
        uint64 userId,
        uint256 amount
    ) external;
}
