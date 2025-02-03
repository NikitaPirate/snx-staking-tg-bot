import asyncio
import logging
import time

from eth_typing import Address

from app.common import Chain
from app.snx_staking.account_manager import AccountManager
from app.snx_staking.snx_data import SNXDataManager
from app.snx_staking.synthetix import Synthetix

logger = logging.getLogger(__name__)


class StakingObserver:
    chain: Chain
    _synthetix: Synthetix
    _sleep_interval: int
    _snx_data_manager: SNXDataManager
    _account_manager: AccountManager
    _new_accounts_queue: asyncio.Queue[Address]

    def __init__(
        self,
        chain: Chain,
        synthetix: Synthetix,
        interval: int,
        snx_data_manager: SNXDataManager,
        account_manager: AccountManager,
    ) -> None:
        self.chain = chain
        self._synthetix = synthetix
        self._sleep_interval = interval
        self._snx_data_manager = snx_data_manager
        self._account_manager = account_manager

    async def run(self) -> None:
        try:
            await self._init()
            while True:
                should_resync = await self._update()
                if should_resync:
                    await self._init()
                await asyncio.sleep(self._sleep_interval)
        except Exception as e:
            logger.error(f"Fatal error in SnxStakingMonitor: {e}", exc_info=True)
            raise

    async def _init(self) -> None:
        start = time.time()
        await self._synthetix.init()
        block_num = await self._synthetix.get_block_num()
        await self._snx_data_manager.update()
        await self._account_manager.init_all_accounts(block_num)
        await self._synthetix.run_filters(block_num + 1)

        logger.info(f"{self.chain} SnxStakingMonitor started in: {time.time() - start}")

    async def _update(self) -> bool:
        """
        :returns is_new_period_started(should_resync)
        """

        await self._synthetix.address_collector_update()
        logger.debug(f"Chain: {self.chain}, address_collector update success")

        new_period_started = await self._snx_data_manager.update()
        logger.debug(f"Chain: {self.chain}, snx_data_manager updated success")
        if new_period_started:
            return True

        new_events = await self._synthetix.get_filters_updates()
        logger.debug(f"Chain: {self.chain}, new_events collected success")

        # INIT NEW ACCOUNTS
        new_accounts = []
        while not self._new_accounts_queue.empty():
            new_accounts.append(await self._new_accounts_queue.get())
        await self._account_manager.init_accounts(new_accounts, "latest")
        logger.debug(f"Chain: {self.chain}, new_accounts inited success")

        await self._account_manager.update_accounts(new_events)
        return False
