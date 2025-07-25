from decimal import Decimal
from struct import calcsize, unpack

from eth_typing import ChecksumAddress
from eth_utils.address import to_checksum_address
from pydantic import BaseModel


def chunkify(lst, n_chunks):
    for i in range(0, len(lst), n_chunks):
        yield lst[i : i + n_chunks]


class Deposit(BaseModel):
    tx_hash: str
    chain: str
    token_contract: ChecksumAddress
    amount: Decimal
    decimal: int
    time: int
    user_id: int
    vout: int

    @property
    def token_name(self):
        return get_token_name(self.chain, self.token_contract)


class DepositTransaction(BaseModel):
    version: int
    operation: str
    chain: str
    deposits: list[Deposit]

    @classmethod
    def from_tx(cls, tx: bytes) -> "DepositTransaction":
        header_format = ">B B 3s H"
        header_size = calcsize(header_format)
        version, operation, chain, count = unpack(header_format, tx[:header_size])
        chain = chain.upper().decode()

        deposit_format = ">32s 20s 32s B I Q B"
        deposit_size = calcsize(deposit_format)
        raw_deposits = list(
            chunkify(tx[header_size : header_size + deposit_size * count], deposit_size)
        )

        deposits = []

        for chunk in raw_deposits:
            tx_hash, token_contract, amount, decimal, t, user_id, vout = unpack(
                deposit_format, chunk[:deposit_size]
            )
            amount = int.from_bytes(amount, byteorder="big")

            amount = Decimal(str(amount))
            amount /= 10 ** Decimal(decimal)

            deposits.append(
                Deposit(
                    tx_hash=tx_hash.hex(),
                    chain=chain,
                    token_contract=to_checksum_address(token_contract.hex()),
                    amount=amount,
                    decimal=decimal,
                    time=t,
                    user_id=user_id,
                    vout=vout,
                )
            )

        return DepositTransaction(
            version=version,
            operation=chr(operation),
            chain=chain,
            deposits=deposits,
        )


if __name__ == "__main__":
    tx = b"\x01dsep\x00\x01\xd6\x8aA\xdf\xae\xefsh\xb2\x8b\x82\xd7\xb1*\x17}?Jk\x1e\t\xb1\xba\xfdg%&V\xa5\xa1\x982o\x8c\xbc\xf0\xb3B\xf6\xa9\x97\x87O\x8b\xf1C\n\xdeQ8\xe1Z\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x06\x14e\x80\x06h\x82\x06\xd0\x00\x00\x00\x00\x00\x00\x00\x16\x00 \xf5\nX\xfc\xe6\xf7a\x9d\x9fx\n\x8b\xeb4\xc7</\xe9\xb5\x8e\x96\xa8s\x03C\x99|\xa4\xe6\xcce\x83],\xe3\xf85\xea\x9a\xd4\x89a\xf9\x15\xad/#(cA\xa2\x94\xd3\xa1\xbe2\x9c\x80e\x1dG\xd4Y\x08\xbcl\xde\x065\x1e\xe8\xb5?\xd7\x19B\xba\x17\x81-\x15\xae\x84\xe4\xa7\xcdPy\xef\x13\xf3XI\xe3\xdci\xfe\x83\x0bc\xc6,f\xf5\xf0\x9f1J\xa6\x04\x8cyQ\x9c\xba?\x04\x16q\xc3\x9c6\xc6\xa5\xeb.\xf2\x1c"
    print(DepositTransaction.from_tx(tx))
