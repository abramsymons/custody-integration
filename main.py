from fastapi import APIRouter, FastAPI, Query
from pydantic import BaseModel

from parse_deposit import DepositTransaction
from verify_deposit import verify_deposit_tx

NUMBER_OF_USERS = 100

router = APIRouter()


@router.get("/users/latest-id")
async def get_latest_user_id() -> dict[str, int]:
    return {"id": NUMBER_OF_USERS}


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
    return {"chain": chain, "id": 0}


class Withdraw(BaseModel):
    chain: str
    tokenContract: str
    amount: str
    destination: str
    user_id: int
    t: int
    id: int


@router.get("/withdraws", response_model=list[Withdraw])
def get_withdraws(
    chain: str = Query(...),
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    return [
        {
            "chain": chain,
            "tokenContract": "0x6f8cbCf0b342f6a997874F8bf1430ADE5138e15a",
            "amount": "5000000",
            "destination": "0x7314b5cb4e67450ef311a1a5e0c79f0d7424072e",
            "user_id": 22,
            "t": 1753369254,
            "id": 0,
        }
    ]


app = FastAPI()
app.include_router(router)
