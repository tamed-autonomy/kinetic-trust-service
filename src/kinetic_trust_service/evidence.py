"""Synchronous collection of caller-supplied observation declarations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Protocol
from unicodedata import category, normalize

from kinetic_trust_library import ValidationError, validate_absolute_uri
from kinetic_trust_library.models.evidence import ObservationDeclaration


_OPERATION_ID = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,127}$")


@dataclass(frozen=True, slots=True)
class EvidenceQuery:
    """Immutable carrier identifying one application's evidence request."""

    operation_id: str
    subject: str
    cutoff: datetime

    def __post_init__(self) -> None:
        _require_operation_id(self.operation_id)
        _require_subject(self.subject)
        _require_cutoff(self.cutoff)


class EvidenceAdapter(Protocol):
    """Application-supplied source of exact observation declarations."""

    @property
    def adapter_id(self) -> str: ...

    def collect(
        self,
        query: EvidenceQuery,
        /,
    ) -> tuple[ObservationDeclaration, ...]: ...


class EvidenceAdapterError(RuntimeError):
    """Report an adapter invocation or result failure by registered ID."""

    adapter_id: str

    def __init__(self, adapter_id: str, /) -> None:
        super().__init__(f"evidence adapter {adapter_id!r} failed")
        self.adapter_id = adapter_id


class EvidenceHost:
    """Collect a fixed adapter tuple in order, stopping on the first failure."""

    __slots__ = ("_adapter_ids", "_adapters")

    def __init__(self, adapters: tuple[EvidenceAdapter, ...], /) -> None:
        if type(adapters) is not tuple:
            raise TypeError("evidence adapters must be an owned tuple")
        adapter_ids: list[str] = []
        seen: set[str] = set()
        for adapter in adapters:
            try:
                adapter_id = adapter.adapter_id
            except Exception as exc:
                raise TypeError("evidence adapter ID is unavailable") from exc
            adapter_id = _require_adapter_id(adapter_id)
            if adapter_id in seen:
                raise ValueError(f"evidence adapter ID is duplicated: {adapter_id!r}")
            seen.add(adapter_id)
            adapter_ids.append(adapter_id)
        self._adapters = adapters
        self._adapter_ids = tuple(adapter_ids)

    def collect(
        self,
        query: EvidenceQuery,
        /,
    ) -> tuple[ObservationDeclaration, ...]:
        if type(query) is not EvidenceQuery:
            raise TypeError("evidence query must be an exact EvidenceQuery")
        declarations: list[ObservationDeclaration] = []
        for adapter_id, adapter in zip(self._adapter_ids, self._adapters, strict=True):
            try:
                produced = adapter.collect(query)
            except Exception as exc:
                raise EvidenceAdapterError(adapter_id) from exc
            try:
                if type(produced) is not tuple:
                    raise TypeError("evidence adapter result must be an owned tuple")
                if any(type(item) is not ObservationDeclaration for item in produced):
                    raise TypeError(
                        "evidence adapter result must contain exact ObservationDeclaration values"
                    )
            except (AttributeError, TypeError, ValueError) as exc:
                raise EvidenceAdapterError(adapter_id) from exc
            declarations.extend(produced)
        return tuple(declarations)


def _utf8(value: str, *, name: str) -> bytes:
    try:
        return value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{name} contains invalid Unicode") from exc


def _require_operation_id(value: object, /) -> str:
    if type(value) is not str:
        raise TypeError("operation ID must be an exact string")
    _utf8(value, name="operation ID")
    if normalize("NFC", value) != value or _OPERATION_ID.fullmatch(value) is None:
        raise ValueError("operation ID is invalid")
    return value


def _require_subject(value: object, /) -> str:
    if type(value) is not str:
        raise TypeError("evidence subject must be an exact string")
    try:
        return validate_absolute_uri(value, name="evidence subject")
    except ValidationError as exc:
        raise ValueError("evidence subject must be an absolute URI") from exc


def _require_cutoff(value: object, /) -> datetime:
    if type(value) is not datetime or value.tzinfo is not timezone.utc:
        raise TypeError("evidence cutoff must be an exact UTC datetime")
    return value


def _require_adapter_id(value: object, /) -> str:
    if type(value) is not str:
        raise TypeError("evidence adapter ID must be an exact string")
    encoded = _utf8(value, name="evidence adapter ID")
    if not encoded or len(encoded) > 256 or normalize("NFC", value) != value:
        raise ValueError("evidence adapter ID is invalid")
    if any(character.isspace() for character in value) or any(
        category(character) in {"Cc", "Cf"} for character in value
    ):
        raise ValueError("evidence adapter ID contains whitespace or controls")
    return value


__all__ = (
    "EvidenceAdapter",
    "EvidenceAdapterError",
    "EvidenceHost",
    "EvidenceQuery",
)
