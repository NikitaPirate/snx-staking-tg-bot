import asyncio
import datetime
import logging
import time
from collections import defaultdict
from decimal import Decimal

from eth_typing import Address, BlockIdentifier
from eth_utils import to_checksum_address

from app.common import Chain, SNXData
from app.data_access import UOWFactoryType
from app.models import Account
from app.snx_staking.synthetix import EventName, Synthetix

logger = logging.getLogger(__name__)


class AccountManager:
    chain: Chain
    _snx_data: SNXData
    _synthetix: Synthetix
    _uow_factory: UOWFactoryType

    def __init__(
        self, chain: Chain, snx_data: SNXData, synthetix: Synthetix, uow_factory: UOWFactoryType
    ) -> None:
        self.chain = chain
        self._snx_data = snx_data
        self._synthetix = synthetix
        self._uow_factory = uow_factory

    async def init_accounts(
        self, addresses: list[Address], block_identifier: BlockIdentifier
    ) -> None:
        start = time.time()
        await asyncio.gather(
            *[
                asyncio.create_task(self._init_account(address, block_identifier))
                for address in addresses
            ],
            return_exceptions=True,
        )
        logger.info(f"{self.chain.value} init in {time.time() - start}")

    async def init_all_accounts(self, block_identifier: BlockIdentifier) -> None:
        async with self._uow_factory() as uow:
            addresses = await uow.accounts.get_all_addresses_for_chain(self.chain)
        addresses = [to_checksum_address(address) for address in addresses]
        await self.init_accounts(addresses, block_identifier)

    async def _init_account(self, address: Address, block_identifier: BlockIdentifier) -> None:
        account_data = await self._synthetix.load_address_data(address, block_identifier)
        async with self._uow_factory() as uow:
            if not (
                account := await uow.accounts.get_by_address_chain_or_none(address, self.chain)
            ):
                return

            account.snx_count = Decimal(str(account_data.collateral))
            account.sds_count = Decimal(str(account_data.debt_share))
            account.claimable_snx = account_data.fees_available[1]

            liquidation_deadline = (
                None
                if account_data.liquidation_deadline == 0
                else datetime.datetime.fromtimestamp(account_data.liquidation_deadline)
            )
            account.liquidation_deadline = liquidation_deadline

            self._calculate_collateral(account)
            self._calculate_debt(account)
            self._calculate_c_ratio(account)

    async def update_accounts(self, events: dict) -> None:
        address_to_event = self._group_events(events)

        if any([self._snx_data.snx_updated, self._snx_data.sds_updated]):
            async with self._uow_factory() as uow:
                addresses_to_update = await uow.accounts.get_all_addresses_for_chain(self.chain)
        else:
            addresses_to_update = set(address_to_event.keys())

        tasks = []
        for address in addresses_to_update:
            events = address_to_event.get(address, [])
            tasks.append(asyncio.create_task(self._update_account(address, events)))
        await asyncio.gather(*tasks)

    async def _update_account(self, address: str, events: list) -> None:
        async with self._uow_factory() as uow:
            if not (
                account := await uow.accounts.get_by_address_chain_or_none(address, self.chain)
            ):
                return
            self._apply_events(account, events)

            collateral_updated = self._snx_data.snx_updated or any(
                event["type"] in {EventName.SEND, EventName.RECEIVE, EventName.FEES_CLAIMED}
                for event in events
            )
            debt_updated = self._snx_data.sds_updated or any(
                event["type"] in {EventName.MINT, EventName.BURN} for event in events
            )

            if collateral_updated:
                self._calculate_collateral(account)

            if debt_updated:
                self._calculate_debt(account)

            if collateral_updated or debt_updated:
                self._calculate_c_ratio(account)

    # CALCULATIONS
    def _calculate_collateral(self, account: Account) -> None:
        account.collateral = account.snx_count * self._snx_data.snx_price

    def _calculate_debt(self, account: Account) -> None:
        account.debt = (account.sds_count * self._snx_data.sds_price) // (10**27)

    @staticmethod
    def _calculate_c_ratio(account: Account) -> None:
        if account.debt != 0:
            account.c_ratio = round((account.collateral / account.debt / 10**18), 5)
        else:
            account.c_ratio = 0

    # EVENTS
    def _group_events(self, events: dict) -> dict[str, list]:
        """:returns dict{address: events}"""
        events_by_address = defaultdict(list)

        # handle transfer events
        transfers = events.pop("transfer", [])
        split_transfers = self._split_transfer_events(transfers)
        if split_transfers:
            events.update(split_transfers)

        for event_type, event_list in events.items():
            for event in event_list:
                events_by_address[event["address"]].append({"type": event_type, **event})

        return events_by_address

    def _split_transfer_events(self, transfers: list) -> dict[str, list]:
        events = defaultdict(list)

        for transfer in transfers:
            if transfer.from_address == self._synthetix.vesting_contract_address:
                continue

            events[EventName.SEND].append(
                {"account": transfer["from"], "amount": transfer["value"]}
            )
            events[EventName.RECEIVE].append(
                {"account": transfer["to"], "amount": transfer["value"]}
            )

        return events

    @staticmethod
    def _apply_events(account: Account, events: list[dict]) -> None:
        handlers = {
            EventName.MINT: lambda _account, _event: setattr(
                _account, "sds_count", _account.sds_count + _event["amount"]
            ),
            EventName.BURN: lambda _account, _event: setattr(
                _account, "sds_count", _account.sds_count - _event["amount"]
            ),
            EventName.SEND: lambda _account, _event: setattr(
                _account, "snx_count", _account.snx_count - _event["amount"]
            ),
            EventName.RECEIVE: lambda _account, _event: setattr(
                _account, "snx_count", _account.snx_count + _event["amount"]
            ),
            EventName.FEES_CLAIMED: lambda _account, _event: (
                setattr(_account, "snx_count", _account.snx_count + _event["snxRewards"]),
                setattr(_account, "claimable_snx", 0),
            ),
            EventName.FLAGGED_FOR_LIQUIDATION: lambda _account, _event: setattr(
                _account,
                "liquidation_deadline",
                datetime.datetime.fromtimestamp(_event["deadline"]),
            ),
            EventName.REMOVED_FROM_LIQUIDATION: lambda _account, _event: setattr(
                _account, "liquidation_deadline", None
            ),
        }

        for event in events:
            handlers[event["type"]](account, event)
