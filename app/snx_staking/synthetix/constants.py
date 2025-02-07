class ContractName:
    EXCHANGE_RATES = "ExchangeRates"
    SYNTHETIX = "Synthetix"
    LIQUIDATOR = "Liquidator"
    SYNTHETIX_DEBT_SHARE = "SynthetixDebtShare"
    PROXY_FEE_POOL = "ProxyFeePool"
    PROXY_ERC20 = "ProxyERC20"
    REWARD_ESCROW_V2 = "RewardEscrowV2"
    AGGREGATOR_DEBT_RATIO = "ext:AggregatorDebtRatio"


class EventName:
    BURN = "Burn"
    MINT = "Mint"
    SNX_TRANSFER = "Transfer"
    FEES_CLAIMED = "FeesClaimed"
    FLAGGED_FOR_LIQUIDATION = "AccountFlaggedForLiquidation"
    REMOVED_FROM_LIQUIDATION = "AccountRemovedFromLiquidation"
    # HELPERS
    SEND = "SEND"
    RECEIVE = "RECEIVE"


contract_names = [value for key, value in vars(ContractName).items() if not key.startswith("__")]

contract_to_events = {
    ContractName.SYNTHETIX_DEBT_SHARE: [EventName.MINT, EventName.BURN],
    ContractName.PROXY_ERC20: [EventName.SNX_TRANSFER],
    ContractName.PROXY_FEE_POOL: [EventName.FEES_CLAIMED],
    ContractName.LIQUIDATOR: [
        EventName.FLAGGED_FOR_LIQUIDATION,
        EventName.REMOVED_FROM_LIQUIDATION,
    ],
}
