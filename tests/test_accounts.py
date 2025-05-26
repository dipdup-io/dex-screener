import pytest

from dex_screener.models.dex_fields import Account


class TestAccounts:
    @pytest.mark.parametrize(
        'account_init_value, account_address',
        (
            (
                '0x00c30560019b1565ab9647c5b3134e325f46ce2c07438ba5b6ba80ee3685bd77',
                '0x00c30560019b1565ab9647c5b3134e325f46ce2c07438ba5b6ba80ee3685bd77',
            ),
            (
                '0X9E289D693888D1BF3BCFA508F827240C56BA2E28BF0F7E429D0FB5CFD867FF62',
                '0x9e289d693888d1bf3bcfa508f827240c56ba2e28bf0f7e429d0fb5cfd867ff62',
            ),
            (
                '16kEGFeyNHmQqpMXwcfRtu2tBMwgsu7PdTF3EQzCgNwJhMUG',
                '0xfe255de774a4fee89844342b558e8817d8914701490f991fbd97925b490268e4',
            ),
            (
                '7PLnYkmNacsCgWqm1A5vgfnetvxDLSnBWi9JzUWArFQ2RiZV',
                '0xfe255de774a4fee89844342b558e8817d8914701490f991fbd97925b490268e4',
            ),
            (
                '14zJrZTexUcA1NZzQPPLusPppmsejSPQHU39yCNzLWSempGP',
                '0xb069cabc2ba7970d0af3aaee3111446290b884f4fcd87799138daa39785e072d',
            ),
            ('7L53bUTBbfuj14UpdCNPwmgzzHSsrsTWBHX5pys32mVWM3C1', f'0x{(b"modl" + b"omnipool").hex():<064}'),
            ('13UVJyLnPLowAMzbZewu9zwEGiSMQKniJ2cp4vM4ru2nci9N', f'0x{(b"modl" + b"omnipool").hex():<064}'),
            (
                '0x6d6f646c6f6d6e69706f6f6c0000000000000000000000000000000000000000',
                f'0x{(b"modl" + b"omnipool").hex():<064}',
            ),
        ),
    )
    def test_account_format(self, account_init_value, account_address):
        test_account = Account(account_init_value)
        assert issubclass(type(test_account), str)
        assert isinstance(test_account, Account)
        assert test_account == account_address
        assert test_account == Account(account_address)
