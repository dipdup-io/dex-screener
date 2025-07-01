from copy import copy
import logging
from functools import cache
from pathlib import Path
from typing import Any

import orjson
from aiosubstrate import SubstrateInterface

# NOTE: It's not an original xxhash, but a custom implementation
from aiosubstrate.utils.hasher import xxh128 as substrate_xxh128
from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent, SubstrateEventData
from scalecodec import GenericExtrinsic
from scalecodec import ScaleBytes

from reserves.types.hydradx.substrate_events.balances_balance_set.v100 import V100 as BalancesBalanceSetPayload
from reserves.types.hydradx.substrate_events.sudo_sudid import SudoSudidPayload

_logger = logging.getLogger(__name__)

_processed_extrinsics = set()



async def on_sudo_sudid(
    ctx: HandlerContext,
    event: SubstrateEvent[SudoSudidPayload],
) -> None:
    extrinsic_index = f'{event.data.block_number}-{event.data.extrinsic_index}'
    if extrinsic_index in _processed_extrinsics:
        return

    node = ctx.get_substrate_datasource('node')

    # Use node to get extrinsic params
    ext_params = await node._interface.retrieve_extrinsic_by_identifier(extrinsic_index)
    await ext_params.retrieve_extrinsic()
    ext_params = ext_params.extrinsic

    set_storage_calls = extract_set_storage_calls(ext_params)
    if not set_storage_calls:
        return

    print(f'Found {len(set_storage_calls)} set_storage calls in sudo_sudid extrinsic: {extrinsic_index}')

    await node._interface.init_runtime(block_id=event.level)



    for call in set_storage_calls:
        key = call['call_args'][0]['value'][0][0]
        value = call['call_args'][0]['value'][0][1]

        try:
            key, value = await decode_set_storage_call(node._interface, key, value)
        except Exception as e:
            _logger.error('!!! Failed to decode set_storage call: %s', e)
            continue

        try:
            free=value['data']['free'].value if value else 0
            reserved=value['data']['reserved'].value if value else 0
        except TypeError as e:
            _logger.error('!!! Failed to decode balance value: %s', e)
            continue

        decoded_args = BalancesBalanceSetPayload(
            who=key.value,
            free=free,
            reserved=reserved,
        )

        new_event_data = SubstrateEventData(
            **{
                **event.data.__dict__,
                'decoded_args': decoded_args,
                'args': None,
            }
        )
        new_event = SubstrateEvent(
            data=new_event_data,
            runtime=event.runtime,
        )
        await ctx.fire_handler(
            name='hydradx.balances.on_balance_set',
            index='hydradx_events',
            args=(new_event, ),
        )
    
    _processed_extrinsics.add(extrinsic_index)

async def decode_set_storage_call(self: SubstrateInterface, key: str, value: str) -> tuple[Any, Any | None]:
    module, storage_function, key = parse_set_storage_key(key)

    metadata_pallet = self.metadata.get_metadata_pallet(module)
    if not metadata_pallet:
        raise ValueError(f'Pallet {module} not found in metadata')
    storage_item = metadata_pallet.get_storage_function(storage_function)

    value_type = storage_item.get_value_type_string()
    param_types = storage_item.get_params_type_string()
    key_hashers = storage_item.get_param_hashers()

    def concat_hash_len(key_hasher: str) -> int:
        if key_hasher == 'Blake2_128Concat':
            return 16
        if key_hasher == 'Twox64Concat':
            return 8
        if key_hasher == 'Identity':
            return 0
        raise ValueError('Unsupported hash type')

    # Determine type string
    print(key, value)
    key_type_string = []
    for n in range(len(param_types)):
        key_type_string.append(f'[u8; {concat_hash_len(key_hashers[n])}]')
        key_type_string.append(param_types[n])

    item_key = self.runtime_config.create_scale_object(
        type_string=f'({", ".join(key_type_string)})',
        data=ScaleBytes('0x' + key),
        metadata=self.metadata,
    )
    item_key.decode()
    item_key = item_key.value_object[1]

    if isinstance(value, str) and not value.replace('\x00', ''):
        return (item_key, None)
    # if not value.startswith('0x'):
    #     value = '0x' + value

    item_value = self.runtime_config.create_scale_object(
        type_string=value_type,
        data=ScaleBytes(value),
        metadata=self.metadata,
    )
    item_value.decode()
    item_value = item_value.value_object

    print(item_key, item_value)
    return (item_key, item_value)


@cache
def get_prefix_hashes() -> tuple[dict[str, str], dict[str, str]]:
    # FIXME: hardcode
    metadata_path = Path(__file__).parent.parent.parent.parent / 'abi' / 'hydradx' / 'v313.json'
    metadata = orjson.loads(metadata_path.read_bytes())

    pallet_xxs = {}
    storage_xxs = {}

    for pallet in metadata:
        name = pallet['name']
        hash_hex = substrate_xxh128(name).hex()
        pallet_xxs[hash_hex] = name

        for storage in pallet.get('storage') or []:
            storage_name = storage['name']
            storage_hash_hex = substrate_xxh128(storage_name).hex()
            storage_xxs[storage_hash_hex] = storage_name

    return pallet_xxs, storage_xxs


def extract_set_storage_calls(obj):
    results = []
    if isinstance(obj, GenericExtrinsic):
        obj = obj.value

    if isinstance(obj, dict):
        if obj.get('call_function') == 'set_storage' and obj.get('call_module') == 'System':
            results.append(obj)
        if 'call' in obj:
            results.extend(extract_set_storage_calls(obj['call']))
        if 'call_args' in obj:
            results.extend(extract_set_storage_calls(obj['call_args']))
        for key in ('value', 'params'):
            if key in obj:
                results.extend(extract_set_storage_calls(obj[key]))
    elif isinstance(obj, list):
        for item in obj:
            results.extend(extract_set_storage_calls(item))
    return results


def parse_set_storage_key(
    key: str,
):
    key_bytes = bytes.fromhex(key[2:])
    pallet_xxs, storage_xxs = get_prefix_hashes()

    pallet_prefix = key_bytes[:16].hex()
    storage_prefix = key_bytes[16:32].hex()
    rest = key_bytes[32:].hex()

    return (
        pallet_xxs[pallet_prefix],
        storage_xxs[storage_prefix],
        rest,
    )





#     key_bytes = bytes.fromhex(key[2:])
#     # value_bytes = bytes.fromhex(value)

#     pallet_xxs, storage_xxs = get_prefix_hashes()

#     pallet_prefix = key_bytes[:16].hex()
#     storage_prefix = key_bytes[16:32].hex()
#     key_bytes[32:].hex()

#     storage_name = storage_xxs[storage_prefix]
#     pallet_name = pallet_xxs[pallet_prefix]

#     path = f'{pallet_name}.{storage_name}'

#     if path != 'System.Account':
#         return


#     pallet_abi = next(p for p in metadata if p['name'] == pallet_name)
#     storage_abi = next(s for s in pallet_abi['storage'] if s['name'] == storage_name)

#     key_type = storage_abi['type']['n_map_type']['key_vec'][0]
#     value_type = storage_abi['type']['n_map_type']['value'].replace('frame_system:AccountInfo')

#     decoded_key = decode_arg(
#         runtime_config=runtime_config,
#         value=key_bytes,
#         type_=key_type,
#         full_type=key_type,
#     )
#     decoded_value = decode_arg(
#         runtime_config=runtime_config,
#         value=value,
#         type_=value_type,
#         full_type=value_type,
#     )

#     print(f'New {path} storage value:')
#     print(f'  - {key_type=}')
#     print(f'  - {decoded_key=}')
#     print(f'  - {value_type=}')
#     print(f'  - {decoded_value=}')

