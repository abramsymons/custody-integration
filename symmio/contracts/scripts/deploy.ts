import { ethers, run } from "hardhat";
import { arrayify } from "@ethersproject/bytes";

async function verifyContract(address: string, constructorArgs: any[] = []) {
  console.log(`Verifying: ${address}`);
  try {
    await run("verify:verify", {
      address,
      constructorArguments: constructorArgs,
    });
    console.log("✅ Verified");
  } catch (err: any) {
    if (err.message.toLowerCase().includes("already verified")) {
      console.log("✔ Already verified");
    } else {
      console.error("❌ Verification failed:", err);
    }
  }
}

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with:", deployer.address);

  const schnorrPubKey = "0x026915bee07d2a4d4218f62b138ed1da3129567e633c93578d9fbba29a1a852967";
  const shieldAddress = "0x786bd69517Bc30eE2fC13FeDA8B1aE0e6feDbad6";
  const schnorrKeyBytes = arrayify(schnorrPubKey);

  // Deploy Schnorr Verifier
  const Schnorr = await ethers.getContractFactory("SchnorrSECP256K1Verifier");
  const schnorr = await Schnorr.deploy();
  await schnorr.waitForDeployment();
  const schnorrAddr = await schnorr.getAddress();

  // Deploy Deposit Verifier
  const DepositVerifier = await ethers.getContractFactory("DepositVerifier");
  const depositVerifier = await DepositVerifier.deploy(
    schnorrAddr,
    shieldAddress,
    schnorrKeyBytes
  );
  await depositVerifier.waitForDeployment();
  const verifierAddr = await depositVerifier.getAddress();

  // Deploy Deposit Parser
  const Parser = await ethers.getContractFactory("DepositParser");
  const parser = await Parser.deploy();
  await parser.waitForDeployment();
  const parserAddr = await parser.getAddress();

  // Deploy Symmio
  const Symmio = await ethers.getContractFactory("Symmio");
  const symmio = await Symmio.deploy();
  await symmio.waitForDeployment();
  const symmioAddr = await symmio.getAddress();

  // Deploy Executor
  const Executor = await ethers.getContractFactory("DepositExecutor");
  const executor = await Executor.deploy(symmioAddr, verifierAddr, parserAddr);
  await executor.waitForDeployment();
  const executorAddr = await executor.getAddress();

  // Set executor
  const tx = await symmio.setExecutor(executorAddr);
  await tx.wait();
  console.log("Executor set in Symmio");

  console.log("SchnorrVerifier:", schnorrAddr);
  await verifyContract(schnorrAddr);

  console.log("DepositVerifier:", verifierAddr);
  await verifyContract(verifierAddr, [schnorrAddr, shieldAddress, schnorrKeyBytes]);

  console.log("DepositParser:", parserAddr);
  await verifyContract(parserAddr);

  console.log("Symmio:", symmioAddr);
  await verifyContract(symmioAddr);

  console.log("DepositExecutor:", executorAddr);
  await verifyContract(executorAddr, [symmioAddr, verifierAddr, parserAddr]);

}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
