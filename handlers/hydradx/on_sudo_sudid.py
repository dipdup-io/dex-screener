from pathlib import Path
from dipdup.context import HandlerContext
from dipdup.models.substrate import SubstrateEvent
import orjson
from scalecodec import ScaleBytes
from dipdup.abi.substrate import decode_arg
from dex_screener import models as models
from dex_screener.types.hydradx.substrate_events.sudo_sudid import SudoSudidPayload


import json
import xxhash

from aiosubstrate.utils.hasher import xxh128

def twox_128(x):
    return xxh128(x).hex()

pallet_xxs  = {}
storage_xxs = {}


def get_prefixes():
    metadata_path = Path(__file__).parent.parent.parent / 'abi' / 'hydradx' / 'v313.json'
    metadata = orjson.loads(metadata_path.read_bytes())

    for pallet in metadata:
        name = pallet['name']
        hash_hex = twox_128(name)
        pallet_xxs[hash_hex] = name

        print(f"{name}: {hash_hex}")

        for storage in pallet.get('storage') or []:
            storage_name = storage['name']
            storage_hash_hex = twox_128(storage_name)
            storage_xxs[storage_hash_hex] = storage_name

            print(f"  {storage_name}: {storage_hash_hex}")

get_prefixes()
# quit()

def extract_set_storage_calls(obj):
    results = []
    if isinstance(obj, dict):
        # If this is a set_storage call, add it
        if obj.get("call_name") == "set_storage":
            results.append(obj)
        # Always check "params" and "value" keys for further nesting
        for key in ["params", "value"]:
            if key in obj:
                results.extend(extract_set_storage_calls(obj[key]))
    elif isinstance(obj, list):
        for item in obj:
            results.extend(extract_set_storage_calls(item))
    return results



async def on_sudo_sudid(
    ctx: HandlerContext,
    event: SubstrateEvent[SudoSudidPayload],
) -> None:
    # print(event.payload)
    extrinsic_index = f'{event.data.block_number}-{event.data.extrinsic_index}'

    subscan = ctx.get_substrate_datasource('subscan')
    node = ctx.get_substrate_datasource('node')

    def decode(t, v):
        return decode_arg(
            runtime_config=node._interface.runtime_config,
            value=ScaleBytes(v),
            type_=t,
            full_type=t,
        )
        

    ext_params = await subscan.request(
        'post',
        'scan/extrinsic/params',
        json={'extrinsic_index': [extrinsic_index]},
        weight=5,
    )
    ext_params = ext_params['data'][0]['params']


    set_storage_calls = extract_set_storage_calls(ext_params)

    for call in set_storage_calls:
        print(call)
        key, value = call['params'][0]['value'][0]['col1'], call['params'][0]['value'][0]['col2']


        key_bytes = bytes.fromhex(key)

        pallet_prefix = key_bytes[:16].hex()
        print('Pallet prefix:', pallet_prefix)
        print('Pallet name:', pallet_xxs.get(pallet_prefix, 'Unknown'))

        storage_prefix = key_bytes[16:32].hex()
        print('Storage prefix:', storage_prefix)
        print('Storage name:', storage_xxs.get(storage_prefix, 'Unknown'))
