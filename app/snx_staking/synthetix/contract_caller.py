from eth_typing import Address
from web3.types import BlockIdentifier

from app.snx_staking.synthetix.constants import ContractName
from app.snx_staking.synthetix.contract_manager import ContractManager
from app.snx_staking.synthetix.utils import RawContractCall, SNX_bytes


class ContractCaller:
    def __init__(self, contract_manager: ContractManager, raw_contract_call: RawContractCall):
        self._contract_manager: ContractManager = contract_manager
        self._raw_contract_call: RawContractCall = raw_contract_call

    # SYNTHETIX
    async def collateral(
        self, address: Address, block_identifier: BlockIdentifier = "latest"
    ) -> int:
        return await self._raw_contract_call(
            self._contract_manager.get_contract(ContractName.SYNTHETIX),
            "collateral",
            block_identifier,
            address,
        )

    # EXCHANGE_RATES
    async def synthetix_price(self, block_identifier: BlockIdentifier = "latest") -> int:
        res = await self._raw_contract_call(
            self._contract_manager.get_contract(ContractName.EXCHANGE_RATES),
            "rateAndInvalid",
            block_identifier,
            SNX_bytes,
        )
        return res[0]

    # SYNTHETIX_DEBT_SHARE
    async def debt_share_of(
        self, address: Address, block_identifier: BlockIdentifier = "latest"
    ) -> int:
        return await self._raw_contract_call(
            self._contract_manager.get_contract(ContractName.SYNTHETIX_DEBT_SHARE),
            "balanceOf",
            block_identifier,
            address,
        )

    # AGGREGATOR_DEBT_RATIO
    async def debt_share_price(self, block_identifier: BlockIdentifier = "latest") -> int:
        return await self._raw_contract_call(
            self._contract_manager.get_contract(ContractName.AGGREGATOR_DEBT_RATIO),
            "latestAnswer",
            block_identifier,
        )

    # FEE POOL
    async def recent_fee_periods(
        self, index: int = 0, block_identifier: BlockIdentifier = "latest"
    ) -> tuple:
        return await self._raw_contract_call(
            self._contract_manager.get_contract(ContractName.PROXY_FEE_POOL),
            "recentFeePeriods",
            block_identifier,
            index,
        )

    async def fees_available(
        self, address: Address, block_identifier: BlockIdentifier = "latest"
    ) -> int:
        return await self._raw_contract_call(
            self._contract_manager.get_contract(ContractName.PROXY_FEE_POOL),
            "feesAvailable",
            block_identifier,
            address,
        )

    async def liquidation_deadline_for_account(
        self, address: Address, block_identifier: BlockIdentifier = "latest"
    ) -> int:
        return await self._raw_contract_call(
            self._contract_manager.get_contract(ContractName.LIQUIDATOR),
            "getLiquidationDeadlineForAccount",
            block_identifier,
            address,
        )
