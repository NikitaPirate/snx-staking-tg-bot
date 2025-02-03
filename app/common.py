from enum import StrEnum


class Chain(StrEnum):
    optimism = "optimism"
    ethereum = "ethereum"

    @classmethod
    def from_string(cls, value: str):
        """returns None if no match"""
        value = value.lower()
        if value in ("e", "eth", "ethereum"):
            return cls.ethereum
        elif value in ("o", "op", "optimism"):
            return cls.optimism


class SNXData:
    chain: Chain

    snx_price: int = 0
    sds_price: int = 0
    period_start: int = 0
    period_end: int = 0

    snx_updated: bool = False
    sds_updated: bool = False
