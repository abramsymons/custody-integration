const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("DepositParser", function () {
  it("should correctly parse the deposit transaction", async function () {
    const DepositParser = await ethers.getContractFactory("DepositParser");
    const parser = await DepositParser.deploy();
    await parser.waitForDeployment();
    const txHex =
      "01" + // version
      "64" + // operation ('d')
      "617074" + // "apt"
      "20" + // tx hash length
      "20" + // token contract address length
      "0001" + // count (1)
      "b12ea2bd1b83a1dc481e18707ad0cf5022501f5040b0bc6ab65842588efd0e0b" + // tx_hash
      "0000000000000000000000000000000000000000000000000000000000000000" + // token_contract
      "0000000000000000000000000000000000000000000000000000000005f5e100" + // amount (10e8)
      "08" + // decimal
      "68bc4564" + // time (1757168996)
      "14" + // salt length (20)
      "5fceb18cf62bf791d7aa0931d3159f95650a045c" + // salt
      "00"; // vout

    const txBytes = "0x" + txHex;

    const parsed = await parser.parseDepositTx(txBytes);

    expect(parsed.version).to.equal(1);
    expect(parsed.operation).to.equal("0x64"); // ASCII 'd'
    expect(parsed.chain).to.equal("apt");

    const deposit = parsed.deposits[0];
    expect(deposit.txHash).to.equal("0xb12ea2bd1b83a1dc481e18707ad0cf5022501f5040b0bc6ab65842588efd0e0b");
    expect(deposit.tokenContract).to.equal("0x0000000000000000000000000000000000000000000000000000000000000000");
    expect(deposit.amount).to.equal("100000000");
    expect(deposit.decimal).to.equal(8);
    expect(deposit.time).to.equal(1757168996);
    expect(deposit.user.toLowerCase()).to.equal("0x5fceb18cf62bf791d7aa0931d3159f95650a045c");
    expect(deposit.vout).to.equal(0);
  });
});
