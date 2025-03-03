from asyncio import Semaphore
from typing import Any, Protocol, Union

from eth_typing import BlockIdentifier
from toolz import curry
from web3 import AsyncWeb3, Web3
from web3.contract.async_contract import AsyncContract, AsyncContractFunction
from web3.middleware import Web3Middleware
from web3.middleware.base import Web3MiddlewareBuilder

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


def create_raw_contract_call() -> RawContractCall:
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

        return await function.call(block_identifier=block_identifier)

    return raw_contract_call


class SemaphoreMiddleware(Web3MiddlewareBuilder):
    semaphore: Semaphore = None

    @staticmethod
    @curry
    def build(semaphore: Semaphore, w3: Union["AsyncWeb3", "Web3"]) -> Web3Middleware:
        middleware = SemaphoreMiddleware(w3)
        middleware.semaphore = semaphore
        return middleware

    async def async_wrap_make_request(self, make_request):  # noqa
        async def middleware(method, params):  # noqa
            async with self.semaphore:
                response = await make_request(method, params)
            return response

        return middleware
