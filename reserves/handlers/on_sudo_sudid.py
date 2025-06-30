from functools import cache
from pathlib import Path
from typing import Any

import orjson

# NOTE: It's not an original xxhash, but a custom implementation
from aiosubstrate.utils.hasher import xxh128 as substrate_xxh128
from dipdup.abi.substrate import decode_arg
from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
from scalecodec import GenericExtrinsic
from scalecodec import ScaleBytes

from reserves.types.hydradx.substrate_events.sudo_sudid import SudoSudidPayload

known = []


@cache
def get_prefix_hashes() -> tuple[dict[str, str], dict[str, str]]:
    pallet_xxs = {}
    storage_xxs = {}

    metadata_path = Path(__file__).parent.parent.parent / 'abi' / 'hydradx' / 'v313.json'
    metadata = orjson.loads(metadata_path.read_bytes())

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
        # Check for set_storage call in the new format
        if obj.get('call_function') == 'set_storage' and obj.get('call_module') == 'System':
            results.append(obj)
        # Check nested 'call' and 'call_args'
        if 'call' in obj:
            results.extend(extract_set_storage_calls(obj['call']))
        if 'call_args' in obj:
            results.extend(extract_set_storage_calls(obj['call_args']))
        # Also check 'value' and 'params' for completeness
        for key in ['value', 'params']:
            if key in obj:
                results.extend(extract_set_storage_calls(obj[key]))
    elif isinstance(obj, list):
        for item in obj:
            results.extend(extract_set_storage_calls(item))
    return results


def parse_set_storage_params(
    set_storage_call: dict,
    metadata: list,
) -> tuple[str, Any]:
    key = set_storage_call['call_args'][0]['value'][0][0]
    set_storage_call['call_args'][0]['value'][0][1]
    key_bytes = bytes.fromhex(key[2:])
    # value_bytes = bytes.fromhex(value)

    pallet_xxs, storage_xxs = get_prefix_hashes()

    pallet_prefix = key_bytes[:16].hex()
    storage_prefix = key_bytes[16:32].hex()
    key_bytes[32:].hex()

    storage_name = storage_xxs[storage_prefix]
    pallet_name = pallet_xxs[pallet_prefix]

    path = f'{pallet_name}.{storage_name}'
    if path not in known:
        known.append(path)
        print(f'New storage path: {path}')


async def on_sudo_sudid(
    ctx: HandlerContext,
    event: SubstrateEvent[SudoSudidPayload],
) -> None:
    extrinsic_index = f'{event.data.block_number}-{event.data.extrinsic_index}'

    node = ctx.get_substrate_datasource('node')

    def decode(t, v):
        return decode_arg(
            runtime_config=node._interface.runtime_config,
            value=ScaleBytes(v),
            type_=t,
            full_type=t,
        )

    # Use node to get extrinsic params
    ext_params = await node._interface.retrieve_extrinsic_by_identifier(extrinsic_index)
    await ext_params.retrieve_extrinsic()
    ext_params = ext_params.extrinsic
    # print(f'Processing sudo_sudid extrinsic: {ext_params}')

    set_storage_calls = extract_set_storage_calls(ext_params)
    print(f'Found {len(set_storage_calls)} set_storage calls in sudo_sudid extrinsic: {extrinsic_index}')

    for call in set_storage_calls:
        parse_set_storage_params(call, node._interface.metadata)
