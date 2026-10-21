# Service vocabulary and ownership

The routinely tested support set is CPython 3.11 through 3.15.

**KTP Library**: The umbrella artifact, packaged as
`kinetic-trust-library` 2.1.0 and imported as `kinetic_trust_library`, providing
RFC-faithful KTP v2.1.0 semantics, models, evaluation, records, and proof rules.

**KTP-Core**: The formal protocol semantics and Library's internal core module,
not the umbrella artifact or a separate Service dependency.

**Service**: Packaged as `kinetic-trust-service` 2.1.0 and imported as
`kinetic_trust_service`. Replaceable synchronous composition conveniences, not
a product or semantic authority. Consumers can replace Service or call Library
directly without losing KTP semantics.

**Compatibility series**: Library and Service package `major.minor` versions
track the implemented KTP RFC series, with independent patch versions. Service
2.1.0 depends on `kinetic-trust-library>=2.1.0,<2.2.0`. Both packages remain
pinned to the immutable KTP v2.1.0 specification tag; a package patch release
does not imply a new KTP specification version.

**Product**: The consuming system that owns source authenticity/completeness,
configuration, credentials, storage, retention, transport, retries,
reconciliation, observability, deployment, execution, enforcement, and human
interaction.

**Core Capacity Result**: The capacity fact returned separately as
`evaluation.core_capacity`, not Envelope supervision or permission.

**Kinetic Envelope Result**: The supervision fact returned separately as
`evaluation.envelope`, not Core Capacity Result or permission.

**EvidenceQuery**: A Service-owned operational query carrier containing
operation identity, subject, and cutoff. It is not evidence.

**EvidenceAdapter**: A caller-implemented direct acquisition interface returning
a tuple of complete Library `ObservationDeclaration` values. The caller owns
external clients and acquisition; Service does not create or repair semantic
evidence.

**adapter_id**: An integration identity used to identify a registered adapter
and its failures. It is never inferred as an evidence `source_id`.

**EvidenceHost**: An ordered fail-first invocation helper. It calls adapters in
registration order and checks result shape, with no retry, evidence repair, or
source-health inference.

**Issuer**: A helper that performs one Library evaluation, constructs a Library
record for a valid evaluation, and issues a proof only for Soul-clear
evaluations. Operational errors propagate to the caller.

**RejectedIssuance**: A composition outcome containing Library's rejected request,
without an evaluation record or proof.

**EvaluatedWithoutProof**: A composition outcome containing a valid evaluation
and its record when the Soul assessment is not clear.

**IssuedProof**: A composition outcome containing a valid Soul-clear
evaluation, its record, and a proof. These three outcomes are not permission or
workflow states. A Soul-clear evaluation can receive a proof even when its
Envelope supervision is `SILENT_VETO`. Proof is not permission.

**DecisionRecord**: Library-owned returned deterministic data, not proof of
persistence, acceptance, execution, or enforcement. It is separate from the
proof and correlated by operation ID / proof `decision_id`. Its
`core_capacity_digest` and `capacity_relation` are `None` on the Soul short path.

**ProofIntent**: Caller intent for proof ID, resource, context hash, trajectory
ID, and requested lifetime. Library derives decision identity and issuance time
from the evaluation and bounds expiry.

If Service convenience conflicts with RFC-faithful Library semantics, Library wins and Service must change.
