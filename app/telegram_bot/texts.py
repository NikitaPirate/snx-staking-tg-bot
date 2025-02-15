bot_description = """
Helper for monitoring Synthetix staking.
"""

bot_short_description = """
Helper for monitoring Synthetix staking.
discussion: @snx_bot_discussion
developer:  @NikitaPirate
"""

info_command = """
*Commands:*
/accounts
/dashboard
/payday
/info
/start - Command to start using the bot. If the bot doesn't work correctly, it's possible you
 never sent it.

*Tutorial:* https://medium.com/@nikita-k/telegram-bot-update-fd56d2931574

*Key Features:*
__Dashboard Updates:__ The dashboard updates automatically whenever something changes.
__Customizable Dashboard:__ You can customize your dashboard to suit your preferences.
__Permanent Notifications:__ Notifications don't get deleted after being sent. They are
 temporarily disabled until the condition is met again, after which they are reactivated.

*Notifications:*
__Ratio:__ You receive a notification when your account's collateral ratio crosses a specified
 threshold.
__Rewards Claimable:__ You get notified when your account has claimable SNX rewards, and your
 c-ratio is above the system threshold.
__Rewards Claimed:__ You get notified when SNX reward claimed. (may not work if you claim rewards
 within ≈ 1 minute after the epoch starts).
__Flagged for Liquidation:__ You'll receive a notification if your account is flagged for
 liquidation.

*Tradeoffs:*
The bot does not take into account until the end of the epoch: liquidation rewards, merged
 accounts. This will be taken into account with the beginning of a new epoch.

*Bot discussion:* @snx\\_bot\\_discussion
*Bot developer:*  @NikitaPirate
"""
