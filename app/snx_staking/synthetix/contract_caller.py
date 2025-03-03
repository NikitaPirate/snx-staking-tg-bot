from eth_typing import Address
from web3.types import BlockIdentifier

from app.snx_staking.synthetix.constants import ContractName
from app.snx_staking.synthetix.contract_manager import ContractManager
from app.snx_staking.synthetix.utils import SNX_bytes


class ContractCaller:
    def __init__(self, contract_manager: ContractManager):
        self._contract_manager: ContractManager = contract_manager

    # SYNTHETIX
    async def collateral(
        self, address: Address, block_identifier: BlockIdentifier = "latest"
    ) -> int:
        contract = self._contract_manager.get_contract(ContractName.SYNTHETIX)
        return await contract.functions.collateral(address).call(block_identifier=block_identifier)

    # EXCHANGE_RATES
    async def synthetix_price(self, block_identifier: BlockIdentifier = "latest") -> int:
        contract = self._contract_manager.get_contract(ContractName.EXCHANGE_RATES)
        res = await contract.functions.rateAndInvalid(SNX_bytes).call(
            block_identifier=block_identifier
        )
        return res[0]

    # SYNTHETIX_DEBT_SHARE
    async def debt_share_of(
        self, address: Address, block_identifier: BlockIdentifier = "latest"
    ) -> int:
        contract = self._contract_manager.get_contract(ContractName.SYNTHETIX_DEBT_SHARE)
        return await contract.functions.balanceOf(address).call(block_identifier=block_identifier)

    # AGGREGATOR_DEBT_RATIO
    async def debt_share_price(self, block_identifier: BlockIdentifier = "latest") -> int:
        contract = self._contract_manager.get_contract(ContractName.AGGREGATOR_DEBT_RATIO)
        return await contract.functions.latestAnswer().call(block_identifier=block_identifier)

    # FEE POOL
    async def recent_fee_periods(
        self, index: int = 0, block_identifier: BlockIdentifier = "latest"
    ) -> tuple:
        contract = self._contract_manager.get_contract(ContractName.PROXY_FEE_POOL)
        return await contract.functions.recentFeePeriods(index).call(
            block_identifier=block_identifier
        )

    async def fees_available(
        self, address: Address, block_identifier: BlockIdentifier = "latest"
    ) -> int:
        contract = self._contract_manager.get_contract(ContractName.PROXY_FEE_POOL)
        return await contract.functions.feesAvailable(address).call(
            block_identifier=block_identifier
        )

    async def liquidation_deadline_for_account(
        self, address: Address, block_identifier: BlockIdentifier = "latest"
    ) -> int:
        contract = self._contract_manager.get_contract(ContractName.LIQUIDATOR)
        return await contract.functions.getLiquidationDeadlineForAccount(address).call(
            block_identifier=block_identifier
        )
