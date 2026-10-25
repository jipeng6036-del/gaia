# GAIA email HTTP memory-mode refusal: reproduction and validation

Source baseline: `82ad2a771c7ed5b6b26f4521b3e4eaad40820f85`. Candidate: `793ba9a26d82f6a3d9fb7cab188885c2ce1b450f` (`fix/refuse-email-turns-with-memory-disabled`). Four files,54 insertions/20 deletions. This implements the interim refusal requested by [issue5482](https://github.com/amd/gaia/issues/5482); the full email memory contract remains open. Independent code/architecture review: [review.md](review.md).

## Actual behavior

The public chat HTTP API accepts email sessions for other clients; the present Agent UI email composer is deliberately read-only. Actual HTTP session creation/send, the CLI server, database/SSE, daemon discovery, verified executable spawn/version handshake, `SidecarProxy`, persisted browser history and reload are exercised. No database is manually edited. Screenshots show the HTTP-created history, not a send through the retired composer.

| Actual entry | mode | email init/query | outcome |
|---|---|---|---|
| Exact baseline | on/private/off | 1/1 each | unsupported memory flag omitted |
| Candidate source | on | 1/1 | ordinary email route preserved, no unsupported field |
| Candidate source | private/off | 0/0 each | explicit agent_error, failed done, persisted error |
| Final wheel in a fresh installation target | on | 1/1 | ordinary route preserved |
| Final wheel in a fresh installation target | private/off | 0/0 each | same refusal and persisted error |

Only the external email executable and Lemonade model metadata endpoints are local fixtures. They record/answer synthetic protocol requests; no mailbox, credentials, model inference or paid judge was used. Acquiring the handle may still start the sidecar before refusal. See [runtime-README.md](runtime-README.md) for precise commands, isolation, versions, launch records, HTTP status/body, SSE and fixture boundaries. `*-launch.json`, `*-http-proof.json`, `*-sse.txt` and `*-messages.json` are the actual outputs.

## Local gates

- Baseline plus new9cases:6fail/3pass; unchanged assertions on candidate:9pass. Related relay/profile/proxy/daemon suites:267pass on Windows; original deprecation warning retained.
- Complete Linux core: **27517 passed, 478 skipped, 3 xfailed, 7 warnings, 41 subtests passed in 447.17s (0:07:27)**; JUnit0failures/0errors. Full commands/time in `clean-core-results.json`, complete log/XML compressed with gzip. Credential-shaped authentication-test parameter IDs are redacted in the public copies; test results, assertions, and counts are unchanged. Original/published hashes and counts are in `test-log-redactions.json`.
- `python util/lint.py --all`:17 blocking checks pass; configured MyPy advisory remains. Module skip guard and hub capability matrix check:pass.
- `npm ci && npm run build` in `src/gaia/apps/webui`:pass (Node24.14.0/npm11.9.0);2391modules,29outputfiles. Frontend lockfile unchanged. Only unused Electron/Playwright binary downloads were disabled; npm lifecycle scripts ran.
- Final build:frontend dist verification, `python -m build`, `python -m twine check`, final wheel dist verification:allpass. Source and final29built web assets verified against wheel ZIP members. Both runtime modules in the final target-installed wheel match source; `/` returns HTTP200 with packaged index.html bytes.
- Final wheel SHA256: `79be6b201ec16223f0b3e2407514b3a38e36aea0bc7a981ba979c466e99d5e8a`. Sdist SHA256: `012fa0168adb06da2f51b4bcf01e9e59b2e7577600dda83aaf30564ddca2e971`. Runtime proof names the same wheel.

Python3.12.14/Linux WSL2 x86_64, standard HOME `/home/gaia-runner`, non-root core runner, exact environment/dependency versions in `environment.json`. Source content hashes in `source-commit.json`/`manifest.json`. No test assertions, timeout or skip policy were weakened.

### Exact core/quality/build commands

```text
python -m pytest tests/unit/ -n4 --dist=worksteal --timeout=180 -v --tb=short --durations=50 --basetemp=/tmp/gaia5482-ram-core --junitxml=/tmp/gaia5482-ram/logs/core.xml
python util/lint.py --all
python util/check_module_skips.py --workflow test_unit.yml --job unit-tests
python hub/agents/gaia/python/packaging/capability_matrix.py --check
# src/gaia/apps/webui, Node24.14.0/npm11.9.0
npm ci
npm run build
# root; precise dist/build/twine invocations in release-package.json
python -m build --outdir /tmp/gaia5482-ram/release-dist
```

Recreate exact sources with `git archive` of the two commits above; run `launch.py`/`http_proof.py` per `runtime-README.md`. The proof exports only synthetic requests and receipts. `final-wheel-integrity-proof.json` verifies artifact/module/frontend identity. The final wheel was tested from its own built frontend; the earlier source UI proof reused an unchanged frontend bundle, clearly identified in the runtime README.

### Environment controls and limits

Earlier complete runs were not green and are preserved: `ram-core-0.log.gz`/`final-core-0.log.gz`. HOME under `/tmp` triggers the filesystem tempguard; exact baseline fails identically and standard HOME passes both. A concurrent frontend install under src causes the Python package scanner to inspect node_modules; the same generated tree produces the same baseline failure. Move generated dependencies outside src, preserve dist, then rerun the **entire** unchanged core suite:the final clean run above passes. `home-control.json` and `frontend-scan-control.json` include identical-condition controls. Host Docker overlay I/O previously stalled an earlier attempt; tmpfs recovered the isolated checks without a claim about the underlying host cause.

478conditional skips and3expected failures are retained, not counted as passes. Scarce-hardware agent evals were not run locally; under CLAUDE.md's next-RC policy, watch `memory`, `gaia_memory`, `gaia_email`. Upstream hosted CI and human maintainer review can only follow PR creation; neither is claimed here. No real mail-memory leak, model behavior, terminal email interaction, or full email memory contract is validated.

All exported files have exact SHA256s in `SHA256SUMS.json`; `.gitattributes` preserves raw evidence bytes.
