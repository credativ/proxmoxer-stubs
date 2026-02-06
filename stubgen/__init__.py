import keyword
import re
import textwrap

from dataclasses import dataclass
from functools import cached_property
from typing import Any, Callable, Literal, Optional, Self, TypeAlias, Union, assert_never

import pydantic
from jinja2 import Template

LATEST = 'v9'

ApiSchemaItemInfoMethodReturns: TypeAlias = Union[
    "ApiSchemaItemInfoMethodReturnsAny",
    "ApiSchemaItemInfoMethodReturnsArray",
    "ApiSchemaItemInfoMethodReturnsBoolean",
    "ApiSchemaItemInfoMethodReturnsInteger",
    "ApiSchemaItemInfoMethodReturnsNull",
    "ApiSchemaItemInfoMethodReturnsNumber",
    "ApiSchemaItemInfoMethodReturnsObject",
    "ApiSchemaItemInfoMethodReturnsString",
]

from .patches import Patch

def render(template: str, *args: Any, **kwargs: Any) -> str:
    return Template(textwrap.dedent(template)).render(
        str=str, repr=repr, *args, **kwargs
    )


class Code(pydantic.BaseModel):
    head: str = ""
    tail: str = ""

    def headcode(self, indent: bool = False) -> str:
        return textwrap.indent(self.head, "    " if indent else "")

    def tailcode(self, indent: bool = False) -> str:
        return textwrap.indent(self.tail, "    " if indent else "")

    def __str__(self) -> str:
        return self.head + self.tail


class Path(pydantic.BaseModel):

    class Segment(pydantic.BaseModel):
        orig: str

        @staticmethod
        def free(name: str) -> str:
            reserved = (*keyword.kwlist, *pydantic.BaseModel.__dict__.keys())
            while name in reserved:
                name = name + "_"
            return name

        @cached_property
        def is_param(self) -> bool:
            return bool(re.fullmatch("[{].+[}]", self.orig))

        @cached_property
        def as_param(self) -> str:
            match = re.fullmatch("[{](.+)[}]", self.orig)
            if not match:
                raise RuntimeError(f"{self} is not a param")
            return match.group(1)

        @cached_property
        def as_property(self) -> str:
            param = re.sub(r"[^a-zA-Z0-9-_]", "", self.orig)
            param = re.sub(r"-", "_", param)
            param = re.sub("([a-z])([A-Z])", r"\1_\2", param).lower()
            return self.free(param)

        @property
        def as_class(self) -> str:
            klass = re.sub(r"[^a-zA-Z0-9-_]", "", self.orig)
            klass = re.sub(r"-", "_", klass)
            klass = re.sub("([a-z])([A-Z])", r"\1_\2", klass).lower()
            klass = "".join(part.capitalize() for part in klass.split("_"))
            return self.free(klass)

        def __str__(self) -> str:
            return self.as_property

        def __eq__(self, value: Any) -> bool:
            if isinstance(value, Path):
                return self.orig == value.orig
            elif isinstance(value, str):
                return self.orig == value
            else:
                return False

    class CodeSegment(Segment):
        @cached_property
        def is_param(self) -> bool:
            return False

        @cached_property
        def as_param(self) -> str:
            raise RuntimeError(f"{self} is not a param")

        @property
        def as_class(self) -> str:
            return "_" + super().as_class

    orig: str
    segments: list[Segment]

    @property
    def params(self) -> list[Segment]:
        return [segment for segment in self.segments if segment.is_param]

    def __getitem__(self, index: int) -> Segment:
        return self.segments[index]

    def __str__(self) -> str:
        return self.orig

    def __eq__(self, value: Any) -> bool:
        if isinstance(value, Path):
            return self.orig == value.orig
        if isinstance(value, str):
            return self.orig == value
        return False

    def __repr__(self) -> str:
        ret = ""
        for segment in self.segments:
            if isinstance(segment, Path.CodeSegment):
                ret += "." + segment.as_class
            elif segment.is_param:
                ret += "/{" + segment.as_property + "}"
            else:
                ret += "/" + segment.orig
        return repr(ret)

    @property
    def as_classpath(self) -> str:
        return "ProxmoxAPI." + ".".join(segment.as_class for segment in self.segments)

    @property
    def rendered_call(self) -> str:
        render = ""
        params = (f"self.{param.as_property}" for param in self.params)
        for segment in self.segments:
            if isinstance(segment, self.CodeSegment):
                continue
            if segment.is_param:
                render += f"({next(params)})"
            elif render:
                render += f".{segment.as_property}"
            else:
                render = segment.as_property
        return render

    def copy_append(self, segment: Segment) -> Self:
        copy = self.model_copy(deep=False)
        copy.segments = self.segments.copy()
        copy.segments.append(segment)
        return copy

    @classmethod
    def new(cls, path: str) -> Self:
        return cls(
            orig=path,
            segments=[cls.Segment(orig=orig) for orig in path.split("/")[1:]]
        )


class Return(pydantic.BaseModel):
    code: Code | None = None
    optional: bool
    primitive: bool = True
    dicttype: str
    modeltype: str


@dataclass
class Field:
    name: str
    ret: Return

    def for_typeddict(self) -> str:
        if self.ret.optional:
            return f"{repr(self.name)}: NotRequired[{self.ret.dicttype}]"
        else:
            return f"{repr(self.name)}: {self.ret.dicttype}"

    def for_model(self) -> str:
        name_as_property = Path.Segment(orig=self.name).as_property
        if self.name == name_as_property:
            if self.ret.optional:
                return f"{self.name}: Optional[{self.ret.modeltype}] = None"

            else:
                return f"{self.name}: {self.ret.modeltype}"
        else:
            if self.ret.optional:
                return f"{name_as_property}: Optional[{self.ret.modeltype}] = pydantic.Field(alias={repr(self.name)}, default=None)"
            else:
                return f"{name_as_property}: {self.ret.modeltype} = pydantic.Field(alias={repr(self.name)})"


class BaseModel(pydantic.BaseModel):
    optional: bool = False

    def _dump(self, path: Path, optional: bool, type: str, param_type: Callable[[str], str | None]) -> Return:
        code = Code(
            head = render(
                """
                @dataclass
                class {{ path[-1].as_class }}:
                    proxmox_api: ProxmoxerProxmoxAPI
                {% if path.params %}
                {%   for param in path.params %}
                    {{ param }}: {{ param_type(param.as_param) }}
                {%   endfor %}
                {% endif %}
                    def __call__(self, *args: Any, **kwargs: Any) -> {{ dicttype }}:
                        return self.proxmox_api.{{ path.rendered_call }}.{{ path[-1] }}(*args, **kwargs)

                    def model(self, *args: Any, **kwargs: Any) -> {{ modeltype }}:
                        class validate(pydantic.BaseModel):
                            data: {{ modeltype }}
                        data: Any = self.proxmox_api.{{ path.rendered_call }}.{{ path[-1] }}(*args, **kwargs)
                        return validate(data=data).data
                """,
                path=path,
                dicttype=type,
                modeltype=type,
                param_type=param_type,
            ),
            tail=render(
                """
                @cached_property
                def {{ path[-1] }}(self) -> {{ path[-1].as_class }}:
                    return self.{{ path[-1].as_class }}(
                        proxmox_api=self.proxmox_api,
                {%   if path.params %}
                {%     for param in path.params %}
                        {{ param }}=self.{{ param }},
                {%-    endfor %}
                {%-  endif %}
                    )
                {% if path[-1] == "post" -%}
                @property
                def create(self) -> {{ path[-1].as_class }}: return self.{{ path[-1] }}
                {% elif path[-1] == "put" -%}
                @property
                def set(self) -> {{ path[-1].as_class }}: return self.{{ path[-1] }}
                {% endif -%}
                """,
                path=path,
                type=type,
            )
        )
        return Return(code=code, optional=optional, primitive=True, dicttype=type, modeltype=type)


class ApiSchemaItemInfoMethodReturnsString(BaseModel):
    type: Literal["string"]
    enum: list[str] | None = None

    def dump(self, path: Path, name: str, param_type: Callable[[str], str | None], **kwargs: Any) -> Return:
        path = path.copy_append(Path.CodeSegment(orig=name))
        if self.enum:
            return self._dump(path=path, optional=self.optional, param_type=param_type, type=f"Literal{repr(self.enum)}")
        else:
            return self._dump(path=path, optional=self.optional, param_type=param_type, type="str")


class ApiSchemaItemInfoMethodReturnsInteger(BaseModel):
    type: Literal["integer"]

    def dump(self, path: Path, name: str, param_type: Callable[[str], str | None], **kwargs: Any) -> Return:
        path = path.copy_append(Path.CodeSegment(orig=name))
        return self._dump(path=path, optional=self.optional, param_type=param_type, type="int")


class ApiSchemaItemInfoMethodReturnsNumber(BaseModel):
    type: Literal["number"]

    def dump(self, path: Path, name: str, param_type: Callable[[str], str | None], **kwargs: Any) -> Return:
        path = path.copy_append(Path.CodeSegment(orig=name))
        return self._dump(path=path, optional=self.optional, param_type=param_type, type="float")


class ApiSchemaItemInfoMethodReturnsBoolean(BaseModel):
    type: Literal["boolean"]

    def dump(self, path: Path, name: str, param_type: Callable[[str], str | None], **kwargs: Any) -> Return:
        path = path.copy_append(Path.CodeSegment(orig=name))
        return self._dump(path=path, optional=self.optional, param_type=param_type, type="bool")


class ApiSchemaItemInfoMethodReturnsNull(BaseModel):
    type: Literal["null"]

    def dump(self, path: Path, name: str, param_type: Callable[[str], str | None], **kwargs: Any) -> Return:
        path = path.copy_append(Path.CodeSegment(orig=name))
        return self._dump(path=path, optional=self.optional, param_type=param_type, type="None")


class ApiSchemaItemInfoMethodReturnsAny(BaseModel):
    type: Literal["any"]

    def dump(self, path: Path, name: str, param_type: Callable[[str], str | None], **kwargs: Any) -> Return:
        path = path.copy_append(Path.CodeSegment(orig=name))
        return self._dump(path=path, optional=self.optional, param_type=param_type, type="Any")


class ApiSchemaItemInfoMethodReturnsArray(BaseModel):
    type: Literal["array"]
    items: Optional[ApiSchemaItemInfoMethodReturns] = None

    def dump(
        self,
        path: Path,
        name: str,
        patch: Patch,
        param_type: Callable[[str], str | None],
        call_type: Callable[[str], str] = lambda x:x,
        call: bool = False,
    ) -> Return:
        patch(self).hook()
        if self.items:
            child = self.items.dump(path=path, name=name, patch=patch(self), param_type=param_type, call_type=lambda x: f"list[{x}]", call=call)
            if child.primitive:
                head = render(
                    """
                    @dataclass
                    class {{ path[-1].as_class }}:
                        proxmox_api: ProxmoxerProxmoxAPI
                    {% if path.params %}
                    {%   for param in path.params %}
                        {{ param }}: {{ param_type(param.as_param) }}
                    {%   endfor %}
                    {% endif %}
                        def __call__(self, *args: Any, **kwargs: Any) -> {{ dicttype }}:
                            return self.proxmox_api.{{ path.rendered_call }}.{{ path[-1] }}(*args, **kwargs)

                        def model(self, *args: Any, **kwargs: Any) -> {{ modeltype }}:
                            class validate(pydantic.BaseModel):
                                data: {{ modeltype }}
                            data: Any = self.proxmox_api.{{ path.rendered_call }}.{{ path[-1] }}(*args, **kwargs)
                            return validate(data=data).data
                    """,
                    path=path.copy_append(Path.CodeSegment(orig=name)),
                    dicttype=call_type(f"list[{child.dicttype}]"),
                    modeltype=call_type(f"list[{child.modeltype}]"),
                    param_type=param_type,
                )
            else:
                assert child.code
                head = child.code.head
            code = Code(
                head=head,
                tail=render(
                    """
                    @cached_property
                    def {{ path[-1] }}(self) -> {{ path[-1].as_class }}:
                        return self.{{ path[-1].as_class }}(
                            proxmox_api=self.proxmox_api,
                    {%   if path.params %}
                    {%     for param in path.params %}
                            {{ param }}=self.{{ param }},
                    {%-    endfor %}
                    {%-  endif %}
                        )
                    {% if path[-1] == "post" -%}
                    @property
                    def create(self) -> {{ path[-1].as_class }}: return self.{{ path[-1] }}
                    {% elif path[-1] == "put" -%}
                    @property
                    def set(self) -> {{ path[-1].as_class }}: return self.{{ path[-1] }}
                    {% endif -%}
                    """,
                    path=path.copy_append(Path.CodeSegment(orig=name)),
                ),
            )
            return Return(
                code=code,
                optional=self.optional,
                primitive=child.primitive,
                dicttype=f"list[{child.dicttype}]",
                modeltype=f"list[{child.modeltype}]",
            )
        else:
            path = path.copy_append(Path.CodeSegment(orig=name))
            code = Code(
                head=render(
                    """
                    @dataclass
                    class {{ path[-1].as_class }}:
                        proxmox_api: ProxmoxerProxmoxAPI
                    {% if path.params %}
                    {%   for param in path.params %}
                        {{ param }}: {{ param_type(param.as_param) }}
                    {%   endfor %}
                    {% endif %}
                        def __call__(self, *args: Any, **kwargs: Any) -> {{ dicttype }}:
                            return self.proxmox_api.{{ path.rendered_call }}.{{ path[-1] }}(*args, **kwargs)

                        def model(self, *args: Any, **kwargs: Any) -> {{ modeltype }}:
                            class validate(pydantic.BaseModel):
                                data: {{ modeltype }}
                            data: Any = self.proxmox_api.{{ path.rendered_call }}.{{ path[-1] }}(*args, **kwargs)
                            return validate(data=data).data
                    """,
                    path=path,
                    dicttype="list[Any]",
                    modeltype="list[Any]",
                    param_type=param_type,
                ),
                tail=render(
                    """
                    @cached_property
                    def {{ path[-1] }}(self) -> {{ path[-1].as_class }}:
                        return self.{{ path[-1].as_class }}(
                            proxmox_api=self.proxmox_api,
                    {%   if path.params %}
                    {%     for param in path.params %}
                            {{ param }}=self.{{ param }},
                    {%-    endfor %}
                    {%-  endif %}
                        )
                    {% if path[-1] == "post" -%}
                    @property
                    def create(self) -> {{ path[-1].as_class }}: return self.{{ path[-1] }}
                    {% elif path[-1] == "put" -%}
                    @property
                    def set(self) -> {{ path[-1].as_class }}: return self.{{ path[-1] }}
                    {% endif -%}
                    """,
                    path=path,
                ),
            )
            return Return(
                code=code, optional=self.optional, primitive=True, dicttype="list[Any]", modeltype="list[Any]",
            )


class ApiSchemaItemInfoMethodReturnsObject(BaseModel):
    type: Literal["object"] | None = None
    properties: dict[str, ApiSchemaItemInfoMethodReturns] | None = None
    values: ApiSchemaItemInfoMethodReturns | None = None

    def dump(
        self,
        path: Path,
        name: str,
        patch: Patch,
        param_type: Callable[[str], str | None],
        call_type: Callable[[str], str] = lambda x:x,
        call: bool = False,
    ) -> Return:
        patch(self).hook()
        if self.properties:
            path = path.copy_append(Path.CodeSegment(orig=name))
            returns: dict[str, Return] = {
                key: prop.dump(path=path, name=key, patch=patch(self, name=key), param_type=param_type) for key, prop in self.properties.items()
            }
            code = Code(
                head=render(
                    """
                    @dataclass
                    class {{ path[-1].as_class }}:
                    {%- for return in returns.values() %}{% if not return.primitive %}{{ return.code.headcode(indent=True) }}{% endif %}{% endfor %}
                        TypedDict = typing.TypedDict('TypedDict', {
                    {%-    for retname, return in returns.items() %}
                            {{ Field(name=retname, ret=return).for_typeddict() }},
                    {%-   endfor %}
                        })
                        class Model(pydantic.BaseModel):
                    {%-    for retname, return in returns.items() %}
                            {{ Field(name=retname, ret=return).for_model() }}
                    {%-   endfor %}
                        Model.__name__ = {{ repr(path.as_classpath) }}

                        proxmox_api: ProxmoxerProxmoxAPI
                    {% if path.params %}
                    {%   for param in path.params %}
                        {{ param }}: {{ param_type(param.as_param) }}
                    {%   endfor %}
                    {% endif %}

                    {%- if call %}
                        def __call__(self, *args: Any, **kwargs: Any) -> {{ dicttype }}:
                            return self.proxmox_api.{{ path.rendered_call }}.{{ path[-1] }}(*args, **kwargs)

                        def model(self, *args: Any, **kwargs: Any) -> {{ modeltype }}:
                            class validate(pydantic.BaseModel):
                                data: {{ modeltype }}
                            data: Any = self.proxmox_api.{{ path.rendered_call }}.{{ path[-1] }}(*args, **kwargs)
                            return validate(data=data).data
                    {%- endif %}
                    """,
                    Field=Field,
                    path=path,
                    returns=returns,
                    call=call,
                    dicttype=call_type(repr(f"{ path.as_classpath }.TypedDict")),
                    modeltype=call_type(repr(f"{ path.as_classpath }.Model")),
                    param_type=param_type,
                ),
                tail=render(
                    """
                    @cached_property
                    def {{ path[-1] }}(self) -> {{ path[-1].as_class }}:
                        return self.{{ path[-1].as_class }}(
                            proxmox_api=self.proxmox_api,
                    {%   if path.params %}
                    {%     for param in path.params %}
                            {{ param }}=self.{{ param }},
                    {%-    endfor %}
                    {%-  endif %}
                        )
                    {% if path[-1] == "post" -%}
                    @property
                    def create(self) -> {{ path[-1].as_class }}: return self.{{ path[-1] }}
                    {% elif path[-1] == "put" -%}
                    @property
                    def set(self) -> {{ path[-1].as_class }}: return self.{{ path[-1] }}
                    {% endif -%}
                    """,
                    path=path,
                ),
            )
            return Return(
                code=code,
                optional=self.optional,
                primitive=False,
                dicttype=repr(f"{path.as_classpath}.TypedDict"),
                modeltype=repr(f"{path.as_classpath}.Model"),
            )
        elif self.values:
            values = self.values.dump(path=path, name=name, patch=patch(self), param_type=param_type)
            return Return(
                code=values.code,
                dicttype=f"dict[str, { values.dicttype }]",
                modeltype=f"dict[str, { values.modeltype }]",
                optional=self.optional,
                primitive=values.primitive,
            )
        else:
            path = path.copy_append(Path.CodeSegment(orig=name))
            code = Code(
                head=render(
                    """
                    @dataclass
                    class {{ path[-1].as_class }}:
                        proxmox_api: ProxmoxerProxmoxAPI
                    {% if path.params %}
                    {%   for param in path.params %}
                        {{ param }}: {{ param_type(param.as_param) }}
                    {%   endfor %}
                    {% endif %}
                        def __call__(self, *args: Any, **kwargs: Any) -> {{ dicttype }}:
                            return self.proxmox_api.{{ path.rendered_call }}.{{ path[-1] }}(*args, **kwargs)

                        def model(self, *args: Any, **kwargs: Any) -> {{ modeltype }}:
                            class validate(pydantic.BaseModel):
                                data: {{ modeltype }}
                            data: Any = self.proxmox_api.{{ path.rendered_call }}.{{ path[-1] }}(*args, **kwargs)
                            return validate(data=data).data
                    """,
                    path=path,
                    dicttype="dict[str, Any]",
                    modeltype="dict[str, Any]",
                    param_type=param_type,
                ),
                tail=render(
                    """
                    @cached_property
                    def {{ path[-1] }}(self) -> {{ path[-1].as_class }}:
                        return self.{{ path[-1].as_class }}(
                            proxmox_api=self.proxmox_api,
                    {%   if path.params %}
                    {%     for param in path.params %}
                            {{ param }}=self.{{ param }},
                    {%-    endfor %}
                    {%-  endif %}
                        )
                    {% if path[-1] == "post" -%}
                    @property
                    def create(self) -> {{ path[-1].as_class }}: return self.{{ path[-1] }}
                    {% elif path[-1] == "put" -%}
                    @property
                    def set(self) -> {{ path[-1].as_class }}: return self.{{ path[-1] }}
                    {% endif -%}
                    """,
                    path=path,
                ),
            )
            return Return(
                code=code, optional=self.optional, primitive=True, dicttype="dict[str, Any]", modeltype="dict[str, Any]",
            )


class ApiSchemaItemInfoMethodProperty(BaseModel):
    type: Literal["array", "boolean", "integer", "number", "string"]

    def __str__(self) -> str:
        if self.type == "array":
            return "list[Any]"
        elif self.type == "boolean":
            return "bool"
        elif self.type == "integer":
            return  "int"
        elif self.type == "number":
            return "float"
        elif self.type == "string":
            return "str"
        else:
            assert_never(self.type)

class ApiSchemaItemInfoMethodParameters(BaseModel):
    properties: dict[str, ApiSchemaItemInfoMethodProperty] | None = None


class ApiSchemaItemInfoMethod(BaseModel):
    method: str
    returns: ApiSchemaItemInfoMethodReturns
    parameters: ApiSchemaItemInfoMethodParameters

    def param_type(self, name: str) -> ApiSchemaItemInfoMethodProperty | None:
        return self.parameters.properties.get(name) if self.parameters.properties else None

    def dump(self, path: Path, method: str, patch: Patch) -> Code | None:
        def param_type(name: str) -> str | None:
            return str(self.param_type(name)) if self.param_type(name) else None
        return self.returns.dump(path=path, name=method, patch=patch(self), param_type=param_type, call=True).code


class ApiSchemaItemInfo(BaseModel):
    DELETE: ApiSchemaItemInfoMethod | None = None
    GET: ApiSchemaItemInfoMethod | None = None
    POST: ApiSchemaItemInfoMethod | None = None
    PUT: ApiSchemaItemInfoMethod | None = None

    def param_type(self, name: str) -> ApiSchemaItemInfoMethodProperty:
        for method in (self.DELETE, self.GET, self.POST, self.PUT):
            if method and (param_type := method.param_type(name)):
                return param_type
        raise RuntimeError(f"Parameter {name} not found")


    def dump(self, path: Path, patch: Patch) -> Code:
        codelist: list[Code] = []
        if self.DELETE and (code := self.DELETE.dump(path=path, method="delete", patch=patch(self))):
            codelist.append(code)
        if self.GET and (code := self.GET.dump(path=path, method="get", patch=patch(self))):
            codelist.append(code)
        if self.POST and (code := self.POST.dump(path=path, method="post", patch=patch(self))):
            codelist.append(code)
        if self.PUT and (code := self.PUT.dump(path=path, method="put", patch=patch(self))):
            codelist.append(code)
        return Code(
            head=render(
                """
                {% for code in codelist -%}
                {{   code.headcode(indent=False) }}
                {% endfor -%}
                {% for code in codelist -%}
                {{   code.tailcode(indent=False) }}
                {% endfor -%}
                """,
                codelist=codelist,
            )
        )


class ApiSchemaItem(BaseModel):
    children: list["ApiSchemaItem"] | None = None
    info: ApiSchemaItemInfo | None = None
    leaf: bool
    path: str
    text: str

    def dump(
        self,
        type_check_only: bool,
        patch: Patch,
        recurse: bool,
        return_prefix: str = "",
    ) -> Code:
        patch(self).hook()
        path = Path.new(self.path)
        return Code(
            head=render(
                """
                {% if recurse -%}
                # {{ path }}
                {%   if type_check_only %}@type_check_only{% else %}@dataclass{% endif %}
                class {{ path[-1].as_class }}:
                {%   if childcodes -%}
                {%     for code in childcodes -%}
                {{       code.headcode(indent=True) }}
                {%     endfor -%}
                {%   endif %}
                {%   if infodump -%}
                {{     infodump.headcode(indent=True) }}
                {%   endif %}
                    proxmox_api: ProxmoxerProxmoxAPI
                {%   if path.params %}
                {%     for param in path.params %}
                    {{   param }}: {% if info %}{{ info.param_type(param.as_param) }}{% else %}str{% endif %}
                {%-    endfor %}
                {%   endif %}
                {% endif %}
                {%- if path[-1].is_param %}
                def __post_init__(self) -> None:
                    @lru_cache
                    def cache({{ path[-1] }}: {% if info %}{{ info.param_type(path[-1].as_param) }}{% else %}str{% endif %}) -> {{ path.as_classpath }}:
                        return self.{{ path[-1].as_class }}(
                            proxmox_api=self.proxmox_api,
                            {{ path[-1] }}={{ path[-1] }},
                    {%   if path.params %}
                    {%     for param in path.params[:-1] %}
                            {{ param }}=self.{{ param }},
                    {%-    endfor %}
                    {%-  endif %}
                        )
                    self.__cache = cache
                def __call__(self, {{ path[-1] }}: {% if info %}{{ info.param_type(path[-1].as_param) }}{% else %}str{% endif %}) -> {{ path[-1].as_class }}:
                    return self.__cache({{ path[-1] }})
                {%- else %}
                @cached_property
                {%    if type_check_only -%}
                @type_check_only
                def {{ path[-1] }}(self) -> {% if return_prefix %}{{ return_prefix }}{% endif %}{{ path[-1].as_class }}: ...
                {%    else -%}
                def {{ path[-1] }}(self) -> {% if return_prefix %}{{ return_prefix }}{% endif %}{{ path[-1].as_class }}:
                    return self.{{ path[-1].as_class }}(
                        proxmox_api=self.proxmox_api,
                {%   if path.params %}
                {%     for param in path.params %}
                        {{ param }}=self.{{ param }},
                {%-    endfor %}
                {%-  endif %}
                    )
                {%    endif -%}
                {% endif -%}
                """,
                childcodes=(child.dump(type_check_only=type_check_only, recurse=True, patch=patch) for child in self.children) if self.children else None,
                info=self.info,
                infodump=self.info.dump(path=path, patch=patch(self)) if self.info else None,
                path=path,
                recurse=recurse,
                type_check_only=type_check_only,
                return_prefix=return_prefix,
            ),
        )


class ApiSchema(BaseModel):
    children: list[ApiSchemaItem]

    def stubs(self, patch: Patch, apiversion: str) -> Code:
        return Code(
            head=render(
                """
                __license__ = "MIT"

                import builtins
                import typing
                from functools import cached_property
                from typing import Any, Literal, NotRequired, type_check_only
                from _typeshed import Incomplete

                import proxmoxer_types.{{ LATEST }} as latest

                logger: Incomplete
                ANYEVENT_HTTP_STATUS_CODES: Incomplete
                SERVICES: Incomplete

                def config_failure(message: Incomplete, *args: Incomplete) -> None: ...
                
                class ResourceException(Exception):
                    status_code: Incomplete
                    status_message: Incomplete
                    content: Incomplete
                    errors: Incomplete
                    def __init__(self, status_code: Incomplete, status_message: Incomplete, content: Incomplete, errors: Incomplete | None = None) -> None: ...
                
                class AuthenticationError(Exception): ...

                class ProxmoxResource:
                    def __init__(self, **kwargs: Incomplete) -> None: ...
                    def __getattr__(self, item: Incomplete) -> Incomplete: ...
                    def url_join(self, base: Incomplete, *args: Incomplete) -> Incomplete: ...
                    def __call__(self, resource_id: Incomplete | None = None) -> Incomplete: ...
                    def get(self, *args: Incomplete, **params: Incomplete) -> Incomplete: ...
                    def post(self, *args: Incomplete, **data: Incomplete) -> Incomplete: ...
                    def put(self, *args: Incomplete, **data: Incomplete) -> Incomplete: ...
                    def delete(self, *args: Incomplete, **params: Incomplete) -> Incomplete: ...
                    def create(self, *args: Incomplete, **data: Incomplete) -> Incomplete: ...
                    def set(self, *args: Incomplete, **data: Incomplete) -> Incomplete: ...

                class ProxmoxAPI:
                    def __init__(self, host: Incomplete | None = None, backend: str = 'https', service: str = 'PVE', **kwargs: Incomplete) -> None: ...
                    def get_tokens(self) -> Incomplete: ...

                {% for code in childcodes -%}
                {{  code.headcode(indent=True) }}
                {% endfor -%}
                """,
                LATEST=LATEST,
                childcodes=(
                    child.dump(
                        patch=patch,
                        recurse=False,
                        return_prefix='latest.ProxmoxAPI.',
                        type_check_only=True,
                    ) for child in self.children
                ),
            )
        )

    def types(self, patch: Patch, apiversion: str) -> Code:
        return Code(
            head=render(
                """
                import builtins
                import proxmoxer
                import pydantic
                import typing
                from dataclasses import dataclass
                from functools import cached_property, lru_cache
                from typing import Any, Literal, Optional, NotRequired, TYPE_CHECKING

                if TYPE_CHECKING:
                    from ..{{ apiversion }} import ProxmoxAPI as ProxmoxerProxmoxAPI
                else:
                    from proxmoxer import ProxmoxAPI as ProxmoxerProxmoxAPI

                class ProxmoxAPI:
                    proxmox_api: ProxmoxerProxmoxAPI
                    def __init__(self, *args: Any, **kwargs: Any) -> None:
                        self.proxmox_api = ProxmoxerProxmoxAPI(*args, **kwargs)

                {% for code in childcodes -%}
                {{  code.headcode(indent=True) }}
                {% endfor -%}
                """,
                apiversion=apiversion,
                childcodes=(child.dump(type_check_only=False, recurse=True, patch=patch) for child in self.children),
            )
        )
