import asyncio
import time

from app.common import SNXData
from app.snx_staking.synthetix import Synthetix


class SNXDataManager:
    # Hardcoded because don't see reasons make flexible
    _period_duration: int = 604800
    _synthetix: Synthetix
    snx_data: SNXData

    def __init__(self, synthetix: Synthetix, snx_data: SNXData):
        self._synthetix: Synthetix = synthetix
        self.snx_data: SNXData = snx_data

    async def _update_prices(self) -> None:
        snx_price, sds_price = await self._synthetix.get_synthetix_prices()

        self.snx_data.snx_updated = self.snx_data.snx_price != snx_price
        self.snx_data.sds_updated = self.snx_data.sds_price != sds_price
        self.snx_data.snx_price = snx_price
        self.snx_data.sds_price = sds_price

    async def _check_new_period(self):
        self.snx_data.period_updated = False
        if time.time() <= self.snx_data.period_end:
            return
        period_data = await self._synthetix.get_period_data()
        if period_data[2] == self.snx_data.period_start:
            return
        self.snx_data.period_start = period_data[2]
        self.snx_data.period_end = self.snx_data.period_start + self._period_duration
        self.snx_data.period_updated = True

    async def update(self):
        """
        :return: is_new_period_started
        """
        t_update_prices = asyncio.create_task(self._update_prices())
        t_check_period = asyncio.create_task(self._check_new_period())
        await asyncio.gather(t_update_prices, t_check_period)
