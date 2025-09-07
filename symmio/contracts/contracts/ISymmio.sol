// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface ISymmio {
    function virtualDepositAndAllocateFor(
        address user,
        uint256 amount
    ) external;
}
