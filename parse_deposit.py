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
    tx = b'\x01dapt  \x00\x01\xb1.\xa2\xbd\x1b\x83\xa1\xdcH\x1e\x18pz\xd0\xcfP"P\x1fP@\xb0\xbcj\xb6XBX\x8e\xfd\x0e\x0b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x05\xf5\xe1\x00\x08h\xbcEd\x14_\xce\xb1\x8c\xf6+\xf7\x91\xd7\xaa\t1\xd3\x15\x9f\x95e\n\x04\\\x00\x85A\x8c\x96\xc2:\x89\xbct\x06\xcca&U\x0f\xb9Pq\x1a\xbe8X\x99\x00\xdd]\xcaF\xc8cI5\xb6\xc1\xe0\xe3Oo\xc1\xa5\x7f\xf3\xa8c\x0f}\xbd{!\xd8\xe6W\x0e=\xc4\xf4\xd27/\x00\xbd01>\xfd\xb7\x10\xcb\x89+\x96z\xacj?`\x89\xd6\xe6\xbe\xf5\x8a\xe7\x93\x8byR\xb2\xfa@\x16\xa3\x01c?\x00RG\xcdh\xa3 \x14\x10\x9e\xed\xda\x96\x1d\xf8op\xd2\x83\x9b\x8a\xca\xbcW\xd0\x81\xf3]R\x11;\xf6\xd1\x1c'
    print(DepositTransaction.from_tx(tx))
