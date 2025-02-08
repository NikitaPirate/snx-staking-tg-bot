from asyncio import Queue, Semaphore

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.common import Chain, SNXData
from app.config import ChainConfig, Config
from app.data_access import UOWFactoryType, uow_factory_maker
from app.snx_staking import AccountManager, SNXDataManager, StakingObserver, bootstrap_synthetix


def bootstrap_staking_observers() -> dict[Chain, StakingObserver]:
    load_dotenv()

    config = Config()
    web3_calls_semaphore = Semaphore(10)

    engine = create_async_engine(config.db_connection)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    uow_factory = uow_factory_maker(session_factory)

    staking_observers = {}
    for chain, chain_config in config.chains.items():
        staking_observers[chain] = bootstrap_chain(
            chain_config, config.etherscan_key, web3_calls_semaphore, uow_factory
        )

    return staking_observers


def bootstrap_chain(
    chain_config: ChainConfig,
    etherscan_key: str,
    web3_calls_semaphore: Semaphore,
    uow_factory: UOWFactoryType,
) -> StakingObserver:
    # Here temporary while no bot
    new_accounts_queue = Queue()

    synthetix = bootstrap_synthetix(chain_config, etherscan_key, web3_calls_semaphore)

    snx_data = SNXData(chain=chain_config.chain)
    snx_data_manager = SNXDataManager(synthetix, snx_data)
    account_manager = AccountManager(chain_config.chain, snx_data, synthetix, uow_factory)
    staking_observer = StakingObserver(
        chain_config.chain, synthetix, snx_data_manager, account_manager, new_accounts_queue
    )

    return staking_observer
