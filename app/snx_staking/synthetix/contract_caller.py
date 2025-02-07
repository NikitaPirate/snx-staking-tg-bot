import asyncio
from asyncio import Semaphore
from typing import Any

from eth_typing import Address
from tenacity import retry, stop_after_delay, wait_exponential
from web3.contract.async_contract import AsyncContractFunction
from web3.eth.async_eth import AsyncContract
from web3.types import BlockIdentifier

from app.snx_staking.synthetix.constants import ContractName
from app.snx_staking.synthetix.contract_manager import ContractManager
from app.snx_staking.synthetix.utils import SNX_bytes


class ContractCaller:
    def __init__(self, contract_manager: ContractManager, semaphore: asyncio.Semaphore):
        self._contract_manager: ContractManager = contract_manager
        self._semaphore: Semaphore = semaphore

    @retry(wait=wait_exponential(multiplier=1, max=60), stop=stop_after_delay(6 * 60 * 60))
    async def _call_contract(
        self,
        contract_name: str,
        function_name: str,
        block_identifier: BlockIdentifier,
        *args: Any,
        **kwargs: Any,
    ) -> Any:  # noqa: ANN401
        contract: AsyncContract = self._contract_manager.get_contract(contract_name)
        function: AsyncContractFunction = getattr(contract.functions, function_name)(
            *args, **kwargs
        )
        async with self._semaphore:
            return await function.call(block_identifier=block_identifier)

    # SYNTHETIX
    async def collateral(
        self, address: Address, block_identifier: BlockIdentifier = "latest"
    ) -> int:
        return await self._call_contract(
            ContractName.SYNTHETIX, "collateral", block_identifier, address
        )

    # EXCHANGE_RATES
    async def synthetix_price(self, block_identifier: BlockIdentifier = "latest") -> int:
        res = await self._call_contract(
            ContractName.EXCHANGE_RATES, "rateAndInvalid", block_identifier, SNX_bytes
        )
        return res[0]

    # SYNTHETIX_DEBT_SHARE
    async def debt_share_of(
        self, address: Address, block_identifier: BlockIdentifier = "latest"
    ) -> int:
        return await self._call_contract(
            ContractName.SYNTHETIX_DEBT_SHARE, "balanceOf", block_identifier, address
        )

    # AGGREGATOR_DEBT_RATIO
    async def debt_share_price(self, block_identifier: BlockIdentifier = "latest") -> int:
        return await self._call_contract(
            ContractName.AGGREGATOR_DEBT_RATIO, "latestAnswer", block_identifier
        )

    # FEE POOL
    async def recent_fee_periods(
        self, index: int = 0, block_identifier: BlockIdentifier = "latest"
    ) -> tuple:
        return await self._call_contract(
            ContractName.PROXY_FEE_POOL, "recentFeePeriods", block_identifier, index
        )

    async def fees_available(
        self, address: Address, block_identifier: BlockIdentifier = "latest"
    ) -> int:
        return await self._call_contract(
            ContractName.PROXY_FEE_POOL, "feesAvailable", block_identifier, address
        )

    async def liquidation_deadline_for_account(
        self, address: Address, block_identifier: BlockIdentifier = "latest"
    ) -> int:
        return await self._call_contract(
            ContractName.LIQUIDATOR, "getLiquidationDeadlineForAccount", block_identifier, address
        )
