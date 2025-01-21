from dex_screener import models as m


async def upsert_pair_model(asset_in: int, asset_out: int) -> str:
    pair_id = m.get_pair_id(asset_in, asset_out)
    # FIXME: ensure pair data is correct and full
    pair_model, created = await m.Pair.get_or_create(
        id=pair_id, defaults={'asset_0_id': asset_in, 'asset_1_id': asset_out, 'dex_key': 'hydradx'}
    )
    if not created:
        await pair_model.save()
    return pair_id
