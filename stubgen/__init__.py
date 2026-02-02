import keyword
import re
import textwrap
from functools import cached_property
from typing import Any, Literal, Optional, TypeAlias, Union, assert_never

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


class Path:
    orig: str

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

    segments: list[Segment]

    @property
    def params(self) -> list[Segment]:
        return [segment for segment in self.segments if segment.is_param]

    def __getitem__(self, index: int) -> Segment:
        return self.segments[index]

    def __str__(self) -> str:
        return self.orig

    def __repr__(self) -> str:
        ret = ""
        for segment in self.segments:
            if segment.is_param:
                ret += "/{" + segment.as_property + "}"
            else:
                ret += "/" + segment.orig
        return repr(ret)

    def repr(self) -> str:
        return self.__repr__()

    @property
    def as_classpath(self) -> str:
        return ".".join(segment.as_class for segment in self.segments)

    def __init__(self, path: str) -> None:
        self.orig = path
        self.segments = [self.Segment(orig=orig) for orig in path.split("/")[1:]]


class Return(pydantic.BaseModel):
    code: Code | None = None
    optional: bool
    primitive: bool = True
    type: str


class BaseModel(pydantic.BaseModel):
    optional: bool = False

    def _dump(
        self, path: Path, name: str, optional: bool, type_: str, sample: Any
    ) -> Return:
        code = Code(
            tail=render(
                """
                def {{ name }}(self, *args: Any, **kwargs: Any) -> {{ type }}: return {{ repr(sample) }}
                {% if str(name) == "post" -%}
                def create(self, *args: Any, **kwargs: Any) -> {{ type }}: return {{ repr(sample) }}
                {% elif str(name) == "put" -%}
                def set(self, *args: Any, **kwargs: Any) -> {{ type }}: return {{ repr(sample) }}
                {% endif -%}
                """,
                name=Path.Segment(orig=name),
                path=path,
                sample=sample,
                type=type_,
            )
        )
        return Return(code=code, optional=optional, primitive=True, type=type_)


class ApiSchemaItemInfoMethodReturnsString(BaseModel):
    type: Literal["string"]
    enum: list[str] | None = None

    def dump(self, path: Path, name: str) -> Return:
        if self.enum:
            return self._dump(path=path, name=name, optional=self.optional, type_=f"Literal{repr(self.enum)}", sample=self.enum[0])
        else:
            return self._dump(path=path, name=name, optional=self.optional, type_="str", sample="")


class ApiSchemaItemInfoMethodReturnsInteger(BaseModel):
    type: Literal["integer"]

    def dump(self, path: Path, name: str) -> Return:
        return self._dump(
            path=path, name=name, optional=self.optional, type_="int", sample=0
        )


class ApiSchemaItemInfoMethodReturnsNumber(BaseModel):
    type: Literal["number"]

    def dump(self, path: Path, name: str) -> Return:
        return self._dump(
            path=path, name=name, optional=self.optional, type_="float", sample=0.0
        )


class ApiSchemaItemInfoMethodReturnsBoolean(BaseModel):
    type: Literal["boolean"]

    def dump(self, path: Path, name: str) -> Return:
        return self._dump(
            path=path, name=name, optional=self.optional, type_="bool", sample=False
        )


class ApiSchemaItemInfoMethodReturnsNull(BaseModel):
    type: Literal["null"]

    def dump(self, path: Path, name: str) -> Return:
        return self._dump(
            path=path, name=name, optional=self.optional, type_="None", sample=None
        )


class ApiSchemaItemInfoMethodReturnsAny(BaseModel):
    type: Literal["any"]

    def dump(self, path: Path, name: str) -> Return:
        return self._dump(
            path=path, name=name, optional=self.optional, type_="Any", sample=None
        )


class ApiSchemaItemInfoMethodReturnsArray(BaseModel):
    type: Literal["array"]
    items: Optional[ApiSchemaItemInfoMethodReturns] = None

    def dump(self, path: Path, name: str) -> Return:
        if self.items:
            child = self.items.dump(path, name)
            code = Code(
                head=child.code.head if child.code else "",
                tail=render(
                    """
                    def {{ name }}(self, *args: Any, **kwargs: Any) -> builtins.list[{{ child.type }}]: return []
                    {% if str(name) == "post" -%}
                    def create(self, *args: Any, **kwargs: Any) -> builtins.list[{{ child.type }}]: return []
                    {% elif str(name) == "put" -%}
                    def set(self, *args: Any, **kwargs: Any) -> builtins.list[{{ child.type }}]: return []
                    {% endif -%}
                    """,
                    child=child,
                    name=Path.Segment(orig=name),
                ),
            )
            return Return(
                code=code,
                optional=self.optional,
                primitive=child.primitive,
                type=f"list[{child.type}]",
            )
        else:
            code = Code(
                tail=render(
                    """
                    def {{ name }}(self, *args: Any, **kwargs: Any) -> list[Any]: return []
                    {% if str(name) == "post" -%}
                    def create(self, *args: Any, **kwargs: Any) -> list[Any]: return []
                    {% elif str(name) == "put" -%}
                    def set(self, *args: Any, **kwargs: Any) -> list[Any]: return []
                    {% endif -%}
                    """,
                    name=Path.Segment(orig=name),
                )
            )
            return Return(
                code=code, optional=self.optional, primitive=True, type="list[Any]"
            )


class ApiSchemaItemInfoMethodReturnsObject(BaseModel):
    type: Literal["object"] | None = None
    properties: dict[str, ApiSchemaItemInfoMethodReturns] | None = None

    def dump(self, path: Path, name: str) -> Return:
        name_ = Path.Segment(orig=name)
        if self.properties:
            returns: dict[str, Return] = {
                name: prop.dump(path, name) for name, prop in self.properties.items()
            }
            code = Code(
                head=render(
                    """
                    class _{{ name.as_class }}:
                    {%- for name, return in returns.items() %}{% if return.code %}{{ return.code.headcode(indent=True) }}{% endif %}{% endfor %}
                        TypedDict = typing.TypedDict('TypedDict', {
                    {%-    for name, return in returns.items() %}
                            {{ name.__repr__() }}: {% if return.optional %}NotRequired[{{ return.type }}]{% else %}{{ return.type }}{% endif %},
                    {%-   endfor %}
                        })
                    """,
                    name=Path.Segment(orig=name),
                    path=path,
                    returns=returns,
                ),
                tail=render(
                    """
                    def {{ name }}(self, *args: Any, **kwargs: Any) -> _{{ name.as_class }}.TypedDict: return typing.cast(ProxmoxAPI.{{ path.as_classpath }}._{{ name.as_class }}.TypedDict, None)
                    {% if str(name) == "post" -%}
                    def create(self, *args: Any, **kwargs: Any) -> _{{ name.as_class }}.TypedDict: return typing.cast(ProxmoxAPI.{{ path.as_classpath }}._{{ name.as_class }}.TypedDict, None)
                    {% elif str(name) == "put" -%}
                    def set(self, *args: Any, **kwargs: Any) -> _{{ name.as_class }}.TypedDict: return typing.cast(ProxmoxAPI.{{ path.as_classpath }}._{{ name.as_class }}.TypedDict, None)
                    {% endif -%}
                    """,
                    name=name_,
                    path=path,
                ),
            )
            return Return(
                code=code,
                optional=self.optional,
                primitive=False,
                type=f"_{name_.as_class}.TypedDict",
            )
        else:
            code = Code(
                tail=render(
                    """
                    def {{ name }}(self, *args: Any, **kwargs: Any) -> dict[Any, Any]: return {}
                    {% if str(name) == "post" -%}
                    def create(self, *args: Any, **kwargs: Any) -> dict[Any, Any]: return {}
                    {% elif str(name) == "put" -%}
                    def set(self, *args: Any, **kwargs: Any) -> dict[Any, Any]: return {}
                    {% endif -%}
                    """,
                    name=name_,
                    path=path,
                )
            )
            return Return(
                code=code, optional=self.optional, primitive=True, type="dict[Any, Any]"
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

    def dump(self, path: Path, method: str) -> Code | None:
        return self.returns.dump(path, method).code


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


    def dump(self, path: Path) -> Code:
        codelist: list[Code] = []
        if self.DELETE and (code := self.DELETE.dump(path, "delete")):
            codelist.append(code)
        if self.GET and (code := self.GET.dump(path, "get")):
            codelist.append(code)
        if self.POST and (code := self.POST.dump(path, "post")):
            codelist.append(code)
        if self.PUT and (code := self.PUT.dump(path, "put")):
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
        self, type_check_only: bool, return_prefix: str = "", recurse: bool = True
    ) -> Code:
        return Code(
            head=render(
                """
                {% if recurse -%}
                # {{ path }}
                {%   if type_check_only %}@type_check_only{% endif %}
                class {{ path[-1].as_class }}:
                {%   if children -%}
                {%     for child in children -%}
                {{       child.dump(type_check_only).headcode(indent=True) }}
                {%     endfor -%}
                {%   endif -%}
                {%   if path.params %}
                {%     for param in path.params %}
                    {{   param }}: str
                {%-    endfor %}

                {%   endif %}
                {%   if info -%}
                {{     info.dump(path).headcode(indent=True) }}
                {%   endif -%}
                {% endif %}
                {%- if path[-1].is_param %}
                def __call__(self, {{ path[-1] }}: {% if info %}{{ info.param_type(path[-1].as_param) }}{% else %}str{% endif %}) -> {{ path[-1].as_class }}: return self.{{ path[-1].as_class }}()
                {%- else %}
                @cached_property
                {% if type_check_only %}@type_check_only{% endif %}
                def {{ path[-1] }}(self) -> {% if return_prefix %}{{ return_prefix }}{% endif %}{{ path[-1].as_class }}: {% if type_check_only %}...{% else %}return self.{{ path[-1].as_class }}(){% endif %}
                {% endif %}
                """,
                children=self.children,
                info=self.info,
                path=Path(self.path),
                recurse=recurse,
                type_check_only=type_check_only,
                return_prefix=return_prefix,
            ),
        )


class ApiSchema(BaseModel):
    children: list[ApiSchemaItem]

    def stubs(self) -> Code:
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

                {% for child in children -%}
                {{  child.dump(type_check_only=True, return_prefix='latest.ProxmoxAPI.', recurse=False).headcode(indent=True) }}
                {% endfor -%}
                """,
                children=self.children,
                LATEST=LATEST,
            )
        )

    def types(self) -> Code:
        return Code(
            head=render(
                """
                import builtins
                import typing
                from functools import cached_property
                from typing import Any, Literal, NotRequired

                class ProxmoxAPI:
                {% for child in children -%}
                {{  child.dump(type_check_only=False).headcode(indent=True) }}
                {% endfor -%}
                """,
                children=self.children,
            )
        )
