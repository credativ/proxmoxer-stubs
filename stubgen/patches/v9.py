from typing import Any
from . import Patch as BasePatch
from .. import (
    ApiSchemaItemInfoMethodReturns,
    ApiSchemaItemInfoMethodReturnsArray,
    ApiSchemaItemInfoMethodReturnsBoolean,
    ApiSchemaItemInfoMethodReturnsBoolint,
    ApiSchemaItemInfoMethodReturnsInteger,
    ApiSchemaItemInfoMethodReturnsNumber,
    ApiSchemaItemInfoMethodReturnsObject,
    ApiSchemaItemInfoMethodReturnsString,
)

__all__ = ["Patch"]

# RRD fields from pve-cluster.git src/pmxcfs/status.c

RRDDATA_DS_NODE: tuple[str, ...] = (
    "loadavg",
    "maxcpu",
    "cpu",
    "iowait",
    "memtotal",
    "memused",
    "swaptotal",
    "swapused",
    "roottotal",
    "rootused",
    "netin",
    "netout",
    "memavailable",
    "arcsize",
    "pressurecpusome",
    "pressureiosome",
    "pressureiofull",
    "pressurememorysome",
    "pressurememoryfull",
    # "memavailable" was named "memfree" when the pve9 format was introduced and
    # renamed shortly after; create_rrd_data() still reads such files and passes
    # the original name through next to the renamed one.
    "memfree",
)

RRDDATA_DS_VM: tuple[str, ...] = (
    "maxcpu",
    "cpu",
    "maxmem",
    "mem",
    "maxdisk",
    "disk",
    "netin",
    "netout",
    "diskread",
    "diskwrite",
    "memhost",
    "pressurecpusome",
    "pressurecpufull",
    "pressureiosome",
    "pressureiofull",
    "pressurememorysome",
    "pressurememoryfull",
)

RRDDATA_DS_STORAGE: tuple[str, ...] = (
    "total",
    "used",
)


class Patch(BasePatch):
    def hook(self) -> None:
        obj = self.callpath[-1].call

        # /cluster/...

        if self == '/cluster/ha/rules.info.GET.array.object':
            print(f"{__name__}: Patching {self}: Add nodes, resources, type properties")
            assert isinstance(obj, ApiSchemaItemInfoMethodReturnsObject)
            assert isinstance(obj.properties, dict)
            obj.properties["affinity"] = ApiSchemaItemInfoMethodReturnsString(optional=True, type="string")
            obj.properties["disable"] = ApiSchemaItemInfoMethodReturnsBoolean(optional=True, type="boolean")
            obj.properties["strict"] = ApiSchemaItemInfoMethodReturnsBoolean(optional=True, type="boolean")
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

        if self == '/nodes/{node}/storage.info.GET.array.object':
            print(f'{__name__}: Patching {self}: Patching boolean to boolint')
            assert isinstance(obj, ApiSchemaItemInfoMethodReturnsObject)
            assert isinstance(obj.properties, dict)
            for prop in ('active', 'enabled'):
                obj.properties[prop] = ApiSchemaItemInfoMethodReturnsBoolint(
                    type='boolint',
                    optional=obj.properties[prop].optional,
                )

        # The documentation declares an rrddata row as an object without any
        # properties at all. The keys it actually carries are the RRD data
        # sources, which differ between nodes, guests and storages.
        if self in (
            '/nodes/{node}/rrddata.info.GET.array',
            '/nodes/{node}/qemu/{vmid}/rrddata.info.GET.array',
            '/nodes/{node}/lxc/{vmid}/rrddata.info.GET.array',
            '/nodes/{node}/storage/{storage}/rrddata.info.GET.array',
        ):
            print(f"{__name__}: Patching {self}: Define rrddata")
            assert isinstance(obj, ApiSchemaItemInfoMethodReturnsArray)
            assert isinstance(obj.items, ApiSchemaItemInfoMethodReturnsObject)

            if self == '/nodes/{node}/rrddata.info.GET.array':
                data_sources = RRDDATA_DS_NODE
            elif self == '/nodes/{node}/storage/{storage}/rrddata.info.GET.array':
                data_sources = RRDDATA_DS_STORAGE
            else:
                data_sources = RRDDATA_DS_VM

            obj.items.values = None
            obj.items.properties = {
                "time": ApiSchemaItemInfoMethodReturnsInteger(optional=False, type="integer"),
                **{
                    name: ApiSchemaItemInfoMethodReturnsNumber(optional=True, type="number")
                    for name in data_sources
                },
            }
