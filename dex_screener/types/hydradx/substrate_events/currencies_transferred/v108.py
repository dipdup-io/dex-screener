from typing import TypedDict

# """
# Currency transfer success.
# """
V108 = TypedDict(
    'V108',
    {
        'currency_id': int,
        'from': str,
        'to': str,
        'amount': int,
    },
)
