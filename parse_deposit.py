from decimal import Decimal
from struct import calcsize, unpack

from pydantic import BaseModel


class Deposit(BaseModel):
    tx_hash: str
    chain: str
    token_contract: str
    amount: Decimal
    decimal: int
    time: int
    salt: str
    vout: int


class DepositTransaction(BaseModel):
    version: int
    operation: str
    chain: str
    deposits: list[Deposit]

    @classmethod
    def from_tx(cls, tx: bytes) -> "DepositTransaction":
        header_format = ">B B 3s B B H"
        header_size = calcsize(header_format)
        if len(tx) < header_size:
            raise ValueError("tx too short for header")

        version, operation, chain_bytes, tx_hash_len, token_contract_len, count = unpack(header_format, tx[:header_size])
        chain = chain_bytes.upper().decode()

        prefix_fmt = f">{tx_hash_len}s{token_contract_len}s32sBI"
        prefix_size = calcsize(prefix_fmt)

        offset = header_size
        deposits: list[Deposit] = []

        for _ in range(count):
            # fixed prefix
            if offset + prefix_size > len(tx):
                raise ValueError("tx too short for deposit prefix")
            tx_hash, token_contract, amount_bytes, decimal, t = unpack(
                prefix_fmt, tx[offset : offset + prefix_size]
            )
            offset += prefix_size

            # salt_len
            if offset + 1 > len(tx):
                raise ValueError("tx too short for salt_len")
            salt_len = tx[offset]
            offset += 1

            # salt (big-endian, variable length)
            if offset + salt_len > len(tx):
                raise ValueError("tx too short for salt bytes")
            salt_bytes = tx[offset : offset + salt_len]
            offset += salt_len
            salt = salt_bytes.hex()

            # vout
            if offset + 1 > len(tx):
                raise ValueError("tx too short for vout")
            vout = tx[offset]
            offset += 1

            # amount -> Decimal with scaling by decimal places
            amount_int = int.from_bytes(amount_bytes, "big")
            amount = Decimal(amount_int) / (Decimal(10) ** Decimal(decimal))

            deposits.append(
                Deposit(
                    tx_hash=tx_hash.hex(),
                    chain=chain,
                    token_contract="0x" + token_contract.hex(),
                    amount=amount,
                    decimal=decimal,
                    time=t,
                    salt=salt,
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
    tx = b'\x01dsep\x00\x01\xcdC\xb5\xa8L\xb3\x1a\xf9]\xa4\xaf\xb1\x15\x94\xe13\xccU\x02\x82\xb9\x9eX2\xecs\xa4\xd8S\x8fQQo\x8c\xbc\xf0\xb3B\xf6\xa9\x97\x87O\x8b\xf1C\n\xdeQ8\xe1Z\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01^\xf3\xc0\x06h\xb9\xc6M\x14_\xce\xb1\x8c\xf6+\xf7\x91\xd7\xaa\t1\xd3\x15\x9f\x95e\n\x04L\x00\x00\x1f8\x86<+Vg\xbc\xe9\xe1.\xbb\xbaA\x06\x97\x94\xe1@\x9b6\x95\xb4\xc1\xbf\xaf0\xa7\xc8\x97\xa3<")\xff\xda\x95\x08\x1aw\xe9 \xebI\xeb\xfa\x1a\xdd*0\xd7\xf0w\xd3\xd9PL\x99\xef\x01m\x1a\xcf\xcd\x0cs.\xef\xad\x89\\\x12\xae4N\xd0\xc1+\x83\xaa\xe8\xdb\x06#\xf7\x9c-\xf4\xd5\x0e\x02\x97\xce\xeb\xc8A"\xd7\xe5\xe1\xd0\xef\x99\x893\xcc\xd6\xee\xbfL\xc1=L\x08#{EH\x99)\xaf\x88\xcc\xaf\n\x01U\x1c'
    print(DepositTransaction.from_tx(tx))
