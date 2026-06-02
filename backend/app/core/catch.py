import inspect
from functools import wraps
from typing import Callable, Optional, ParamSpec, TypeVar, Union, overload

from .result import Result

P = ParamSpec("P")
T = TypeVar("T")
ExceptionHandler = Callable[[BaseException, inspect.BoundArguments], Result[T]]


@overload
def catch_result(
    *,
    handlers: Optional[
        dict[type[BaseException] | tuple[type[BaseException], ...], ExceptionHandler[T]]
    ] = None,
    default: Optional[ExceptionHandler[T]] = None,
) -> Callable[[Callable[P, T | Result[T]]], Callable[P, Result[T]]]: ...

@overload
def catch_result(func: Callable[P, T | Result[T]]) -> Callable[P, Result[T]]: ...

def catch_result(
    func: Optional[Callable[P, T | Result[T]]] = None,
    *,
    handlers: Optional[
        dict[type[BaseException] | tuple[type[BaseException], ...], ExceptionHandler[T]]
    ] = None,
    default: Optional[ExceptionHandler[T]] = None,
) -> Union[
    Callable[[Callable[P, T | Result[T]]], Callable[P, Result[T]]],
    Callable[P, Result[T]],
]:
    def decorator(fn: Callable[P, T | Result[T]]) -> Callable[P, Result[T]]:
        signature = inspect.signature(fn)

        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Result[T]:
            bound = signature.bind_partial(*args, **kwargs)

            try:
                raw = fn(*args, **kwargs)
                if isinstance(raw, Result):
                    return raw
                return Result.success(raw)
            except Exception as exc:
                if handlers:
                    for exception_types, handler in handlers.items():
                        if isinstance(exc, exception_types):
                            return handler(exc, bound)

                if default is not None:
                    return default(exc, bound)
                raise

        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


__all__ = ["catch_result"]
