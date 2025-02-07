from web3 import Web3

sUSD_bytes = "0x7355534400000000000000000000000000000000000000000000000000000000"  # noqa N816
SNX_bytes = "0x534e580000000000000000000000000000000000000000000000000000000000"


def str_to_bytes32(text: str) -> bytes:
    return Web3.to_bytes(hexstr=Web3.to_hex(text=text)).ljust(32, b"\00")
