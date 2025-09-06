import { expect } from "chai"
import { ethers } from "hardhat"
import { arrayify } from "@ethersproject/bytes";

describe("DepositVerifier", function () {
  let depositVerifier: any
  let schnorrVerifier: any
  let shield: string
  const depositShieldAddress = "0x786bd69517Bc30eE2fC13FeDA8B1aE0e6feDbad6"
  const verifyingPubKey = "0x026915bee07d2a4d4218f62b138ed1da3129567e633c93578d9fbba29a1a852967"
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
      "0x016461707420200001b12ea2bd1b83a1dc481e18707ad0cf5022501f5040b0bc6ab65842588efd0e0b00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005f5e1000868bc4564145fceb18cf62bf791d7aa0931d3159f95650a045c0085418c96c23a89bc7406cc6126550fb950711abe38589900dd5dca46c8634935b6c1e0e34f6fc1a57ff3a8630f7dbd7b21d8e6570e3dc4f4d2372f00bd30313efdb710cb892b967aac6a3f6089d6e6bef58ae7938b7952b2fa4016a301633f005247cd68a32014109eedda961df86f70d2839b8acabc57d081f35d52113bf6d11c"

    const txBytes = arrayify(hex)
    const result = await depositVerifier.verifyDeposit(txBytes)

    expect(result).to.be.true
  })
})
