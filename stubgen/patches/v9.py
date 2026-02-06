from typing import Any
from . import Patch as BasePatch
from .. import (
    ApiSchemaItemInfoMethodReturns,
    ApiSchemaItemInfoMethodReturnsArray,
    ApiSchemaItemInfoMethodReturnsInteger,
    ApiSchemaItemInfoMethodReturnsNumber,
    ApiSchemaItemInfoMethodReturnsObject,
    ApiSchemaItemInfoMethodReturnsString,
)

__all__ = ["Patch"]

class Patch(BasePatch):
    def hook(self) -> None:
        obj = self.callpath[-1].call

        # /cluster/...

        if self == '/cluster/ha/rules.info.GET.array.object':
            print(f"{__name__}: Patching {self}: Add nodes, resources, type properties")
            assert isinstance(obj, ApiSchemaItemInfoMethodReturnsObject)
            assert isinstance(obj.properties, dict)
            obj.properties["nodes"] = ApiSchemaItemInfoMethodReturnsString(optional=True, type="string")
            obj.properties["resources"] = ApiSchemaItemInfoMethodReturnsString(optional=True, type="string")
            obj.properties["type"] = ApiSchemaItemInfoMethodReturnsString(optional=False, type="string")


        if self == '/cluster/ha/status/current.info.GET.array.object':
            print(f"{__name__}: Patching {self}: Specify type property as string")
            assert isinstance(obj, ApiSchemaItemInfoMethodReturnsObject)
            assert isinstance(obj.properties, dict)
            obj.properties["type"] = ApiSchemaItemInfoMethodReturnsString(optional=False, type="string", enum=["quorum", "master", "lrm", "service"])

        # /nodes/...

        if self == '/nodes.info.GET.array.object':
            print(f"{__name__}: Patching {self}: Add disk and maxdisk propertries")
            assert isinstance(obj, ApiSchemaItemInfoMethodReturnsObject)
            assert isinstance(obj.properties, dict)
            obj.properties["disk"] = ApiSchemaItemInfoMethodReturnsInteger(optional=True, type="integer")
            obj.properties["maxdisk"] = ApiSchemaItemInfoMethodReturnsInteger(optional=True, type="integer")

        if self == "/pools/{poolid}.info.GET.object[members].array.object":
            print(f"{__name__}: Patching {self}: Add name property")
            assert isinstance(obj, ApiSchemaItemInfoMethodReturnsObject)
            assert isinstance(obj.properties, dict)
            obj.properties["name"] = ApiSchemaItemInfoMethodReturnsString(optional=False, type="string")

        if self == "/nodes/{node}/qemu.info.GET.array.object":
            print(f"{__name__}: Patching {self}: Add disk property")
            assert isinstance(obj, ApiSchemaItemInfoMethodReturnsObject)
            assert isinstance(obj.properties, dict)
            obj.properties["disk"] = ApiSchemaItemInfoMethodReturnsInteger(optional=True, type="integer")

        # Returned data is not a dict with fields as specified but a dict whose values are a dict as specified
        if self == "/nodes/{node}/qemu/{vmid}/migrate.info.GET.object":
            print(f"{__name__}: Patching {self}: Modify node_allowed_nodes property")
            assert isinstance(obj, ApiSchemaItemInfoMethodReturnsObject)
            assert isinstance(obj.properties, dict)
            obj.properties["not_allowed_nodes"] = ApiSchemaItemInfoMethodReturnsObject(
                optional=True,
                type="object",
                values=obj.properties["not_allowed_nodes"],
            )

        if self == '/nodes/{node}/apt/repositories.info.GET.object[infos].array.object':
            print(f"{__name__}: Patching {self}: Fixing index property from string to integer")
            assert isinstance(obj, ApiSchemaItemInfoMethodReturnsObject)
            assert isinstance(obj.properties, dict)
            obj.properties["index"] = ApiSchemaItemInfoMethodReturnsInteger(optional=False, type="integer")

        if self == '/nodes/{node}/rrddata.info.GET.array':
            print(f"{__name__}: Patching {self}: Define rrddata")
            assert isinstance(obj, ApiSchemaItemInfoMethodReturnsArray)
            assert isinstance(obj.items, ApiSchemaItemInfoMethodReturnsObject)
            obj.items.properties = None
            obj.items.values = ApiSchemaItemInfoMethodReturnsNumber(optional=False, type="number")
