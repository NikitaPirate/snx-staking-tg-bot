import asyncio

import aiohttp
from eth_typing import Address
from tenacity import retry, stop_after_attempt, wait_exponential
from web3 import AsyncWeb3
from web3.contract import AsyncContract

from app.common import Chain
from app.snx_staking.synthetix.addres_resolver_abi import address_resolver_abi
from app.snx_staking.synthetix.constants import contract_names
from app.snx_staking.synthetix.proxy_abi import proxy_abi
from app.snx_staking.synthetix.utils import RawContractCall, str_to_bytes32


class ContractManager:
    def __init__(
        self,
        chain: Chain,
        web3: AsyncWeb3,
        raw_contract_call: RawContractCall,
        address_resolver_address: Address,
        etherscan_key: str,
    ) -> None:
        self._chain: Chain = chain
        self._web3: AsyncWeb3 = web3
        self._raw_contract_call: RawContractCall = raw_contract_call
        self._address_resolver_contract: AsyncContract = self._web3.eth.contract(
            address=address_resolver_address, abi=address_resolver_abi
        )
        self._etherscan_key: str = etherscan_key

        self._contract_addresses: dict[str, Address] = {}
        self._contracts: dict[str, AsyncContract] = {}

    def get_contract(self, name: str) -> AsyncContract:
        return self._contracts[name]

    async def check_contracts_updates(self) -> bool:
        """Check if any contract addresses have been updated.
        Returns True if any contract address has changed."""

        async def is_contract_updated(contract_name: str) -> bool:
            current_address = self._contract_addresses[contract_name]
            new_address = await self._fetch_contract_address(contract_name)
            if current_address != new_address:
                await self._install_contract(contract_name, contract_address=new_address)
                return True
            return False

        checks = await asyncio.gather(
            *[is_contract_updated(name) for name in contract_names], return_exceptions=True
        )
        return any(checks)

    async def install_contracts(self) -> None:
        await asyncio.gather(
            *[self._install_contract(contract_name) for contract_name in contract_names],
            return_exceptions=True,
        )

    async def _install_contract(
        self, contract_name: str, contract_address: Address = None
    ) -> None:
        if not contract_address:
            contract_address: Address = await self._fetch_contract_address(contract_name)
        self._contract_addresses[contract_name] = contract_address

        if contract_name.startswith("Proxy"):
            proxy_contract = self._web3.eth.contract(address=contract_address, abi=proxy_abi)
            contract_address = await self._raw_contract_call(proxy_contract, "target", "latest")
        abi = await self._get_contract_abi(contract_address)
        contract = self._web3.eth.contract(address=contract_address, abi=abi)

        self._contracts[contract_name] = contract

    async def _fetch_contract_address(self, contract_name: str) -> Address:
        contract_name_bytes: bytes = str_to_bytes32(contract_name)
        contract_address: Address = await self._raw_contract_call(
            self._address_resolver_contract, "getAddress", "latest", contract_name_bytes
        )
        return contract_address

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=5),
    )
    async def _get_contract_abi(self, contract_address: Address) -> str:
        url = "https://api.etherscan.io/v2/api"
        params = {
            "chainid": self._chain.chain_id,
            "module": "contract",
            "action": "getabi",
            "address": contract_address,
            "apikey": self._etherscan_key,
        }
        async with aiohttp.ClientSession() as session, session.get(url, params=params) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}: {await response.text()}")
            data = await response.json()

        if data.get("status") == "1":
            return data["result"]
        raise Exception(f"Etherscan error: {data}")
