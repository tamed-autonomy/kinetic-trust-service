"""Boundary behavior for the synchronous evidence adapter seam."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from typing import Callable
import unittest

from kinetic_trust_library import ValidationError
from kinetic_trust_library.models.evidence import (
    DerivedStateMeasurementEnvelope,
    ObservationClass,
    ObservationDeclaration,
)
from kinetic_trust_library.models.profile import RiskDomain
import kinetic_trust_service
from kinetic_trust_service import evidence
from kinetic_trust_service.evidence import (
    EvidenceAdapterError,
    EvidenceHost,
    EvidenceQuery,
)


_CUTOFF = datetime(2026, 10, 7, 12, 0, tzinfo=timezone.utc)
_QUERY = EvidenceQuery(
    operation_id="operation:evidence:1", subject="urn:agent:test", cutoff=_CUTOFF
)


def declaration(*, source_id: str, sequence: int = 1) -> ObservationDeclaration:
    return ObservationDeclaration(
        observation_id=f"observation:{source_id}:{sequence}",
        source_id=source_id,
        sequence=sequence,
        signal_id="body.clock.sync_state",
        domain=RiskDomain.NODE,
        observation_class=ObservationClass.DERIVED_STATE,
        measurement_envelope=DerivedStateMeasurementEnvelope(
            scope="subject",
            authoritative_source="urn:source:identity",
            source_version="1",
        ),
        raw_value="present",
        unit="state",
        observed_at=_CUTOFF,
        ingested_at=_CUTOFF,
    )


class Adapter:
    def __init__(
        self,
        adapter_id: str,
        behavior: Callable[[EvidenceQuery], object],
        calls: list[tuple[str, EvidenceQuery]],
    ) -> None:
        self.adapter_id = adapter_id
        self._behavior = behavior
        self._calls = calls

    def collect(self, query: EvidenceQuery, /) -> object:
        self._calls.append((self.adapter_id, query))
        return self._behavior(query)


class EvidenceHostTests(unittest.TestCase):
    def test_evidence_exports_preserve_root_identity(self) -> None:
        expected = (
            "EvidenceAdapter", "EvidenceAdapterError", "EvidenceHost", "EvidenceQuery"
        )
        self.assertEqual(evidence.__all__, expected)
        for name in expected:
            self.assertIs(getattr(kinetic_trust_service, name), getattr(evidence, name))

    def test_collect_preserves_adapter_and_declaration_order(self) -> None:
        calls: list[tuple[str, EvidenceQuery]] = []
        first = declaration(source_id="source:first")
        second = declaration(source_id="source:first", sequence=2)
        third = declaration(source_id="source:second")
        host = EvidenceHost((
            Adapter("adapter:first", lambda query: (first, second), calls),
            Adapter("adapter:second", lambda query: (third,), calls),
        ))
        result = host.collect(_QUERY)
        self.assertIs(type(result), tuple)
        self.assertEqual(result, (first, second, third))
        for actual, expected in zip(result, (first, second, third), strict=True):
            self.assertIs(actual, expected)
        self.assertEqual(calls, [("adapter:first", _QUERY), ("adapter:second", _QUERY)])
        self.assertTrue(all(query is _QUERY for _, query in calls))

    def test_empty_host_and_empty_adapter_results_are_valid(self) -> None:
        self.assertEqual(EvidenceHost(()).collect(_QUERY), ())
        host = EvidenceHost((Adapter("adapter:empty", lambda query: (), []),))
        self.assertEqual(host.collect(_QUERY), ())

    def test_adapter_failure_preserves_id_and_cause_and_stops(self) -> None:
        calls: list[tuple[str, EvidenceQuery]] = []
        failure = LookupError("source unavailable")

        def fail(query: EvidenceQuery) -> object:
            raise failure

        host = EvidenceHost((
            Adapter("adapter:failing", fail, calls),
            Adapter("adapter:later", lambda query: (), calls),
        ))
        with self.assertRaises(EvidenceAdapterError) as caught:
            host.collect(_QUERY)
        self.assertEqual(caught.exception.adapter_id, "adapter:failing")
        self.assertIs(caught.exception.__cause__, failure)
        self.assertEqual(calls, [("adapter:failing", _QUERY)])

    def test_result_contract_failure_stops_without_fabricated_evidence(self) -> None:
        calls: list[tuple[str, EvidenceQuery]] = []
        host = EvidenceHost((
            Adapter("adapter:bad", lambda query: [declaration(source_id="source:bad")], calls),
            Adapter("adapter:later", lambda query: (), calls),
        ))
        with self.assertRaises(EvidenceAdapterError) as caught:
            host.collect(_QUERY)
        self.assertEqual(caught.exception.adapter_id, "adapter:bad")
        self.assertIsInstance(caught.exception.__cause__, TypeError)
        self.assertEqual(tuple(call[0] for call in calls), ("adapter:bad",))

    def test_exact_but_semantically_invalid_declaration_passes_unchanged(self) -> None:
        invalid = declaration(source_id="source:semantic", sequence=-1)
        host = EvidenceHost((Adapter("adapter:semantic", lambda query: (invalid,), []),))
        self.assertIs(host.collect(_QUERY)[0], invalid)

    def test_adapter_id_is_not_evidence_source_id(self) -> None:
        value = declaration(source_id="source:independent")
        host = EvidenceHost((Adapter("adapter:integration", lambda query: (value,), []),))
        self.assertIs(host.collect(_QUERY)[0], value)

    def test_constructor_requires_exact_adapter_tuple(self) -> None:
        class TupleSubclass(tuple):
            pass

        for adapters in ([], TupleSubclass(())):
            with self.subTest(adapters=type(adapters)), self.assertRaises(TypeError):
                EvidenceHost(adapters)

    def test_constructor_rejects_duplicate_ids(self) -> None:
        with self.assertRaises(ValueError):
            EvidenceHost((
                Adapter("adapter:duplicate", lambda query: (), []),
                Adapter("adapter:duplicate", lambda query: (), []),
            ))

    def test_constructor_requires_exact_string_ids(self) -> None:
        class StringSubclass(str):
            pass

        for adapter_id in (StringSubclass("adapter:subclass"), None):
            with self.subTest(adapter_id=adapter_id), self.assertRaises(TypeError):
                EvidenceHost((Adapter(adapter_id, lambda query: (), []),))

    def test_constructor_rejects_invalid_adapter_id_carriers(self) -> None:
        for adapter_id in ("", "adapter:e\u0301", "adapter: space", "adapter:\t", "adapter:\x00", "adapter:\u200d", "é" * 129, "\ud800"):
            with self.subTest(adapter_id=repr(adapter_id)), self.assertRaises(ValueError):
                EvidenceHost((Adapter(adapter_id, lambda query: (), []),))

    def test_constructor_preserves_valid_nfc_id_at_utf8_limit(self) -> None:
        adapter_id = "é" * 128
        failure = LookupError("unavailable")

        def fail(query: EvidenceQuery) -> object:
            raise failure

        host = EvidenceHost((Adapter(adapter_id, fail, []),))
        with self.assertRaises(EvidenceAdapterError) as caught:
            host.collect(_QUERY)
        self.assertEqual(caught.exception.adapter_id, adapter_id)

    def test_constructor_preserves_unavailable_id_cause(self) -> None:
        failure = LookupError("missing ID")

        class UnavailableAdapter:
            @property
            def adapter_id(self) -> str:
                raise failure

        with self.assertRaises(TypeError) as caught:
            EvidenceHost((UnavailableAdapter(),))
        self.assertIs(caught.exception.__cause__, failure)

    def test_failure_uses_id_owned_at_registration(self) -> None:
        failure = LookupError("unavailable")

        def fail(query: EvidenceQuery) -> object:
            raise failure

        adapter = Adapter("adapter:registered", fail, [])
        host = EvidenceHost((adapter,))
        adapter.adapter_id = "adapter:changed"
        with self.assertRaises(EvidenceAdapterError) as caught:
            host.collect(_QUERY)
        self.assertEqual(caught.exception.adapter_id, "adapter:registered")

    def test_collect_rejects_non_exact_query_before_invoking_adapters(self) -> None:
        class QuerySubclass(EvidenceQuery):
            pass

        calls: list[tuple[str, EvidenceQuery]] = []
        host = EvidenceHost((Adapter("adapter:unused", lambda query: (), calls),))
        for query in (object(), QuerySubclass("operation:1", "urn:agent:test", _CUTOFF)):
            with self.subTest(query=type(query)), self.assertRaises(TypeError):
                host.collect(query)
        self.assertEqual(calls, [])

    def test_collect_rejects_tuple_subclass_results(self) -> None:
        class TupleSubclass(tuple):
            pass

        host = EvidenceHost((Adapter("adapter:result", lambda query: TupleSubclass(()), []),))
        with self.assertRaises(EvidenceAdapterError) as caught:
            host.collect(_QUERY)
        self.assertIsInstance(caught.exception.__cause__, TypeError)

    def test_collect_rejects_non_exact_declarations_and_stops(self) -> None:
        class DeclarationSubclass(ObservationDeclaration):
            pass

        source = declaration(source_id="source:subclass")
        subclass = DeclarationSubclass(**{
            name: getattr(source, name) for name in source.__dataclass_fields__
        })
        for invalid in (subclass, object()):
            calls: list[tuple[str, EvidenceQuery]] = []
            host = EvidenceHost((
                Adapter("adapter:bad-item", lambda query: (source, invalid), calls),
                Adapter("adapter:later", lambda query: (), calls),
            ))
            with self.subTest(invalid=type(invalid)), self.assertRaises(EvidenceAdapterError) as caught:
                host.collect(_QUERY)
            self.assertEqual(caught.exception.adapter_id, "adapter:bad-item")
            self.assertIsInstance(caught.exception.__cause__, TypeError)
            self.assertEqual(calls, [("adapter:bad-item", _QUERY)])

    def test_host_boundaries_are_positional_only(self) -> None:
        with self.assertRaises(TypeError):
            EvidenceHost(adapters=())
        with self.assertRaises(TypeError):
            EvidenceHost(()).collect(query=_QUERY)
        with self.assertRaises(TypeError):
            EvidenceAdapterError(adapter_id="adapter:1")


class EvidenceQueryTests(unittest.TestCase):
    def test_query_is_immutable_and_preserves_values(self) -> None:
        query = EvidenceQuery("operation:1", "https://example.test/a", _CUTOFF)
        self.assertEqual(query.operation_id, "operation:1")
        self.assertEqual(query.subject, "https://example.test/a")
        self.assertIs(query.cutoff, _CUTOFF)
        with self.assertRaises(FrozenInstanceError):
            query.subject = "urn:changed"

    def test_query_rejects_non_exact_strings(self) -> None:
        class StringSubclass(str):
            pass

        for field in ("operation_id", "subject"):
            values = dict(operation_id="operation:1", subject="urn:agent:test", cutoff=_CUTOFF)
            values[field] = StringSubclass(values[field])
            with self.subTest(field=field), self.assertRaises(TypeError):
                EvidenceQuery(**values)

    def test_query_rejects_malformed_operation_ids(self) -> None:
        for operation_id in ("", "Operation:1", "operation/1", "operation 1", "a" * 129, "e\u0301", "\ud800"):
            with self.subTest(operation_id=repr(operation_id)), self.assertRaises(ValueError):
                EvidenceQuery(operation_id, "urn:agent:test", _CUTOFF)

    def test_query_accepts_operation_id_length_boundary(self) -> None:
        self.assertEqual(EvidenceQuery("a" * 128, "urn:agent:test", _CUTOFF).operation_id, "a" * 128)

    def test_query_rejects_invalid_subject_carriers(self) -> None:
        for subject in ("", "relative/path", "urn:", "1bad:x", "urn:e\u0301", "urn:space here", "urn:\x00", "urn:\u200d", "urn:" + "é" * 1023, "urn:\ud800", "https:relative", "https:///path", "https://example.test:bad", "http://[bad"):
            with self.subTest(subject=repr(subject)), self.assertRaises(ValueError):
                EvidenceQuery("operation:1", subject, _CUTOFF)

    def test_query_rejects_subjects_outside_library_uri_policy(self) -> None:
        invalid = (
            "urn:%ZZ",
            "urn:a\\b",
            "urn:é",
            "urn:{x}",
            "http://999.999.999.999",
            "https://example.test:",
            "https://user@@example.test",
        )
        for subject in invalid:
            with self.subTest(subject=subject):
                with self.assertRaises(ValueError) as caught:
                    EvidenceQuery("operation:1", subject, _CUTOFF)
                self.assertIsInstance(caught.exception.__cause__, ValidationError)

    def test_query_preserves_subject_at_character_limit(self) -> None:
        subject = "urn:" + "a" * 2044
        self.assertEqual(
            EvidenceQuery("operation:1", subject, _CUTOFF).subject,
            subject,
        )

    def test_query_requires_exact_utc_cutoff(self) -> None:
        class DatetimeSubclass(datetime):
            pass

        for cutoff in (
            datetime(2026, 10, 7, 12),
            datetime(2026, 10, 7, 12, tzinfo=timezone(timedelta(hours=1))),
            DatetimeSubclass(2026, 10, 7, 12, tzinfo=timezone.utc),
            "2026-10-07T12:00:00Z",
        ):
            with self.subTest(cutoff=cutoff), self.assertRaises(TypeError):
                EvidenceQuery("operation:1", "urn:agent:test", cutoff)


if __name__ == "__main__":
    unittest.main()
