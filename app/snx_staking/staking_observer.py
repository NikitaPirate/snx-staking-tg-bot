import asyncio
import logging
import time
from dataclasses import dataclass, field

from eth_typing import AnyAddress

from app.common import Chain
from app.snx_staking.account_manager import AccountManager
from app.snx_staking.snx_data_manager import SNXDataManager
from app.snx_staking.synthetix import Synthetix

logger = logging.getLogger(__name__)


@dataclass
class SynthetixUpdate:
    reinit: bool = False
    can_init_new_accounts: bool = False
    events: dict = field(default_factory=dict)
    current_block: int | None = None


class StakingObserver:
    _last_checked_events_block: int
    _last_contracts_check: float
    _last_events_check: float

    def __init__(
        self,
        chain: Chain,
        synthetix: Synthetix,
        snx_data_manager: SNXDataManager,
        account_manager: AccountManager,
        new_accounts_queue: asyncio.Queue[AnyAddress],
        contracts_check_interval: int = 60 * 60 * 24,
        events_check_interval: int = 60 * 10,
    ):
        self.chain = chain
        self._synthetix: Synthetix = synthetix
        self._snx_data_manager: SNXDataManager = snx_data_manager
        self._account_manager = account_manager
        self._new_accounts_queue: asyncio.Queue[AnyAddress] = new_accounts_queue

        self._contract_check_interval: int = contracts_check_interval
        self._events_check_interval: int = events_check_interval

        self._is_first_run = True

    async def _init(self):
        now = time.time()
        current_block = await self._synthetix.get_block_num()
        await self._snx_data_manager.update()
        await self._account_manager.init_all_accounts(current_block)
        logger.info(f"{self.chain} init in {time.time() - now}")

        now = time.time()
        self._last_contracts_check = now
        self._last_events_check = now
        self._last_checked_events_block = current_block

    async def update(self):
        if self._is_first_run:
            await self._synthetix.install_contracts()
            await self._init()
            self._is_first_run = False
            return

        update = await self._get_synthetix_update()
        if update.reinit:
            await self._init()
            return

        # INIT NEW ACCOUNTS
        if update.can_init_new_accounts:
            new_accounts = []
            while not self._new_accounts_queue.empty():
                new_accounts.append(await self._new_accounts_queue.get())
            await self._account_manager.init_accounts(new_accounts, update.current_block)

        await self._account_manager.update_accounts(update.events)

    async def _get_synthetix_update(self) -> SynthetixUpdate:
        #   1. check address collector updates
        now = time.time()
        if now - self._contract_check_interval > self._last_contracts_check:
            if await self._synthetix.check_contracts_updates():
                return SynthetixUpdate(reinit=True)
            self._last_contracts_check = now

        #   2. update snx_data
        await self._snx_data_manager.update()
        if self._snx_data_manager.snx_data.period_updated:
            return SynthetixUpdate(reinit=True)

        #   3. check events
        if now - self._events_check_interval > self._last_events_check:
            current_block = await self._synthetix.get_block_num()
            events = await self._synthetix.get_all_events(
                from_block=self._last_checked_events_block + 1, to_block=current_block
            )
            self._last_events_check = now
            self._last_checked_events_block = current_block
            return SynthetixUpdate(
                reinit=False,
                events=events,
                can_init_new_accounts=True,
                current_block=current_block,
            )
        return SynthetixUpdate()
