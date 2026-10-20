"""One-evaluation composition of Library records and Trust Proof issuance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from kinetic_trust_library.core import evaluate
from kinetic_trust_library.core.record import build_decision_record
from kinetic_trust_library.models.envelope import (
    EvaluationBundle,
    EvaluationRequest,
    RejectedRequest,
)
from kinetic_trust_library.models.proof import ProofIntent, ProofToken
from kinetic_trust_library.models.record import DecisionRecord
from kinetic_trust_library.models.soul import SoulAssessmentState
from kinetic_trust_library.proofs import TrustProofs
from kinetic_trust_library.protocols import ProofSigner


@dataclass(frozen=True, slots=True, init=False)
class RejectedIssuance:
    rejection: RejectedRequest

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("RejectedIssuance values are created by Issuer")


@dataclass(frozen=True, slots=True, init=False)
class EvaluatedWithoutProof:
    evaluation: EvaluationBundle
    record: DecisionRecord

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("EvaluatedWithoutProof values are created by Issuer")


@dataclass(frozen=True, slots=True, init=False)
class IssuedProof:
    evaluation: EvaluationBundle
    proof: ProofToken
    record: DecisionRecord

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("IssuedProof values are created by Issuer")


IssuanceOutcome: TypeAlias = RejectedIssuance | EvaluatedWithoutProof | IssuedProof


def _rejected_issuance(value: RejectedRequest, /) -> RejectedIssuance:
    if type(value) is not RejectedRequest:
        raise TypeError("rejected issuance requires an exact RejectedRequest")
    outcome = object.__new__(RejectedIssuance)
    object.__setattr__(outcome, "rejection", value)
    return outcome


def _evaluated_without_proof(
    evaluation: EvaluationBundle,
    record: DecisionRecord,
    /,
) -> EvaluatedWithoutProof:
    if type(evaluation) is not EvaluationBundle or type(record) is not DecisionRecord:
        raise TypeError("evaluated outcome requires exact Library values")
    outcome = object.__new__(EvaluatedWithoutProof)
    object.__setattr__(outcome, "evaluation", evaluation)
    object.__setattr__(outcome, "record", record)
    return outcome


def _issued_proof(
    evaluation: EvaluationBundle,
    proof: ProofToken,
    record: DecisionRecord,
    /,
) -> IssuedProof:
    if (
        type(evaluation) is not EvaluationBundle
        or type(proof) is not ProofToken
        or type(record) is not DecisionRecord
    ):
        raise TypeError("issued outcome requires exact Library values")
    outcome = object.__new__(IssuedProof)
    object.__setattr__(outcome, "evaluation", evaluation)
    object.__setattr__(outcome, "proof", proof)
    object.__setattr__(outcome, "record", record)
    return outcome


class Issuer:
    __slots__ = ("_proofs",)

    def __init__(self, proofs: TrustProofs, /) -> None:
        if type(proofs) is not TrustProofs:
            raise TypeError("issuer requires an exact TrustProofs facade")
        self._proofs = proofs

    def issue(
        self,
        request: EvaluationRequest,
        *,
        proof: ProofIntent,
        signer: ProofSigner,
    ) -> IssuanceOutcome:
        evaluated = evaluate(request)
        if type(evaluated) is RejectedRequest:
            return _rejected_issuance(evaluated)

        record = build_decision_record(evaluated)
        if record.soul_state is not SoulAssessmentState.CLEAR:
            return _evaluated_without_proof(evaluated, record)

        token = self._proofs.issue(evaluated, proof=proof, signer=signer)
        return _issued_proof(evaluated, token, record)


__all__ = [
    "EvaluatedWithoutProof",
    "IssuedProof",
    "IssuanceOutcome",
    "Issuer",
    "RejectedIssuance",
]
