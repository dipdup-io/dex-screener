from typing import Any

from dex_screener import models


def test_fix_multilocation():
    path = [
        [
            {
                'parents': 0,
                'interior': {
                    '__kind': 'X2',
                    'value': [
                        {
                            '__kind': 'PalletInstance',
                            'value': 50,
                        },
                        {
                            '__kind': 'GeneralIndex',
                            'value': '1337',
                        },
                    ],
                },
            },
            84640,
        ],
        [
            {
                'parents': 1,
                'interior': {
                    '__kind': 'Here',
                },
            },
            122612710,
        ],
    ]

    expected_path = (
        (
            {
                'parents': 0,
                'interior': {
                    'X2': (
                        {'PalletInstance': 50},
                        {'GeneralIndex': 1337},
                    ),
                },
            },
            84640,
        ),
        (
            {
                'parents': 1,
                'interior': 'Here',
            },
            122612710,
        ),
    )

    assert models.fix_multilocation(path) == expected_path
