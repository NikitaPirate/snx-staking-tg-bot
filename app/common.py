from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from app.telegram_bot.utils import remaining_time_until


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
    issuance_ratio: int

    snx_price: int = 0
    sds_price: int = 0
    period_start: int = 0
    period_end: int = 0

    snx_updated: bool = False
    sds_updated: bool = False
    period_updated: bool = False


class SNXMultiChainData:
    def __init__(self):
        self._data: dict[Chain, SNXData] = {
            Chain.ethereum: SNXData(chain=Chain.ethereum),
            Chain.optimism: SNXData(chain=Chain.optimism),
        }

    def __getitem__(self, chain: Chain) -> SNXData:
        return self._data[chain]

    # Texts for bot
    def format_period_end_times(self) -> str:
        text = ""
        for chain, data in self._data.items():
            remaining_time = remaining_time_until(data.period_end)
            text += f"{chain}: {remaining_time}\n"
        return text

    def format_snx_price(self) -> str:
        snx_prices = [data.snx_price for data in self._data.values() if data.snx_price != 0]
        if not snx_prices:
            return "loading"

        avg_price = sum(snx_prices) / len(snx_prices)
        return str(round(avg_price / 10**18, 2))
