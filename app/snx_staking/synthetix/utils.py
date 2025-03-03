from asyncio import Semaphore
from typing import Union

from toolz import curry
from web3 import AsyncWeb3, Web3
from web3.middleware import Web3Middleware
from web3.middleware.base import Web3MiddlewareBuilder

sUSD_bytes = "0x7355534400000000000000000000000000000000000000000000000000000000"  # noqa N816
SNX_bytes = "0x534e580000000000000000000000000000000000000000000000000000000000"


def str_to_bytes32(text: str) -> bytes:
    return Web3.to_bytes(hexstr=Web3.to_hex(text=text)).ljust(32, b"\00")


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
