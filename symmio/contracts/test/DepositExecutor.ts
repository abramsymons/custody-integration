import { expect } from "chai";
import { ethers } from "hardhat";
import { arrayify } from "@ethersproject/bytes";

const DEPOSIT_TX =
  "0x01647365700001d68a41dfaeef7368b28b82d7b12a177d3f4a6b1e09b1bafd67252656a5a198326f8cbcf0b342f6a997874f8bf1430ade5138e15a000000000000000000000000000000000000000000000000000000000614658006688206d000000000000000160020f50a58fce6f7619d9f780a8beb34c73c2fe9b58e96a8730343997ca4e6cc65835d2ce3f835ea9ad48961f915ad2f23286341a294d3a1be329c80651d47d45908bc6cde06351ee8b53fd71942ba17812d15ae84e4a7cd5079ef13f35849e3dc69fe830b63c62c66f5f09f314aa6048c79519cba3f041671c39c36c6a5eb2ef21c";

describe("DepositExecutor", function () {
  let symmio: any;
  let executor: any;
  let depositVerifier: any;
  let txData: Uint8Array;

  before(async () => {
    const [deployer] = await ethers.getSigners();

    // Reuse pattern from DepositVerifier test
    const shieldAddress = "0x786bd69517Bc30eE2fC13FeDA8B1aE0e6feDbad6";
    const pubkey =
      "0x0361a7241715d3d5d80b0c0cd3811765b1d2e38050b8a3f2d73e2488c93e4a0b64";
    const pubkeyBytes = arrayify(pubkey);

    const SchnorrVerifier = await ethers.getContractFactory(
      "SchnorrSECP256K1Verifier"
    );
    const schnorrVerifier = await SchnorrVerifier.deploy();
    await schnorrVerifier.waitForDeployment();

    const DepositVerifier = await ethers.getContractFactory("DepositVerifier");
    depositVerifier = await DepositVerifier.deploy(
      schnorrVerifier.target,
      shieldAddress,
      pubkeyBytes
    );
    await depositVerifier.waitForDeployment();

    const Symmio = await ethers.getContractFactory("Symmio");
    symmio = await Symmio.deploy();
    await symmio.waitForDeployment();

    const Parser = await ethers.getContractFactory("DepositParser");
    const parser = await Parser.deploy();
    await parser.waitForDeployment();

    const Executor = await ethers.getContractFactory("DepositExecutor");
    executor = await Executor.deploy(
      await symmio.getAddress(),
      await depositVerifier.getAddress(),
      await parser.getAddress()
    );
    await executor.waitForDeployment();

    await symmio.setExecutor(await executor.getAddress());

    txData = arrayify(DEPOSIT_TX);
  });

  it("should ignore deposit with invalid pair", async () => {
    await expect(executor.executeDeposit(txData)).to.not.be.reverted;
    const balance = await symmio.balances(22);
    expect(balance).to.equal(0n);
  });

  it("should accept deposit after marking pair as valid", async () => {
    await executor.setPairValid(
      "sep",
      "0x6f8cbCf0b342f6a997874F8bf1430ADE5138e15a",
      true
    );
    await expect(executor.executeDeposit(txData)).to.not.be.reverted;
    const balance = await symmio.balances(22);
    expect(balance).to.equal(102000000n);
  });

  it("should ignore replayed deposit", async () => {
    await expect(executor.executeDeposit(txData)).to.not.be.reverted;
    const balance = await symmio.balances(22);
    expect(balance).to.equal(102000000n); // Should remain unchanged
  });
});
