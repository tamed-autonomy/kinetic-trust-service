"""The issuer composes Library boundaries without adding semantic policy."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import unittest
from unittest.mock import patch

from kinetic_trust_library.core import evaluate as library_evaluate
from kinetic_trust_library.errors import SigningProviderFailureError
from kinetic_trust_library.models.capacity import CapacityRelation, CoreCapacityResult
from kinetic_trust_library.models.envelope import (
    EvaluationBundle,
    KineticEnvelopeResult,
    RejectedRequest,
)
from kinetic_trust_library.models.proof import ProofToken
from kinetic_trust_library.models.record import DecisionRecord
from kinetic_trust_library.models.soul import SoulAssessmentState
from kinetic_trust_library.proofs import TrustProofs
from kinetic_trust_service.issuance import (
    EvaluatedWithoutProof,
    IssuedProof,
    Issuer,
    RejectedIssuance,
)


class Hostile:
    def __getattribute__(self, name: str) -> object:
        raise AssertionError(f"unexpected access: {name}")


# Exact Library shells are confined to patched orchestration boundaries. No Library
# operation receives them: Library validation and crypto have their own tests.
def evaluation(*, clear: bool) -> EvaluationBundle:
    value = object.__new__(EvaluationBundle)
    capacity = None
    capacity_digest = None
    if clear:
        capacity = object.__new__(CoreCapacityResult)
        object.__setattr__(capacity, "digest", "a" * 64)
        capacity_digest = capacity.digest
    envelope = object.__new__(KineticEnvelopeResult)
    object.__setattr__(envelope, "core_capacity_digest", capacity_digest)
    object.__setattr__(value, "core_capacity", capacity)
    object.__setattr__(value, "envelope", envelope)
    return value


def record(state: SoulAssessmentState) -> DecisionRecord:
    value = object.__new__(DecisionRecord)
    object.__setattr__(value, "soul_state", state)
    object.__setattr__(
        value, "core_capacity_digest",
        "a" * 64 if state is SoulAssessmentState.CLEAR else None,
    )
    object.__setattr__(
        value, "capacity_relation",
        CapacityRelation.BELOW_CAPACITY if state is SoulAssessmentState.CLEAR else None,
    )
    return value


def token() -> ProofToken:
    return object.__new__(ProofToken)


class IssuerTests(unittest.TestCase):
    def test_rejected_request_does_not_touch_record_proof_or_signer(self) -> None:
        proofs = object.__new__(TrustProofs)
        request = object()
        with (
            patch("kinetic_trust_service.issuance.evaluate", wraps=library_evaluate) as evaluate_call,
            patch("kinetic_trust_service.issuance.build_decision_record") as build_call,
            patch.object(TrustProofs, "issue") as proof_call,
        ):
            outcome = Issuer(proofs).issue(
                request,  # type: ignore[arg-type]
                proof=Hostile(),  # type: ignore[arg-type]
                signer=Hostile(),  # type: ignore[arg-type]
            )
        self.assertIs(type(outcome), RejectedIssuance)
        self.assertIs(type(outcome.rejection), RejectedRequest)
        evaluate_call.assert_called_once_with(request)
        build_call.assert_not_called()
        proof_call.assert_not_called()

    def test_nonclear_paths_build_record_without_touching_proof_or_signer(self) -> None:
        for state in (SoulAssessmentState.VETO, SoulAssessmentState.UNDETERMINED):
            with self.subTest(state=state):
                proofs = object.__new__(TrustProofs)
                request = object()
                evaluated = evaluation(clear=False)
                represented = record(state)
                with (
                    patch("kinetic_trust_service.issuance.evaluate", return_value=evaluated) as evaluate_call,
                    patch("kinetic_trust_service.issuance.build_decision_record", return_value=represented) as build_call,
                    patch.object(TrustProofs, "issue") as proof_call,
                ):
                    outcome = Issuer(proofs).issue(
                        request,  # type: ignore[arg-type]
                        proof=Hostile(),  # type: ignore[arg-type]
                        signer=Hostile(),  # type: ignore[arg-type]
                    )
                self.assertIs(type(outcome), EvaluatedWithoutProof)
                self.assertIs(outcome.evaluation, evaluated)
                self.assertIs(outcome.record, represented)
                self.assertIsNone(outcome.evaluation.core_capacity)
                self.assertIsNone(outcome.evaluation.envelope.core_capacity_digest)
                self.assertIsNone(outcome.record.core_capacity_digest)
                self.assertIsNone(outcome.record.capacity_relation)
                evaluate_call.assert_called_once_with(request)
                build_call.assert_called_once_with(evaluated)
                proof_call.assert_not_called()

    def test_clear_path_builds_record_then_issues_once(self) -> None:
        proofs = object.__new__(TrustProofs)
        request = object()
        evaluated = evaluation(clear=True)
        represented = record(SoulAssessmentState.CLEAR)
        proof_token = token()
        proof = object()
        signer = object()
        calls: list[str] = []

        def build(value: EvaluationBundle) -> DecisionRecord:
            calls.append("record")
            return represented

        def issue(value: EvaluationBundle, *, proof: object, signer: object) -> ProofToken:
            calls.append("proof")
            return proof_token

        with (
            patch("kinetic_trust_service.issuance.evaluate", return_value=evaluated) as evaluate_call,
            patch("kinetic_trust_service.issuance.build_decision_record", side_effect=build) as build_call,
            patch.object(TrustProofs, "issue", side_effect=issue) as proof_call,
        ):
            outcome = Issuer(proofs).issue(
                request,  # type: ignore[arg-type]
                proof=proof,  # type: ignore[arg-type]
                signer=signer,  # type: ignore[arg-type]
            )
        self.assertIs(type(outcome), IssuedProof)
        self.assertIs(outcome.evaluation, evaluated)
        self.assertIs(outcome.record, represented)
        self.assertIs(outcome.proof, proof_token)
        self.assertEqual(
            outcome.evaluation.envelope.core_capacity_digest,
            outcome.evaluation.core_capacity.digest,
        )
        self.assertEqual(
            outcome.record.core_capacity_digest,
            outcome.evaluation.core_capacity.digest,
        )
        self.assertIs(outcome.record.capacity_relation, CapacityRelation.BELOW_CAPACITY)
        evaluate_call.assert_called_once_with(request)
        build_call.assert_called_once_with(evaluated)
        proof_call.assert_called_once_with(evaluated, proof=proof, signer=signer)
        self.assertEqual(calls, ["record", "proof"])

    def test_proof_error_propagates_by_identity_without_retry(self) -> None:
        failure = SigningProviderFailureError("signer failed")
        proofs = object.__new__(TrustProofs)
        with (
            patch("kinetic_trust_service.issuance.evaluate", return_value=evaluation(clear=True)),
            patch("kinetic_trust_service.issuance.build_decision_record", return_value=record(SoulAssessmentState.CLEAR)),
            patch.object(TrustProofs, "issue", side_effect=failure) as proof_call,
        ):
            with self.assertRaises(SigningProviderFailureError) as caught:
                Issuer(proofs).issue(object(), proof=object(), signer=object())  # type: ignore[arg-type]
        self.assertIs(caught.exception, failure)
        self.assertEqual(proof_call.call_count, 1)

    def test_record_error_propagates_by_identity_without_proof_access(self) -> None:
        failure = ValueError("record failed")
        with (
            patch("kinetic_trust_service.issuance.evaluate", return_value=evaluation(clear=True)) as evaluate_call,
            patch("kinetic_trust_service.issuance.build_decision_record", side_effect=failure) as build_call,
            patch.object(TrustProofs, "issue") as proof_call,
        ):
            with self.assertRaises(ValueError) as caught:
                Issuer(object.__new__(TrustProofs)).issue(
                    object(), proof=Hostile(), signer=Hostile()  # type: ignore[arg-type]
                )
        self.assertIs(caught.exception, failure)
        self.assertEqual(evaluate_call.call_count, 1)
        self.assertEqual(build_call.call_count, 1)
        proof_call.assert_not_called()

    def test_evaluation_error_propagates_without_record_or_proof_access(self) -> None:
        failure = RuntimeError("evaluation failed")
        with (
            patch("kinetic_trust_service.issuance.evaluate", side_effect=failure) as evaluate_call,
            patch("kinetic_trust_service.issuance.build_decision_record") as build_call,
            patch.object(TrustProofs, "issue") as proof_call,
        ):
            with self.assertRaises(RuntimeError) as caught:
                Issuer(object.__new__(TrustProofs)).issue(
                    object(), proof=Hostile(), signer=Hostile()  # type: ignore[arg-type]
                )
        self.assertIs(caught.exception, failure)
        self.assertEqual(evaluate_call.call_count, 1)
        build_call.assert_not_called()
        proof_call.assert_not_called()

    def test_outcome_public_construction_is_guarded(self) -> None:
        for outcome in (RejectedIssuance, EvaluatedWithoutProof, IssuedProof):
            with self.subTest(outcome=outcome), self.assertRaises(TypeError):
                outcome()

    def test_issuer_requires_exact_positional_trust_proofs(self) -> None:
        class ProofsSubclass(TrustProofs):
            pass

        for invalid in (object(), object.__new__(ProofsSubclass)):
            with self.subTest(invalid=type(invalid)), self.assertRaises(TypeError):
                Issuer(invalid)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            Issuer(proofs=object.__new__(TrustProofs))

    def test_outcome_fields_are_immutable(self) -> None:
        proofs = object.__new__(TrustProofs)
        rejected = Issuer(proofs).issue(
            object(), proof=Hostile(), signer=Hostile()  # type: ignore[arg-type]
        )
        outcomes = [(rejected, "rejection")]
        for state in (SoulAssessmentState.VETO, SoulAssessmentState.CLEAR):
            with (
                patch("kinetic_trust_service.issuance.evaluate", return_value=evaluation(clear=state is SoulAssessmentState.CLEAR)),
                patch("kinetic_trust_service.issuance.build_decision_record", return_value=record(state)),
                patch.object(TrustProofs, "issue", return_value=token()),
            ):
                outcomes.append((Issuer(proofs).issue(
                    object(), proof=object(), signer=object()  # type: ignore[arg-type]
                ), "record"))
        for outcome, field in outcomes:
            with self.subTest(outcome=type(outcome)), self.assertRaises(FrozenInstanceError):
                setattr(outcome, field, object())
            self.assertFalse(hasattr(outcome, "__dict__"))


if __name__ == "__main__":
    unittest.main()
