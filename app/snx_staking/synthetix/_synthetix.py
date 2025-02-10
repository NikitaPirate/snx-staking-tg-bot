import asyncio
from typing import NamedTuple

from eth_typing import AnyAddress
from web3 import AsyncHTTPProvider, AsyncWeb3
from web3.types import BlockIdentifier

from app.common import Chain
from app.config import ChainConfig
from app.snx_staking.synthetix.constants import ContractName, contract_to_events
from app.snx_staking.synthetix.contract_caller import ContractCaller
from app.snx_staking.synthetix.contract_manager import ContractManager
from app.snx_staking.synthetix.utils import create_raw_contract_call


class AddressData(NamedTuple):
    collateral: int
    debt_share: int
    fees_available: tuple[int]
    liquidation_deadline: int


class Synthetix:
    def __init__(
        self,
        chain: Chain,
        web3: AsyncWeb3,
        contract_manager: ContractManager,
        contract_caller: ContractCaller,
    ):
        self.chain = chain
        self._web3: AsyncWeb3 = web3
        self._contract_manager: ContractManager = contract_manager
        self._contract_caller: ContractCaller = contract_caller

    @property
    def vesting_contract_address(self) -> AnyAddress:
        return self._contract_manager.get_contract(ContractName.REWARD_ESCROW_V2).address

    # CONTRACTS MANAGEMENT
    async def install_contracts(self):
        await self._contract_manager.install_contracts()

    async def check_contracts_updates(self) -> bool:
        return await self._contract_manager.check_contracts_updates()

    # WEB3 CALL
    async def get_block_num(self) -> int:
        return await self._web3.eth.block_number

    # CONTRACT CALL
    async def get_synthetix_prices(self) -> tuple:
        t_snx_price = asyncio.create_task(self._contract_caller.synthetix_price())
        t_sds_price = asyncio.create_task(self._contract_caller.debt_share_price())
        return await asyncio.gather(t_snx_price, t_sds_price)

    async def get_period_data(self) -> tuple:
        return await self._contract_caller.recent_fee_periods()

    async def load_address_data(
        self, address: AnyAddress, block_identifier: BlockIdentifier
    ) -> AddressData:
        return AddressData(
            *await asyncio.gather(
                self._contract_caller.collateral(address, block_identifier=block_identifier),
                self._contract_caller.debt_share_of(address, block_identifier=block_identifier),
                self._contract_caller.fees_available(address, block_identifier=block_identifier),
                self._contract_caller.liquidation_deadline_for_account(
                    address, block_identifier=block_identifier
                ),
            )
        )

    # EVENTS
    async def get_all_events(self, from_block: int, to_block: int) -> dict[str, list]:
        events = {}
        for contract_name, event_names in contract_to_events.items():
            contract = self._contract_manager.get_contract(contract_name)
            for event_name in event_names:
                event = getattr(contract.events, event_name)
                events[event_name] = await event.get_logs(from_block=from_block, to_block=to_block)
        return events


def bootstrap_synthetix(chain_config: ChainConfig, etherscan_key: str) -> Synthetix:
    web3 = AsyncWeb3(AsyncHTTPProvider(chain_config.api))
    raw_contract_call = create_raw_contract_call()
    contract_manager = ContractManager(
        chain_config.chain,
        web3,
        raw_contract_call,
        chain_config.address_resolver_address,
        etherscan_key,
    )
    contract_caller = ContractCaller(contract_manager, raw_contract_call)
    synthetix = Synthetix(chain_config.chain, web3, contract_manager, contract_caller)
    return synthetix
