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
      "736570" + // "sep"
      "0001" + // count (1)
      "d68a41dfaeef7368b28b82d7b12a177d3f4a6b1e09b1bafd67252656a5a19832" + // tx_hash
      "6f8cbcf0b342f6a997874f8bf1430ade5138e15a" + // token_contract
      "0000000000000000000000000000000000000000000000000000000006146580" + // amount (102e6)
      "06" + // decimal
      "688206d0" + // time (1753351888)
      "0000000000000016" + // user_id (22)
      "00"; // vout

    const txBytes = "0x" + txHex;

    const parsed = await parser.parseDepositTx(txBytes);

    expect(parsed.version).to.equal(1);
    expect(parsed.operation).to.equal("0x64"); // ASCII 'd'
    expect(parsed.chain).to.equal("sep");

    const deposit = parsed.deposits[0];
    expect(deposit.txHash).to.equal("0xd68a41dfaeef7368b28b82d7b12a177d3f4a6b1e09b1bafd67252656a5a19832");
    expect(deposit.tokenContract).to.equal("0x6f8cbCf0b342f6a997874F8bf1430ADE5138e15a");
    expect(deposit.amount).to.equal("102000000");
    expect(deposit.decimal).to.equal(6);
    expect(deposit.time).to.equal(1753351888);
    expect(deposit.userId).to.equal(22);
    expect(deposit.vout).to.equal(0);
  });
});
