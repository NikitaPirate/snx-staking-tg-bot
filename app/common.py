from dataclasses import dataclass
from enum import StrEnum
from typing import Self


class Chain(StrEnum):
    optimism = "optimism"
    ethereum = "ethereum"

    @property
    def chain_id(self) -> int:
        return {
            Chain.optimism: 10,
            Chain.ethereum: 1,
        }[self]

    @property
    def alchemy_name(self) -> str:
        return {
            Chain.optimism: "opt",
            Chain.ethereum: "eth",
        }[self]

    @classmethod
    def from_string(cls, value: str) -> Self:
        """returns None if no match"""
        value = value.lower()
        if value in ("e", "eth", "ethereum"):
            return cls.ethereum
        elif value in ("o", "op", "optimism"):
            return cls.optimism


@dataclass
class SNXData:
    chain: Chain

    snx_price: int = 0
    sds_price: int = 0
    period_start: int = 0
    period_end: int = 0

    snx_updated: bool = False
    sds_updated: bool = False
    period_updated: bool = False
