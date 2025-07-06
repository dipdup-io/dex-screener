import logging
from functools import cache
from typing import TYPE_CHECKING
from typing import Any
from typing import cast

import orjson
from aiosubstrate import SubstrateInterface

# NOTE: It's not an original xxhash, but a custom implementation
from aiosubstrate.utils.hasher import xxh128 as substrate_xxh128
from dipdup.context import HandlerContext
from dipdup.env import get_package_path
from dipdup.models.substrate import SubstrateEvent
from dipdup.models.substrate import SubstrateEventData
from scalecodec import GenericExtrinsic  # type: ignore[import-untyped]
from scalecodec import ScaleBytes

from reserves.types.hydradx.substrate_events.balances_balance_set.v100 import V100 as BalancesBalanceSetPayload
from reserves.types.hydradx.substrate_events.sudo_sudid import SudoSudidPayload

if TYPE_CHECKING:
    from dipdup.datasources.substrate_node import SubstrateNodeDatasource

_logger = logging.getLogger(__name__)

_processed_extrinsics = set()

_storage_filter = (('System', 'Account'),)

# NOTE: highest MAX_ID where (((MAX_INT << 16) + MAX_ID) << 1) + 1 < MAX_INT; MAX_INT = (2**63) - 1
MAX_ID = (2**16) - 1


async def on_sudo_sudid(
    ctx: HandlerContext,
    event: SubstrateEvent[SudoSudidPayload],
) -> None:
    extrinsic_index = f'{event.data.block_number}-{event.data.extrinsic_index}'

    # NOTE: Multiple `Sudo.Sudid` events can be emitted in one block
    if extrinsic_index in _processed_extrinsics:
        return

    node = cast('SubstrateNodeDatasource', ctx.get_substrate_datasource('node'))

    await node._interface.init_runtime(block_id=event.level)
    try:
        extrinsic_reciept = await node._interface.retrieve_extrinsic_by_identifier(extrinsic_index)
        await extrinsic_reciept.retrieve_extrinsic()
    except ValueError as e:
        ctx.logger.error(
            'Failed to retrieve extrinsic %s: %s',
            extrinsic_index,
            e,
        )
        return
    extrinsic = extrinsic_reciept.extrinsic

    set_storage_calls = extract_set_storage_calls(extrinsic)
    if not set_storage_calls:
        return

    ctx.logger.info(
        'Found %s `set_storage` calls in extrinsic emitted Sudo.Sudid: %s', len(set_storage_calls), extrinsic_index
    )

    for artificial_event_index, call in enumerate(set_storage_calls):
        raw_key = call['call_args'][0]['value'][0][0]
        raw_value = call['call_args'][0]['value'][0][1]

        key, value = await decode_set_storage_call(node._interface, raw_key, raw_value)
        if not key:
            continue

        free = value['data']['free'].value if value else 0
        reserved = value['data']['reserved'].value if value else 0

        decoded_args = BalancesBalanceSetPayload(
            who=key.value,
            free=free,
            reserved=reserved,
        )

        # NOTE: temporate hack
        event_id = MAX_ID - event.data.index - artificial_event_index
        new_event_data = SubstrateEventData(
            **{
                **event.data.__dict__,
                'index': event_id,
                'decoded_args': decoded_args,
                'args': None,
            }
        )

        new_event: Any = SubstrateEvent(
            data=new_event_data,
            runtime=event.runtime,
        )
        await ctx.fire_handler(
            name='hydradx.balances.on_balance_set',
            index='hydradx_events',
            args=(new_event,),
        )

    _processed_extrinsics.add(extrinsic_index)


async def decode_set_storage_call(
    self: SubstrateInterface,
    key: str,
    value: str,
) -> tuple[Any | Any, Any | None]:
    module, storage_function, key = parse_set_storage_key(key)
    if (module, storage_function) not in _storage_filter:
        return (None, None)

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

    if '\x00' in value:
        value = '0x' + bytes(value, 'utf-8').hex()

    item_value = self.runtime_config.create_scale_object(
        type_string=value_type,
        data=ScaleBytes(value),
        metadata=self.metadata,
    )
    item_value.decode()
    item_value = item_value.value_object

    return (item_key, item_value)


@cache
def get_prefix_hashes() -> dict[str, str]:
    # FIXME: hardcode
    metadata_path = get_package_path('dex_screener') / 'abi' / 'hydradx' / 'v313.json'
    metadata = orjson.loads(metadata_path.read_bytes())

    xx_hashes = {}

    for pallet in metadata:
        name = pallet['name']
        hash_hex = substrate_xxh128(name).hex()
        xx_hashes[hash_hex] = name

        for storage in pallet.get('storage') or []:
            storage_name = storage['name']
            storage_hash_hex = substrate_xxh128(storage_name).hex()
            xx_hashes[storage_hash_hex] = storage_name

    return xx_hashes


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


def parse_set_storage_key(key: str) -> tuple[str, str, str]:
    prefix_hashes = get_prefix_hashes()
    key_bytes = bytes.fromhex(key[2:])

    pallet_prefix = key_bytes[:16].hex()
    storage_prefix = key_bytes[16:32].hex()
    rest = key_bytes[32:].hex()

    return (
        prefix_hashes[pallet_prefix],
        prefix_hashes[storage_prefix],
        rest,
    )
