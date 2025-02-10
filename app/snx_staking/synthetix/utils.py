from asyncio import Semaphore
from typing import Any, Protocol

from eth_typing import BlockIdentifier
from tenacity import retry, stop_after_delay, wait_exponential
from web3 import Web3
from web3.contract.async_contract import AsyncContract, AsyncContractFunction

sUSD_bytes = "0x7355534400000000000000000000000000000000000000000000000000000000"  # noqa N816
SNX_bytes = "0x534e580000000000000000000000000000000000000000000000000000000000"


def str_to_bytes32(text: str) -> bytes:
    return Web3.to_bytes(hexstr=Web3.to_hex(text=text)).ljust(32, b"\00")


# Raw contract call


class RawContractCall(Protocol):
    async def __call__(
        self,
        contract: AsyncContract,
        function_name: str,
        block_identifier: BlockIdentifier,
        *args: Any,
        **kwargs: Any,
    ) -> Any: ...  # noqa: ANN401


def create_raw_contract_call(max_parallel_calls: int = 10) -> RawContractCall:
    semaphore: Semaphore = Semaphore(max_parallel_calls)

    @retry(wait=wait_exponential(max=60), stop=stop_after_delay(600))
    async def raw_contract_call(
        contract: AsyncContract,
        function_name: str,
        block_identifier: BlockIdentifier,
        *args: Any,
        **kwargs: Any,
    ) -> Any:  # noqa: ANN401
        function: AsyncContractFunction = getattr(contract.functions, function_name)(
            *args, **kwargs
        )
        async with semaphore:
            return await function.call(block_identifier=block_identifier)

    return raw_contract_call
