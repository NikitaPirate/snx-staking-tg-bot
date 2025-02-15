from app.models import NotifType


class Callbacks:
    # MAIN MENU
    DASHBOARD = "dashboard"
    ACCOUNTS_MENU = "accounts_menu"

    # ACCOUNTS MENU
    ADD_ACCOUNT = "add_account"

    # ACCOUNT MENU
    ACCOUNT_MENU = "account_menu"
    CUSTOMIZE_DISPLAY = "customize_display"
    ACCOUNT_NOTIFS = "account_notifs"
    DELETE_ACCOUNT = "delete_account"

    # ACCOUNT NOTIFS MENU
    CREATE_NOTIF = "create_notif"

    # ACCOUNT NOTIF MENU
    DELETE_NOTIF = "delete_notif"


class States:
    (
        ACCOUNTS_MENU,
        ACCOUNT_MENU,
        HANDLE_ACCOUNT_INFO,
        ACCOUNT_ADDED,
        CUSTOMIZE_ACCOUNT_DISPLAY,
    ) = [f"accounts{i}" for i in range(5)]

    (
        ACCOUNT_NOTIFS_MENU,
        SELECT_NOTIF_TYPE_TO_CREATE,
        HANDLE_NOTIF_INFO,
        NOTIF_CREATED,
    ) = [f"notifs{i}" for i in range(4)]


NOTIF_TYPE_NAMES = {
    NotifType.ratio: "Ratio",
    NotifType.rewards_claimable: "Rewards claimable",
    NotifType.rewards_claimed: "Rewards claimed",
    NotifType.flagged_for_liquidation: "Flagged for liquidation",
}


COMMANDS = [
    ("dashboard", "Dashboard"),
    ("accounts", "Edit accounts"),
    ("info", "Info"),
    ("payday", "Time remaining until the end of the epoch"),
]
