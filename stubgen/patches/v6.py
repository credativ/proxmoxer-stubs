from typing import Any
from . import Patch as BasePatch
from .. import (
    Code,
    Path,
    ApiSchemaItem,
    ApiSchemaItemInfo,
    ApiSchemaItemInfoMethodProperty,
)

__all__ = ["Patch"]

class Patch(BasePatch):
    def hook(self) -> None:
        obj = self.callpath[-1].call

        # /nodes/...

        if self == "/nodes/{node}/qemu/{vmid}/cloudinit":
            print(f"{__name__}: Patching {self}: transform vmid type from str to int")
            assert isinstance(obj, ApiSchemaItem)
            assert obj.info is None

            class FakeInfo(ApiSchemaItemInfo):
                def dump(self, path: Path, patch: BasePatch) -> Code:
                    return Code()

                def param_type(self, name: str) -> ApiSchemaItemInfoMethodProperty:
                    if name == "vmid":
                        return ApiSchemaItemInfoMethodProperty(type="integer")
                    elif name == "node":
                        return ApiSchemaItemInfoMethodProperty(type="string")
                    else:
                        raise NotImplementedError(name)
            obj.info = FakeInfo()
