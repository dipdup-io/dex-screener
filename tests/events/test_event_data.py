import pytest
from dipdup.models.substrate import SubstrateEvent
from service.event.dto import DexScreenerEventDataDTO
from service.event.event_service import DexScreenerEventService


@pytest.mark.parametrize('event, expected_event_data', [
    # (SubstrateEvent)
])
async def test_resolve_event_data(event: SubstrateEvent, expected_event_data: DexScreenerEventDataDTO):
    event_entity = DexScreenerEventService.build_swap_event_entity(event)
    event_data = await event_entity.resolve_event_data()
    assert event_data == expected_event_data
