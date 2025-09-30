import { ethers, run, network } from "hardhat";

async function main() {
  const [deployer] = await ethers.getSigners();

  console.log("🚀 Deploying contract with account:", deployer.address);
  const balance = await deployer.provider?.getBalance(deployer.address);
  console.log("💰 Balance:", ethers.formatEther(balance || 0), "ETH");

  // Deploy contract
  const WithdrawLogger = await ethers.getContractFactory("WithdrawLogger");
  const logger = await WithdrawLogger.deploy();
  await logger.waitForDeployment();

  const loggerAddress = await logger.getAddress();
  console.log("✅ WithdrawLogger deployed to:", loggerAddress);

  // Skip verification on Hardhat local network
  if (network.name === "hardhat" || network.name === "localhost") {
    console.log("ℹ️ Local network detected, skipping Etherscan verification.");
    return;
  }

  // Wait a bit to ensure Etherscan has indexed the contract
  console.log("⏳ Waiting for Etherscan to index contract...");
  await new Promise((resolve) => setTimeout(resolve, 10000)); // wait 10s

  try {
    console.log("🔍 Verifying contract on Etherscan...");
    await run("verify:verify", {
      address: loggerAddress,
      constructorArguments: [], // none for this contract
    });
    console.log("✅ Verification successful!");
  } catch (err: any) {
    if (err.message.toLowerCase().includes("already verified")) {
      console.log("✅ Contract already verified!");
    } else {
      console.error("❌ Verification failed:", err);
    }
  }
}

main().catch((error) => {
  console.error("❌ Deployment script failed:", error);
  process.exitCode = 1;
});
