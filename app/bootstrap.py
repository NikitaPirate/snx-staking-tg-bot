import asyncio

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from telegram.ext import Application, ApplicationBuilder, ContextTypes

from app.common import Chain, ChainConfig, SNXData, SNXMultiChainData
from app.config import Config
from app.data_access import UOWFactoryType, uow_factory_maker
from app.snx_staking import AccountManager, SNXDataManager, StakingObserver, bootstrap_synthetix
from app.telegram_bot import (
    AccountUpdateProcessor,
    BotData,
    ChatData,
    SnxBotContext,
    error_handler,
    handlers,
    run_account_update_processor,
    update_staking_observers_job,
)


def bootstrap() -> Application:
    load_dotenv()
    config = Config()

    # UOW
    engine = create_async_engine(
        config.db_connection,
    )
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    uow_factory = uow_factory_maker(session_factory)

    # ASYNC QUEUES
    new_accounts_queues = {Chain(chain): asyncio.Queue() for chain in Chain}
    updates_accounts_queue = asyncio.Queue()

    # SNX
    snx_multichain_data = SNXMultiChainData(config.chains)

    staking_observers = bootstrap_staking_observers(
        uow_factory,
        config.chains,
        snx_multichain_data,
        config.etherscan_key,
        new_accounts_queues,
        updates_accounts_queue,
    )

    # TG APP
    tg_app = bootstrap_telegram_bot(config.telegram_token)

    account_update_processor = AccountUpdateProcessor(
        tg_app.bot, uow_factory, snx_multichain_data, updates_accounts_queue
    )

    tg_app.bot_data = BotData(
        snx_data=snx_multichain_data,
        uow_factory=uow_factory,
        new_accounts_queues=new_accounts_queues,
        staking_observers=staking_observers,
        account_update_processor=account_update_processor,
    )

    tg_app.job_queue.run_repeating(
        update_staking_observers_job, 60, first=1, name="Update staking observers"
    )
    tg_app.job_queue.run_once(run_account_update_processor, 0.1, name="Account update processor")

    return tg_app


def bootstrap_telegram_bot(telegram_token: str) -> Application:
    context_types = ContextTypes(context=SnxBotContext, chat_data=ChatData, bot_data=BotData)
    app = ApplicationBuilder().token(telegram_token).context_types(context_types).build()
    app.add_handlers(handlers)
    app.add_error_handler(error_handler)

    return app


def bootstrap_staking_observers(
    uow_factory: UOWFactoryType,
    chain_configs: dict[Chain, ChainConfig],
    snx_multichain_data: SNXMultiChainData,
    etherscan_key: str,
    new_accounts_queues: dict[Chain, asyncio.Queue],
    updates_accounts_queue: asyncio.Queue,
) -> dict[Chain, StakingObserver]:
    staking_observers = {}

    for chain, chain_config in chain_configs.items():
        staking_observers[chain] = bootstrap_chain(
            chain_config,
            etherscan_key,
            uow_factory,
            snx_multichain_data[chain],
            updates_accounts_queue,
            new_accounts_queues[chain],
        )
    return staking_observers


def bootstrap_chain(
    chain_config: ChainConfig,
    etherscan_key: str,
    uow_factory: UOWFactoryType,
    snx_data: SNXData,
    updated_accounts_queue: asyncio.Queue,
    new_accounts_queue: asyncio.Queue,
) -> StakingObserver:
    synthetix = bootstrap_synthetix(chain_config, etherscan_key)

    snx_data_manager = SNXDataManager(synthetix, snx_data)
    account_manager = AccountManager(
        chain_config.chain, snx_data, synthetix, uow_factory, updated_accounts_queue
    )
    staking_observer = StakingObserver(
        chain_config.chain, synthetix, snx_data_manager, account_manager, new_accounts_queue
    )

    return staking_observer
