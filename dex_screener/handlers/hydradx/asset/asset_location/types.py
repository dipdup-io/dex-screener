from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any
from typing import Self


class ScalarInteriorElement:
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}({super().__repr__()})>'


class Parachain(ScalarInteriorElement, int):
    pass


class PalletInstance(ScalarInteriorElement, int):
    pass


class GeneralIndex(ScalarInteriorElement, int):
    pass


class AccountKey20(ScalarInteriorElement, str):
    pass


class GeneralKey(ScalarInteriorElement, str):
    def __new__(cls, data: str, length: int | None = None, *args, **kwarg) -> type[Self]:
        if length is None:
            return str.__new__(cls, data)
        key: str = data[: 2 + length * 2]
        return str.__new__(cls, key)


class Here:
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}>'


class Interior(tuple):
    def __new__(cls, interior_data: tuple|str, *args, **kwargs) -> type[Self]:
        value = interior_data
        if isinstance(interior_data , tuple):
            value = tuple(cls.convert(element) for element in interior_data)
        elif interior_data == 'Here':
            value = Here()
        if not isinstance(value, Iterable):
            value = [value]
        return tuple.__new__(cls, value)

    @staticmethod
    def convert(element: dict[str, str | int]) -> Any:
        match element:
            case {'Parachain': int(parachain_id)}:
                return Parachain(parachain_id)
            case {'GeneralKey': {'data': str(key_hex_prefixed), 'length': int(key_length)}}:
                return GeneralKey(key_hex_prefixed, key_length)
            case {'GeneralKey': str(key_hex_prefixed)}:
                return GeneralKey(key_hex_prefixed)
            case {'GeneralIndex': str(index) | int(index)}:
                return GeneralIndex(int(index))
            case {'AccountKey20': str(key_hex_prefixed)}:
                return AccountKey20(key_hex_prefixed)
            case {'PalletInstance': int(pallet_id)}:
                return PalletInstance(pallet_id)
            case _:
                pass
        return element

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}[{super().__repr__()[1:-1]}]>'


@dataclass
class NativeLocation:
    interior: Interior
    parents: int

    def __post_init__(self):
        if isinstance(self.interior, tuple):
            self.interior = Interior(self.interior)


@dataclass
class AssetRegistryLocation:
    asset_id: int
    location: NativeLocation

    def __post_init__(self):
        if isinstance(self.location, dict):
            self.location = NativeLocation(**self.location)

    @classmethod
    def from_event(cls, payload: dict) -> type[Self]:
        decoded_interior = payload['location']['interior']
        if isinstance(decoded_interior, dict):
            assert len(decoded_interior) == 1
            _, payload['location']['interior'] = decoded_interior.popitem()
        return cls(**payload)
