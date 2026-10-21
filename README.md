# Kinetic Trust Service

`kinetic-trust-service` 2.1.0 is a synchronous library of KTP v2.1.0
evidence and issuance composition helpers. It is not a product or a runtime
service. Library owns RFC-faithful semantics and `DecisionRecord`; Service
provides replaceable conveniences for invoking product-supplied evidence
adapters and one-evaluation issuance. Consumers may call Library directly
without losing KTP semantics.

This is an independently maintained composition package. It is not an official
KTP SDK and is not certified, maintained, or endorsed by NMCITRA. Passing
tests, package checks, vectors, or scans is evidence limited to the behavior
exercised; it is not deployment or application conformance.

## Choosing Library or Service

[Kinetic Trust Library](https://github.com/tamed-autonomy/kinetic-trust-library)
is the semantic layer. Service is an optional Python package of synchronous
composition helpers built on Library; despite its name, it is not a server or
daemon. There is no Service-only path: Service depends on Library and delegates
KTP semantics to it.

| Scenario | Use |
|---|---|
| You need deterministic KTP validation and evaluation, Decision Record projection, Trust Proof operations, Soul Constraint document parsing, or Trajectory parsing and adjacent-pair assessment. | **Library directly** |
| You want Service's ordered, fail-first `EvidenceHost` for product-supplied adapters and/or its `Issuer` to compose one evaluation with Decision Record projection and, when Soul-clear, proof issuance. | **Library plus Service** |
| You need networking, storage, retries, source authentication, key lifecycle, observability, human workflows, action execution, or enforcement. | **Product-owned code around Library or Library plus Service.** Neither package supplies these capabilities. |

If you are unsure, start with Library and add Service only when `EvidenceHost`
or `Issuer` removes composition code you would otherwise maintain. Service is
replaceable without changing KTP semantics. Neither package alone establishes
application or deployment conformance, and neither is an enforcement point. A
Trust Proof is not permission to perform an action.

## Building a conforming KTP application

Conformance applies to a named, versioned application and its deployment, not
to Library or Service by themselves. Neither package has a Basic, Standard, or
Full mode, and the levels are cumulative: Standard includes Basic, and Full
includes Standard. The [Library contract
matrix](https://github.com/tamed-autonomy/kinetic-trust-library/blob/main/docs/traceability/library-contracts.md)
states what Library actually implements; the immutable [KTP-Conformance
v2.1.0](https://github.com/nmcitra/ktp-rfc/blob/v2.1.0/rfc-src/ktp-conformance.md)
defines the controlling requirements. This table is orientation, not a
complete requirements, certification, or remaining-gap checklist.

| Target | Capabilities the assembled application and deployment must provide |
|---|---|
| **Basic** | An operational Oracle interface and product-owned evidence sources; secure key and Trust Proof lifecycle; a real PEP that intercepts every protected request, validates proofs, enforces the Zeroth Law before the protected effect, and logs the result; queryable decision records retained for at least 30 days; unique agent identities and proof obtain, present, refresh, and denial behavior; conservative failure handling; and published evidence for the required Basic tests. |
| **Standard** | Everything in Basic, plus a three-or-more-node Oracle mesh with 2-of-3 threshold signing; all six weighted Risk Factors and the independent Soul veto across three risk domains; velocity, lineage, Proof of Resilience, sponsorship, and federation behavior; five-tier and Soul enforcement with graceful degradation; tamper-evident Decision Geometry, audit queries, one-year decision retention, and seven-year Soul-veto retention; full trajectory behavior; automated key rotation; and published Standard test evidence. |
| **Full** | Everything in Standard, plus at least five Oracle nodes across at least three regions, 3-of-5 threshold signing, real-time consensus, and sub-second proof refresh; redundant failover sensing and Indigenous Data Sovereignty controls; all-zone layered enforcement within the required latency; externally anchored, multi-region records with seven-year retention and forensic reconstruction; HSM-backed keys and complete identity, attestation, and extended-proof behavior; formal security review, penetration testing, incident-response and recovery procedures; and third-party certification. |

Service can reduce synchronous composition code; it does not satisfy or waive
any conformance obligation. Package tests and released vectors establish only
the named package behaviors. An unqualified Basic, Standard, or Full claim
requires satisfying every applicable requirement and passing 100% of the
required tests for that level. Under v2.1.0, documented deviations support
only a clearly identified partial-compliance claim.

The tagged v2.1.0 corpus has cross-document inconsistencies affecting level
boundaries, including Basic inputs and Soul, recorder chaining, proof
lifetimes, Standard HSM requirements, Full post-quantum timing, and the
relationship between six weighted factors and the independent Soul veto.
Upstream issues [#154](https://github.com/nmcitra/ktp-rfc/issues/154) and
[#155](https://github.com/nmcitra/ktp-rfc/issues/155) propose a single Core
semantic contract and component-scoped conformance claims. Until those
proposals are adopted in an immutable specification, an application must
assess the complete v2.1.0 tag, document its interpretations, and avoid
representing this summary as certification evidence.

> **Looking ahead (non-normative):** Upstream issue
> [#182](https://github.com/nmcitra/ktp-rfc/issues/182) is an open proposal for
> KTP v3.0.0 ("Ostrom"), with a planned—not committed—tag date of December 10,
> 2026. Its proposed release set includes the still-open #154 and #155 work.
> The tag is intended to wait until applicable review floors clear, required
> pull requests are green, and required release evidence is complete. Until an
> immutable v3 tag exists and these projects separately review and adopt it,
> they remain pinned to KTP v2.1.0.

## Install

Python 3.11 or newer is required; the routinely tested support set is
CPython 3.11 through 3.15. When version 2.1.0 appears on the
[PyPI project page](https://pypi.org/project/kinetic-trust-service/), install
it in a local virtual environment; its compatible Library dependency is
installed automatically:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install 'kinetic-trust-service==2.1.0'
```

For unreleased changes—or until the first release appears on PyPI—use sibling
`kinetic-trust-service` and `kinetic-trust-library` checkouts. Run from the
Service checkout, installing Library first:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install ../kinetic-trust-library
.venv/bin/python -m pip install .
```

Library and Service package `major.minor` versions track the implemented KTP
RFC series, while each package advances patch versions independently. Service
2.1.0 depends on `kinetic-trust-library>=2.1.0,<2.2.0` and adds no other runtime
dependencies or optional crypto dependency. Both packages remain pinned to the
immutable KTP v2.1.0 specification tag; a package patch release does not imply
a new KTP specification version.
PyCA Cryptography is needed only when a consumer chooses Library's optional
PyCA crypto adapter. The Python
interpreter running the library is sufficient; no separate interpreter
component is required.

## Direct evidence injection

The product supplies `product_declarations`: a tuple of complete, product- or
adapter-owned Library `ObservationDeclaration` values. These include source
identity, sequence, class-specific measurement facts, domain, and times; see
[Library's declaration documentation](https://github.com/tamed-autonomy/kinetic-trust-library/blob/main/CONTEXT.md)
and the
[declaration model](https://github.com/tamed-autonomy/kinetic-trust-library/blob/main/src/kinetic_trust_library/models/evidence.py).
The product owns external clients, configuration, credentials, and source
authenticity and completeness. Service neither creates nor repairs semantic
evidence.

```python
from datetime import datetime, timezone

from kinetic_trust_library.models.evidence import ObservationDeclaration
from kinetic_trust_service import EvidenceHost, EvidenceQuery


class ProductEvidenceAdapter:
    def __init__(
        self,
        declarations: tuple[ObservationDeclaration, ...],
    ) -> None:
        self._declarations = declarations

    @property
    def adapter_id(self) -> str:
        return "adapter:product-evidence"

    def collect(
        self,
        query: EvidenceQuery,
        /,
    ) -> tuple[ObservationDeclaration, ...]:
        return self._declarations


host = EvidenceHost((ProductEvidenceAdapter(product_declarations),))
observations = host.collect(
    EvidenceQuery(
        operation_id="operation:example:1",
        subject="urn:agent:example",
        cutoff=datetime(2026, 10, 7, 12, 0, tzinfo=timezone.utc),
    )
)
```

This is an integration skeleton: `product_declarations` must already exist.
`EvidenceQuery` carries an operational request, not evidence. `adapter_id`
identifies an integration and is never inferred as a declaration's `source_id`.
`EvidenceHost` calls adapters in registration order and stops at the first
failure, raising `EvidenceAdapterError` with that adapter's ID. It provides no
retry, evidence repair, or source-health inference.

## One-evaluation issuance

The product assembles a complete Library `EvaluationRequest` as `request`, a
`ProofIntent` as `proof_intent`, and a configured Library `TrustProofs` facade as
`proofs` with a caller-owned `ProofSigner` as `signer`. See
[Library's evaluation and proof examples](https://github.com/tamed-autonomy/kinetic-trust-library/blob/main/README.md).
`ProofIntent` supplies proof ID, resource, context hash, trajectory ID, and
requested lifetime; Library derives decision identity and issuance time from the
evaluation and bounds expiry.

```python
from kinetic_trust_service import (
    EvaluatedWithoutProof,
    IssuedProof,
    Issuer,
    RejectedIssuance,
)

outcome = Issuer(proofs).issue(
    request,
    proof=proof_intent,
    signer=signer,
)

if type(outcome) is RejectedIssuance:
    rejection = outcome.rejection
elif type(outcome) is EvaluatedWithoutProof:
    evaluation = outcome.evaluation
    core_capacity = evaluation.core_capacity
    envelope = evaluation.envelope
    record = outcome.record
else:
    assert type(outcome) is IssuedProof
    evaluation = outcome.evaluation
    core_capacity = evaluation.core_capacity
    envelope = evaluation.envelope
    record = outcome.record
    proof_token = outcome.proof
```

`Issuer` evaluates once. A rejected request returns `RejectedIssuance` without
a record or proof. A valid evaluation produces Library's deterministic
`DecisionRecord`; non-clear Soul assessments return `EvaluatedWithoutProof`,
while Soul-clear evaluations proceed to proof issuance and return `IssuedProof`.
Operational errors propagate to the caller, which owns recovery and
retry/reconciliation.

`evaluation.core_capacity` (Core Capacity Result) and `evaluation.envelope`
(Kinetic Envelope Result) are separate returned facts, not one combined decision.
On the Soul short path, `record.core_capacity_digest` and
`record.capacity_relation` are `None`.

A Soul-clear evaluation can receive a proof even when Envelope supervision is
`SILENT_VETO`. Proof is not permission. These outcomes and
returned records do not establish storage, acceptance, execution, or
enforcement. The product decides whether and how to store results, recover
from operational errors, enforce policy, or execute actions.

## Ownership boundary

Library owns RFC-faithful KTP-Core semantics, deterministic evaluation and proof
rules, and the returned `DecisionRecord`. Service owns only replaceable synchronous
composition. The product owns source authenticity/completeness,
configuration/credentials, storage/retention/transport, retry/reconciliation,
observability, deployment, execution, enforcement, and human interaction.

Library provides independent Trajectory parsing and assessment; Service does
not wrap it or operate a chain, and products may call Library directly.

Service provides no network server, background process, discovery mechanism,
configuration system, persistence, retry loop, or action execution. See
[project terminology](https://github.com/tamed-autonomy/kinetic-trust-service/blob/main/CONTEXT.md)
for the vocabulary and boundary.

## Test a checkout

The supported checkout test installs a wheel built from the Library checkout
under review; it does not add sibling Library source to PYTHONPATH:

    LIBRARY_CHECKOUT=/absolute/path/to/kinetic-trust-library
    WORK_DIR=$(mktemp -d)
    python3 -m venv "$WORK_DIR/venv"
    "$WORK_DIR/venv/bin/python" -m pip install build==1.5.0
    "$WORK_DIR/venv/bin/python" -m build --wheel \
      --outdir "$WORK_DIR/library-dist" "$LIBRARY_CHECKOUT"
    "$WORK_DIR/venv/bin/python" -m pip install --no-index --no-deps \
      "$WORK_DIR/library-dist/kinetic_trust_library-2.1.0-py3-none-any.whl"
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
      "$WORK_DIR/venv/bin/python" -m unittest discover -s tests -t . -v

The suite does not require PyCA. Products choosing Library's optional PyCA
provider install and test it separately.

Maintainers preparing a package publication must follow the
[PyPI release procedure](https://github.com/tamed-autonomy/kinetic-trust-service/blob/main/docs/releasing.md).

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md). Community participation follows
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Report vulnerabilities privately as
described in [SECURITY.md](SECURITY.md), never in a public issue. Protocol
questions belong in the
[official KTP Discussions area](https://github.com/nmcitra/ktp-rfc/discussions).
