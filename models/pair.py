from typing import Literal

from dex_screener import models as m


async def upsert_pair_model(
    asset_in: int,
    asset_out: int,
    dex_key: Literal['hydradx'] | Literal['assethub'] = 'hydradx',
) -> str:
    pair_id = m.get_pair_id(asset_in, asset_out)
    # FIXME: ensure pair data is correct and full
    pair_model, created = await m.Pair.get_or_create(
        id=pair_id,
        defaults={
            'asset_0_id': asset_in,
            'asset_1_id': asset_out,
            'dex_key': dex_key,
            # created_at_block_number
            # created_at_block_timestamp
            # created_at_txn_id
            # creator
            # fee_bps
            # metadata
        },
    )
    if not created:
        await pair_model.save()
    return pair_id
