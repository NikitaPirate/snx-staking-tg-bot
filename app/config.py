from pydantic_settings import BaseSettings

from app.common import Chain


class ChainConfig:
    def __init__(
        self, chain: Chain, api: str, address_resolver_address: str, issuance_ratio: float
    ):
        self.chain = chain
        self.api = api
        self.address_resolver_address: str = address_resolver_address
        self.issuance_ratio: float = issuance_ratio


class Config(BaseSettings, extra="allow"):
    etherscan_key: str
    db_connection: str
    alchemy_key: str

    ethereum_address_resolver_address: str
    optimism_address_resolver_address: str

    ethereum_issuance_ratio: float
    optimism_issuance_ratio: float

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chains: dict[Chain, ChainConfig] = {}

        for chain in Chain.__members__.values():
            self.chains[chain] = ChainConfig(
                chain=chain,
                api=f"https://{chain.alchemy_name}-mainnet.g.alchemy.com/v2/{self.alchemy_key}",
                address_resolver_address=getattr(self, f"{chain.value}_address_resolver_address"),
                issuance_ratio=getattr(self, f"{chain.value}_issuance_ratio"),
            )
