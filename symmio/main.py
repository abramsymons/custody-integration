import sys
import os
import json
from fastapi import APIRouter, FastAPI, Query, HTTPException
from pydantic import BaseModel

from web3 import AsyncHTTPProvider, AsyncWeb3
from eth_account import Account

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from parse_deposit import DepositTransaction, Deposit
from verify_deposit import verify_deposit_tx

FINALITY_BLOCKS = 1
NUMBER_OF_USERS = 100
PRIVATE_KEY = os.environ["PRIVATE_KEY"]
ACCOUNT_ADDRESS = Account.from_key(PRIVATE_KEY).address
SUPPORTED_CHAINS = {
    "SEP": {
        "rpc": "https://ethereum-sepolia-rpc.publicnode.com",
        "withdraw_logger_address": "0x2546042e663eF294bC6893D2615c867a28d38983",
        "deposit_executor_address": "0x1C6f721C0588338Ba7a80B20036F1D5627d46276",
        "chain_id": 11155111,
    }
}

with open("WithdrawLogger.json") as f:
    WITHDRAW_LOGGER_ABI = json.load(f)

with open("DepositExecutor.json") as f:
    DEPOSIT_EXECUTOR_ABI = json.load(f)

router = APIRouter()


def client(chain: str) -> AsyncWeb3:
    return AsyncWeb3(AsyncHTTPProvider(SUPPORTED_CHAINS[chain]["rpc"]))


@router.get("/users/latest-id")
async def get_latest_user_id() -> dict[str, int]:
    return {"id": NUMBER_OF_USERS}


@router.post("/deposit")
async def deposit(deposit_txs: list[str]) -> dict[str, bool]:
    deposit_txs = [tx.encode("latin-1") for tx in deposit_txs]
    for deposit_tx in deposit_txs:
        if verify_deposit_tx(deposit_tx):
            parsed_tx = DepositTransaction.from_tx(deposit_tx)
            print(parsed_tx)
            chain = parsed_tx.chain
            contract_address = SUPPORTED_CHAINS[chain]["deposit_executor_address"]
            executor = client(chain).eth.contract(
                address=contract_address, abi=DEPOSIT_EXECUTOR_ABI
            )

            tx = executor.functions.executeDeposit(deposit_tx)
            gas_estimate = await tx.estimate_gas({'from': ACCOUNT_ADDRESS})
            w3 = client(chain)
            gas_price = await w3.eth.gas_price
            tx_dict = await tx.build_transaction({
                "from": ACCOUNT_ADDRESS,
                "nonce": await w3.eth.get_transaction_count(ACCOUNT_ADDRESS),
                "gas": gas_estimate,
                "gasPrice": gas_price * 3,
            })

            signed_tx = w3.eth.account.sign_transaction(tx_dict, private_key=PRIVATE_KEY)
            tx_hash = await w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            print(f"Transaction sent: {tx_hash.hex()}")
            receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"Transaction mined in block {receipt.blockNumber}")

        else:
            return {"success": False}

    return {"success": True}


@router.get("/withdraw/id/last")
async def get_last_withdraw_id(chain: str = Query(...)) -> dict[str, int | str]:
    if chain not in SUPPORTED_CHAINS:
        raise HTTPException(status_code=400, detail="Unsupported chain")

    contract_address = SUPPORTED_CHAINS[chain]["withdraw_logger_address"]
    withdrawal_chain_id = SUPPORTED_CHAINS[chain]["chain_id"]
    contract = client(chain).eth.contract(
        address=contract_address, abi=WITHDRAW_LOGGER_ABI
    )
    current_block = await client(chain).eth.block_number
    block_number = current_block - FINALITY_BLOCKS
    count = await contract.functions.getWithdrawCount(withdrawal_chain_id).call(
        block_identifier=block_number
    )
    return {"chain": chain, "id": count}


class Withdraw(BaseModel):
    chain: str
    tokenContract: str
    amount: str
    destination: str
    user_id: int
    t: int
    id: int


@router.get("/withdraws", response_model=list[Withdraw])
async def get_withdraws(
    chain: str = Query(...),
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    if chain not in SUPPORTED_CHAINS:
        raise HTTPException(status_code=400, detail="Unsupported chain")

    contract_address = SUPPORTED_CHAINS[chain]["withdraw_logger_address"]
    withdrawal_chain_id = SUPPORTED_CHAINS[chain]["chain_id"]
    contract = client(chain).eth.contract(
        address=contract_address, abi=WITHDRAW_LOGGER_ABI
    )
    current_block = await client(chain).eth.block_number
    block_number = current_block - FINALITY_BLOCKS

    block = await client(chain).eth.get_block(block_number)
    timestamp = block["timestamp"]

    withdrawals = await contract.functions.getWithdrawals(
        withdrawal_chain_id, offset, offset + limit
    ).call(block_identifier=block_number)

    return [
        {
            "chain": chain,
            "id": withdrawal[0],
            "tokenContract": withdrawal[1],
            "amount": str(withdrawal[2]),
            "destination": withdrawal[3],
            "user_id": int(withdrawal[4], 16),
            "t": timestamp,
            
        } for withdrawal in withdrawals
    ]


app = FastAPI()
app.include_router(router)
