"""Type stubs for numpy.typing package"""
from typing import TypeVar, Generic
from typing_extensions import Protocol

_T = TypeVar("_T")

class NDArray(Protocol[_T]):
    """numpy配列の型定義"""
    pass

