from __future__ import annotations

from decimal import DefaultContext
from decimal import setcontext

RUNTIME_BALANCE_MAX_DIGITS = len(str(2 ** 128 - 1))
DEX_SCREENER_PRICE_MAX_DECIMALS = 50

DEX_SCREENER_PRICE_MAX_DIGITS = RUNTIME_BALANCE_MAX_DIGITS * 2
# Suppose the edge case with probability of division 1e38 by 9e-38

DefaultContext.prec = DEX_SCREENER_PRICE_MAX_DIGITS

setcontext(DefaultContext)
