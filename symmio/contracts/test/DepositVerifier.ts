import { expect } from "chai"
import { ethers } from "hardhat"
import { arrayify } from "@ethersproject/bytes";

describe("DepositVerifier", function () {
  let depositVerifier: any
  let schnorrVerifier: any
  let shield: string
  const depositShieldAddress = "0x786bd69517Bc30eE2fC13FeDA8B1aE0e6feDbad6"
  const verifyingPubKey = "0x0361a7241715d3d5d80b0c0cd3811765b1d2e38050b8a3f2d73e2488c93e4a0b64"
  const pubkeyBytes = arrayify(verifyingPubKey)

  beforeEach(async function () {
    shield = depositShieldAddress

    const SchnorrVerifier = await ethers.getContractFactory("SchnorrSECP256K1Verifier")
    schnorrVerifier = await SchnorrVerifier.deploy()
    await schnorrVerifier.waitForDeployment();

    const DepositVerifier = await ethers.getContractFactory("DepositVerifier")
    depositVerifier = await DepositVerifier.deploy(schnorrVerifier.target, shield, pubkeyBytes)
    await depositVerifier.waitForDeployment()
  })

  it("should verify a valid deposit transaction", async function () {
    const hex =
      "0x01647365700001d68a41dfaeef7368b28b82d7b12a177d3f4a6b1e09b1bafd67252656a5a198326f8cbcf0b342f6a997874f8bf1430ade5138e15a000000000000000000000000000000000000000000000000000000000614658006688206d000000000000000160020f50a58fce6f7619d9f780a8beb34c73c2fe9b58e96a8730343997ca4e6cc65835d2ce3f835ea9ad48961f915ad2f23286341a294d3a1be329c80651d47d45908bc6cde06351ee8b53fd71942ba17812d15ae84e4a7cd5079ef13f35849e3dc69fe830b63c62c66f5f09f314aa6048c79519cba3f041671c39c36c6a5eb2ef21c"

    const txBytes = arrayify(hex)
    const result = await depositVerifier.verifyDeposit(txBytes)

    expect(result).to.be.true
  })
})
