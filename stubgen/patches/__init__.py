from dataclasses import dataclass, field
from typing import Any, Optional, Union, Self, TypeAlias

import stubgen

CallType: TypeAlias = Union[
    "stubgen.ApiSchemaItem",
    "stubgen.ApiSchemaItemInfo",
    "stubgen.ApiSchemaItemInfoMethod",
    "stubgen.ApiSchemaItemInfoMethodReturns",
]

@dataclass
class Patch:
    @dataclass
    class Call:
        call: CallType
        name: Optional[str] = None

        def __str__(self) -> str:
            if isinstance(self.call, stubgen.ApiSchemaItem):
                assert isinstance(self.call.path, str)
                return self.call.path
            elif isinstance(self.call, stubgen.ApiSchemaItemInfo):
                return "info"
            elif isinstance(self.call, stubgen.ApiSchemaItemInfoMethod):
                assert isinstance(self.call.method, str)
                return self.call.method
            else:
                type_: str = getattr(self.call, 'type') or ''
                return f"{type_}[{self.name}]" if self.name else type_

    callpath: list[Call] = field(default_factory=list)

    def hook(self) -> None:
        pass

    def __call__(self, head: CallType, name: Optional[str] = None) -> Self:
        return type(self)(callpath=[*self.callpath, self.Call(call=head, name=name)])

    def __repr__(self) -> str:
        return ".".join(str(call) for call in self.callpath)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Patch):
            return repr(self) == repr(value)
        elif isinstance(value, str):
            return repr(self) == value
        else:
            return False
