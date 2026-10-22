# PyPI release procedure

This procedure publishes Kinetic Trust Service from one clean, reviewed
commit. Service and Library package `major.minor` versions track the implemented
KTP RFC series, while each package advances patch versions independently. A
package patch release does not imply a new KTP specification version.

## Publication boundary

The repository contains a tag-triggered Trusted Publishing workflow, but its
presence does not authorize a release. Pushing a matching version tag starts
publication; it is not a dry run. Tag creation and package publication require
separate approval after the checks below are complete.

The workflow separates an unprivileged build job from its OIDC-enabled publish
job. It builds the wheel and source distribution once, retains those exact
files as a workflow artifact, and publishes those same bytes. The official
PyPI action produces Sigstore attestations by default. No PyPI password or API
token belongs in GitHub secrets.

## One-time Trusted Publishing setup

Before the first tag is pushed, configure a pending PyPI Trusted Publisher with
these exact values:

- PyPI project: `kinetic-trust-service`
- GitHub owner: `tamed-autonomy`
- GitHub repository: `kinetic-trust-service`
- workflow filename: `release.yml`
- environment: `pypi`

Create the matching GitHub `pypi` environment. Restrict its deployments to
tags matching `v*` and require approval by the designated release reviewer.
Under the current single-maintainer governance model, allow that maintainer to
approve a deployment they initiated. If an independent release reviewer is
formally appointed, prevent the initiator from approving their own deployment.
Adjust the tag ruleset so an authorized maintainer can create a new tag while
tag updates and deletions remain blocked.
Do not weaken branch protection or permit mutable release tags. The workflow
also rejects a tag whose target is not reachable from `main`.

## Preconditions

Before publishing Service `2.1.0`:

1. Require the exact reviewed commit on `main` to pass CI and CodeQL.
2. Build and inspect fresh Service wheel and source-distribution artifacts as
   required by `.github/workflows/ci.yml`.
3. Confirm `kinetic-trust-library==2.1.0` is already visible and installable
   from PyPI. This is a release-order gate, not a new Service runtime feature.
4. Confirm the Trusted Publisher, GitHub environment, and immutable-tag rules
   above are active.
5. Obtain separate approval to publish.

## Publish and verify

Create and locally verify a signed, annotated tag whose name is exactly `v`
plus the version in `pyproject.toml`; for this release it is `v2.1.0`. Pushing
that tag starts `.github/workflows/release.yml`. The workflow rejects every tag
that does not exactly match the package version.

After the workflow succeeds, verify the PyPI metadata and provenance, then use
a fresh environment to confirm that PyPI resolves both packages:

```console
python3 -m venv /tmp/kinetic-trust-service-release-check
/tmp/kinetic-trust-service-release-check/bin/python -m pip install \
  --no-cache-dir 'kinetic-trust-service==2.1.0'
/tmp/kinetic-trust-service-release-check/bin/python -c \
  'from importlib.metadata import version; assert version("kinetic-trust-service") == "2.1.0"; assert version("kinetic-trust-library") == "2.1.0"'
```

This procedure and its automation establish neither application conformance
nor release approval. Products still own storage, keys, transport, retries,
failure handling, action, and enforcement.
