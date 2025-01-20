def get_pool_id(pool_id_list) -> str | None:
    assert len(pool_id_list) == 2
    assert pool_id_list[0]['interior'] == 'Here'
    try:
        return '-1_' + str(pool_id_list[1]['interior']['X2'][-1]['GeneralIndex'])
    except KeyError:
        return None
