from tortoise.functions import Sum

from reserves.models import BalanceUpdateEvent


async def balance_update_from_balance(
    account: str,
    asset_id: int,
    balance: int,
) -> int:
    """
    Calculate the balance update based on the current balance.
    If the balance is None, it is treated as zero.
    """
    latest_balance: int = (
        await BalanceUpdateEvent.filter(  # type: ignore[assignment]
            asset_id=asset_id,
            account=account,
        )
        .group_by(
            'account',
            'asset_id',
        )
        .annotate(latest_balance=Sum('balance_update'))
        .first()
        .values_list('latest_balance', flat=True)
    )
    if latest_balance is None:
        latest_balance = 0
    return balance - latest_balance
