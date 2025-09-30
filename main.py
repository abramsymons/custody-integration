import json

from fastapi import APIRouter, FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from parse_deposit import DepositTransaction
from verify_deposit import verify_deposit_tx
from id2address_apt import compute_apt_address

NUMBER_OF_USERS = 100

router = APIRouter()


@router.get("/user/count")
async def get_user_count() -> dict[str, int]:
    return {"count": NUMBER_OF_USERS}


class User(BaseModel):
    salt: int
    id: int


@router.get("/users", response_model=list[User])
def get_users(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    return [
        {
            "salt": i + 0x5FCEB18CF62BF791D7AA0931D3159F95650A0061 + 1000,
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


WITHDRAWALS = [
    {
        "chain": "SEP",
        "tokenContract": "0x6f8cbCf0b342f6a997874F8bf1430ADE5138e15a",
        "amount": "2000000",
        "destination": "0x7314b5cb4e67450ef311a1a5e0c79f0d7424072e",
        "user_id": 5 + 0x5FCEB18CF62BF791D7AA0931D3159F95650A0061 + 1000,
        "t": 1753369254,
        "id": 0,
    },
    {
        "chain": "SEP",
        "tokenContract": "0x6f8cbCf0b342f6a997874F8bf1430ADE5138e15a",
        "amount": "1500000",
        "destination": "0x7314b5cb4e67450ef311a1a5e0c79f0d7424072e",
        "user_id": 5 + 0x5FCEB18CF62BF791D7AA0931D3159F95650A0061 + 1000,
        "t": 1753369255,
        "id": 1,
    },
]

WITHDRAWALS_MAP = {withdrawal["id"]: withdrawal for withdrawal in WITHDRAWALS}


@router.get("/withdraw/count")
def get_withdraw_count(chain: str = Query(...)) -> dict[str, int | str]:
    if chain != "SEP":
        raise HTTPException(status_code=400, detail="Invalid chain.")

    return {"chain": chain, "count": len(WITHDRAWALS)}


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
    if chain != "SEP":
        raise HTTPException(status_code=400, detail="Invalid chain.")

    return WITHDRAWALS


@router.get("/withdraw/id", response_model=list[Withdraw])
def get_withdraw_by_ids(
    chain: str = Query(...),
    ids: str = Query(..., description="JSON.dumps of list of ids"),
):
    if chain != "SEP":
        raise HTTPException(status_code=400, detail="Invalid chain.")

    try:
        id_list: list[int] = json.loads(ids)
        if not isinstance(id_list, list) or not all(
            isinstance(i, int) for i in id_list
        ):
            raise ValueError("ids must be a JSON list of integers.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid ids format: {e}")

    withdrawals = []
    for wid in id_list:
        if wid in WITHDRAWALS_MAP:
            withdrawals.append(WITHDRAWALS_MAP[wid])

    return withdrawals


class AddressMapping(BaseModel):
    apt: str
    # in the future you could add: btc: str | None = None, sui: str | None = None, etc.


class AddressesResponse(BaseModel):
    addresses: dict[str, AddressMapping]


@router.post("/deposit/addresses", response_model=AddressesResponse)
def convert_eth_to_aptos(eth_addresses: list[str]):
    if not eth_addresses:
        raise HTTPException(status_code=400, detail="No Ethereum addresses provided.")

    result: dict[str, AddressMapping] = {}

    try:
        for addr in eth_addresses:
            apt_addr = compute_apt_address(addr)
            result[addr] = AddressMapping(apt=apt_addr)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion error: {e}")

    return AddressesResponse(addresses=result)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins (dev only)
    allow_credentials=False,  # must be False when allow_origins=["*"]
    allow_methods=["*"],  # or ["GET","POST","PUT","DELETE","OPTIONS"]
    allow_headers=["*"],  # or specific headers
)
app.include_router(router)
