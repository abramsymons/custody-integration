from fastapi import APIRouter, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from parse_deposit import DepositTransaction
from verify_deposit import verify_deposit_tx

NUMBER_OF_USERS = 100

router = APIRouter()


@router.get("/user/id/last")
async def get_last_user_id() -> dict[str, int]:
    return {"id": NUMBER_OF_USERS}


class User(BaseModel):
    salt: str
    id: int


@router.get("/users", response_model=list[User])
def get_users(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    return [
        {
            "salt": hex(i + 0x5fCeb18CF62bF791d7Aa0931D3159f95650A0061 + 1000), # This can be any hex str specified by the app
            "id": i,
        }
        for i in range(offset, limit + offset)
    ]


@router.post("/deposit")
async def deposit(deposit_txs: list[str]) -> dict[str, bool]:
    deposit_txs = [tx.encode("latin-1") for tx in deposit_txs]
    for tx in deposit_txs:
        if verify_deposit_tx(tx):
            parsed_tx = DepositTransaction.from_tx(tx)
            for deposit in parsed_tx.deposits:
                ##############################
                #  process deposit txs here  #
                ##############################
                print(deposit)

    return {"success": True}


@router.get("/withdraw/id/last")
def get_last_withdraw_id(chain: str = Query(...)) -> dict[str, int | str]:
    return {"chain": chain, "id": 1}


class Withdraw(BaseModel):
    chain: str
    tokenContract: str
    amount: str
    destination: str
    salt: str
    t: int
    id: int


@router.get("/withdraws", response_model=list[Withdraw])
def get_withdraws(
    chain: str = Query(...),
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    if chain != "SEP":
        return []
    return [
        {
            "chain": chain,
            "tokenContract": "0x6f8cbCf0b342f6a997874F8bf1430ADE5138e15a",
            "amount": "2000000",
            "destination": "0x7314b5cb4e67450ef311a1a5e0c79f0d7424072e",
            "salt": hex(5 + 0x5fCeb18CF62bF791d7Aa0931D3159f95650A0061 + 1000),
            "t": 1753369254,
            "id": 0,
        }, {
            "chain": chain,
            "tokenContract": "0x6f8cbCf0b342f6a997874F8bf1430ADE5138e15a",
            "amount": "1500000",
            "destination": "0x7314b5cb4e67450ef311a1a5e0c79f0d7424072e",
            "salt": hex(5 + 0x5fCeb18CF62bF791d7Aa0931D3159f95650A0061 + 1000),
            "t": 1753369255,
            "id": 1,
        }
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
