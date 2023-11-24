import typing
from dataclasses import dataclass, field

from marshmallow import EXCLUDE, Schema, fields, types


@dataclass(kw_only=True)
class LogResult:
    collected_count: int = field()
    error_count: int = field()
    elapsed_sec: int = field()

    class __LogResultSchema(Schema):
        collected_count: int = fields.Int(required=True)
        error_count: int = fields.Int(required=True)
        elapsed_sec: int = fields.Int(required=True)

        def load(
            self,
            data: (
                typing.Mapping[str, typing.Any]
                | typing.Iterable[typing.Mapping[str, typing.Any]]
            ),
            *,
            many: bool | None = None,
            partial: bool | types.StrSequenceOrSet | None = None,
            unknown: str | None = None,
        ):
            res = super().load(data, many=many, partial=partial, unknown=unknown)
            return LogResult(**res)

        class Meta:
            unknown = EXCLUDE

    @classmethod
    def load(cls, data: typing.Mapping[str, typing.Any]) -> "LogResult":
        return cls.__LogResultSchema().load(data)
