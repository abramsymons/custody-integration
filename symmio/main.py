import sys
import os
import json
import sqlite3
from contextlib import contextmanager
from fastapi import APIRouter, FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from web3 import AsyncHTTPProvider, AsyncWeb3
from eth_account import Account

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from parse_deposit import DepositTransaction, Deposit
from verify_deposit import verify_deposit_tx
from id2address_apt import compute_apt_address

FINALITY_BLOCKS = 1
PRIVATE_KEY = os.environ["PRIVATE_KEY"]
ACCOUNT_ADDRESS = Account.from_key(PRIVATE_KEY).address
DEPLOYMENTS = {
    "SEP": {
        "rpc": "https://ethereum-sepolia-rpc.publicnode.com",
        "withdraw_logger_address": "0x2546042e663eF294bC6893D2615c867a28d38983",
        "deposit_executor_address": "0x1C6f721C0588338Ba7a80B20036F1D5627d46276",
    },
    "POL": {
        "rpc": "https://polygon-bor-rpc.publicnode.com",
        "withdraw_logger_address": "0x2546042e663eF294bC6893D2615c867a28d38983",
        "deposit_executor_address": "0x787FCe8e2Ee89C2015c02ae91D91bECC17e649A5",
    },
    "BASE": {
        "rpc": "https://base.drpc.org",
        "withdraw_logger_address": "0xf893D81CC438dC44c25dD6F22a2422c26C626C9c",
        "deposit_executor_address": "0x9A51E128906bEcbA69201f1DA32f61b92eF8c6Cc",
    }
}

DEPLOYMENT = DEPLOYMENTS["BASE"]
w3 = AsyncWeb3(AsyncHTTPProvider(DEPLOYMENT["rpc"]))

CHAIN2ID = {
    "APT": 2
}

with open("WithdrawLogger.json") as f:
    WITHDRAW_LOGGER_ABI = json.load(f)

with open("DepositExecutor.json") as f:
    DEPOSIT_EXECUTOR_ABI = json.load(f)


router = APIRouter()

DB_PATH = "relayer.db"

def init_db() -> None:
    """Create DB + salts table if missing."""
    con = sqlite3.connect(DB_PATH)
    try:
        con.execute("PRAGMA journal_mode=WAL;")  # better concurrency for reads
        con.execute("""
            CREATE TABLE IF NOT EXISTS salts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL UNIQUE COLLATE NOCASE
            );
        """)
        con.commit()
    finally:
        con.close()

init_db()

@contextmanager
def db():
    con = sqlite3.connect(DB_PATH, timeout=10)
    try:
        yield con
        con.commit()
    finally:
        con.close()

def insert_eth_addresses(addresses: list[str]) -> None:
    """
    Insert unique (case-insensitive) ETH addresses into salts.
    Uses INSERT OR IGNORE so existing rows are left untouched.
    """
    if not addresses:
        return
    normalized = {a.lower() for a in addresses}  # dedupe before hitting the DB
    with db() as con:
        con.executemany(
            "INSERT OR IGNORE INTO salts(address) VALUES (?)",
            [(a,) for a in normalized],
        )

class AddressMapping(BaseModel):
    apt: str
    # in the future you could add: btc: str | None = None, sui: str | None = None, etc.

class AddressesResponse(BaseModel):
    addresses: dict[str, AddressMapping]


@router.post("/vibe/deposit/addresses", response_model=AddressesResponse)
def convert_eth_to_aptos(eth_addresses: list[str]):
    if not eth_addresses:
        raise HTTPException(status_code=400, detail="No Ethereum addresses provided.")

    try:
        result = {
            addr: AddressMapping(apt=compute_apt_address(addr))
            for addr in eth_addresses
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion error: {e}")

    try:
        insert_eth_addresses(eth_addresses)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    return AddressesResponse(addresses=result)


@router.get("/user/id/last")
async def get_last_user_id() -> dict[str, int]:
    try:
        with db() as con:  # uses the db() context manager from earlier
            cur = con.execute("SELECT COUNT(*) FROM salts")
            (count,) = cur.fetchone()
        return {"id": int(count) - 1}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

class User(BaseModel):
    salt: str
    id: int


@router.get("/users", response_model=list[User])
def get_users(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    try:
        with db() as con:  # uses the `db()` context manager from earlier
            cur = con.execute("SELECT id, address FROM salts ORDER BY id")
            rows = cur.fetchall()
        return [User(id=offset + i, salt=row[1]) for i, row in enumerate(rows[offset:offset+limit])]
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.post("/deposit")
async def deposit(deposit_txs: list[str]) -> dict[str, bool]:
    deposit_txs = [tx.encode("latin-1") for tx in deposit_txs]
    for deposit_tx in deposit_txs:
        if verify_deposit_tx(deposit_tx):
            parsed_tx = DepositTransaction.from_tx(deposit_tx)
            print(parsed_tx)
            chain = parsed_tx.chain
            assert chain == "APT", f"Invalid deposit chain {chain}"
            contract_address = DEPLOYMENT["deposit_executor_address"]
            executor = w3.eth.contract(
                address=contract_address, abi=DEPOSIT_EXECUTOR_ABI
            )

            tx = executor.functions.executeDeposit(deposit_tx)
            gas_estimate = await tx.estimate_gas({"from": ACCOUNT_ADDRESS})
            gas_price = await w3.eth.gas_price
            tx_dict = await tx.build_transaction(
                {
                    "from": ACCOUNT_ADDRESS,
                    "nonce": await w3.eth.get_transaction_count(ACCOUNT_ADDRESS),
                    "gas": gas_estimate,
                    "gasPrice": gas_price * 3,
                }
            )

            signed_tx = w3.eth.account.sign_transaction(
                tx_dict, private_key=PRIVATE_KEY
            )
            tx_hash = await w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            print(f"Transaction sent: {tx_hash.hex()}")
            receipt = await w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"Transaction mined in block {receipt.blockNumber}")

        else:
            return {"success": False}

    return {"success": True}


@router.get("/withdraw/id/last")
async def get_last_withdraw_id(chain: str = Query(...)) -> dict[str, int | str]:
    if chain not in CHAIN2ID:
        raise HTTPException(status_code=400, detail="Unsupported chain")

    contract_address = DEPLOYMENT["withdraw_logger_address"]
    withdrawal_chain_id = CHAIN2ID[chain]
    contract = w3.eth.contract(
        address=contract_address, abi=WITHDRAW_LOGGER_ABI
    )
    current_block = await w3.eth.block_number
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
    salt: str
    t: int
    id: int


@router.get("/withdraws", response_model=list[Withdraw])
async def get_withdraws(
    chain: str = Query(...),
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    if chain not in CHAIN2ID:
        raise HTTPException(status_code=400, detail="Unsupported chain")

    contract_address = DEPLOYMENT["withdraw_logger_address"]
    withdrawal_chain_id = CHAIN2ID[chain]
    contract = w3.eth.contract(
        address=contract_address, abi=WITHDRAW_LOGGER_ABI
    )
    current_block = await w3.eth.block_number
    block_number = current_block - FINALITY_BLOCKS

    block = await w3.eth.get_block(block_number)
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
            "salt": withdrawal[4],
            "t": timestamp,
        }
        for withdrawal in withdrawals
    ]


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # allow all origins (dev only)
    allow_credentials=False,      # must be False when allow_origins=["*"]
    allow_methods=["*"],          # or ["GET","POST","PUT","DELETE","OPTIONS"]
    allow_headers=["*"],          # or specific headers
)
app.include_router(router)
