# Contributing to Kinetic Trust Service

Thank you for helping improve Kinetic Trust Service. This repository contains
replaceable synchronous composition helpers around Kinetic Trust Library. It
does not define new KTP protocol semantics and does not own product storage,
retry, recovery, action, or enforcement.

## When an issue is required

Open an issue before changing:

- interpretation of a KTP RFC or released conformance artifact;
- a public Python interface or wire representation;
- compatibility or versioning;
- a cryptographic or security boundary; or
- ownership between Library, Service, and consuming products.

Bounded defects, documentation corrections, test maintenance, dependency
updates, and internal refactors may proceed directly as pull requests when
they do not cross those boundaries.

A consequential issue and pull request must identify the pinned KTP tag and
relevant section or artifact, current and proposed behavior, compatibility
impact, test or vector evidence and its limits, the responsible Library,
Service, or product owner, and alternatives considered. Keep one coherent
decision per pull request. Protocol changes belong in the official KTP RFC
repository: https://github.com/nmcitra/ktp-rfc

## Local verification

Build and install a Library wheel; do not add sibling Library source to
PYTHONPATH:

    LIBRARY_CHECKOUT=/absolute/path/to/kinetic-trust-library
    WORK_DIR=$(mktemp -d)
    python3 -m venv "$WORK_DIR/venv"
    "$WORK_DIR/venv/bin/python" -m pip install build==1.5.0
    "$WORK_DIR/venv/bin/python" -m build --wheel \
      --outdir "$WORK_DIR/library-dist" "$LIBRARY_CHECKOUT"
    "$WORK_DIR/venv/bin/python" -m pip install --no-index --no-deps \
      "$WORK_DIR/library-dist/kinetic_trust_library-1.0.0-py3-none-any.whl"
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
      "$WORK_DIR/venv/bin/python" -m unittest discover -s tests -t . -v

Also build and inspect fresh Service wheel and source-distribution artifacts
as required by .github/workflows/ci.yml.

## Pull requests

Explain scope, tests, packaging effect, security considerations, and evidence
limits. Link an issue for an issue-required category. Never include
credentials, private vulnerability details, or unrelated changes.
