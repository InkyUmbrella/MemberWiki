from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, Optional, TypeVar, cast, overload

T = TypeVar("T")
U = TypeVar("U")
_MISSING = object()


@dataclass
class Result(Generic[T]):
    ok: bool
    value: Optional[T] = None
    error: Optional[str] = None
    code: Optional[str] = None
    cause: Optional["Result[Any]"] = None
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(cls, value: Optional[T] = None, **data: Any) -> "Result[T]":
        return cls(ok=True, value=value, data=data)

    @classmethod
    def failure(
        cls,
        error: str | object,
        *,
        code: Optional[str] = None,
        value: Optional[T] = None,
        **data: Any,
    ) -> "Result[T]":
        if not isinstance(error, str):
            msg = getattr(error, "message", str(error))
            err_code = getattr(error, "code", code)
            return cls(ok=False, value=value, error=msg, code=err_code, data=data)
        return cls(ok=False, value=value, error=error, code=code, data=data)

    @overload
    @classmethod
    def failure_from(
        cls,
        result: "Result[T]",
        *,
        error: Optional[str] = None,
        code: Optional[str] = None,
        **data: Any,
    ) -> "Result[T]": ...

    @overload
    @classmethod
    def failure_from(
        cls,
        result: "Result[Any]",
        *,
        error: Optional[str] = None,
        code: Optional[str] = None,
        value: Optional[U],
        **data: Any,
    ) -> "Result[U]": ...

    @classmethod
    def failure_from(
        cls,
        result: "Result[Any]",
        *,
        error: Optional[str] = None,
        code: Optional[str] = None,
        value: object = _MISSING,
        **data: Any,
    ) -> "Result[Any]":
        if result.ok:
            raise ValueError("failure_from can only be used on a failed Result")

        merged_data = dict(result.data)
        merged_data.update(data)

        return cls(
            ok=False,
            value=cast(Optional[Any], result.value if value is _MISSING else value),
            error=error if error is not None else result.error,
            code=code if code is not None else result.code,
            cause=result,
            data=merged_data,
        )

    def unwrap(self) -> T:
        if not self.ok:
            raise RuntimeError(self.error or "Result unwrap failed")
        if self.value is None:
            raise RuntimeError("Result unwrap failed: value is None")
        return cast(T, self.value)

    def expect(self, message: str) -> T:
        if not self.ok:
            detail = self.error or "unknown error"
            raise RuntimeError(f"{message}: {detail}")
        if self.value is None:
            raise RuntimeError(f"{message}: value is None")
        return cast(T, self.value)


__all__ = ["Result"]
