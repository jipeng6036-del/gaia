# GAIA #5666: retain the turn error when saving undo also fails

Baseline production: `82ad2a771c7ed5b6b26f4521b3e4eaad40820f85`.
Candidate, three Git blobs, commands, versions, complete-log hashes and actual test counts are in `manifest.json`.

## Actual user path

The same built frontend and the real `gaia chat --ui --ui-port 18803 --base-url http://127.0.0.1:18802/api/v1 --ui-dist /webui` run against each exact source tree. Browser traffic goes through the normal Agent UI, daemon, documented dev sidecar, canonical query endpoint, real `GaiaAgent`, and real `write_file` tool. A loopback-only Docker port forward makes that browser reachable from the host. The ordinary Ask-mode prompt is approved once for the isolated `/documents/proof.txt` file.

An isolated Hub binary-install **receipt fixture** selects the normal relay instead of the wheel's in-process route, with `GAIA_GAIA_AGENT_MODE=dev`. No frozen binary download/install is being certified. The production registry/daemon/relay/server code is not patched for the proof.

`model_boundary.py` scripts only the external model HTTP replies. The first reply asks the real tool to create the file; after receiving its actual result, the fixture fills **only** the separate 1 MiB tmpfs mounted at `/state/snapshots`, checking both the mount identity and capacity first. A subsequent non-object tool-argument reply triggers an uncaught processing exception on this baseline. `recording_turn` then hits genuine OS `ENOSPC` copying the real after-image. The original processing failure is intentionally the independently tracked #5471 case; this server-side fix is directly based on main and does not stack #5732's parser fix.

Before: the browser reports the generic “This is a bug” text. After: the same two failures preserve `AttributeError: 'str' object has no attribute 'get'`, with undo warnings preceding the error. The real copy failure suppresses exception context (`raise ... from None`), so the original traceback is explicitly logged as well as the undo failure. That detail was discovered in the actual runtime proof and covered before submission.

The browser is reloaded and persisted messages/outputs/changes are fetched from its actual API. Four raw PNGs are unedited. `verify_runtime.py` checks six full UI→daemon→sidecar HTTP streams: double failure, successful processing + failed undo, and failed processing without failed undo, for both revisions. The two controls preserve existing behavior. `candidate-ui-sse.txt` is also the actual browser response body. UI framing uses `agent_error`/`done`; the sidecar's canonical framing is separately covered by the new endpoint regressions.

This is deterministic HTTP-boundary testing, **not** real model inference, Lemonade/GPU compatibility, a model-quality score or production acceptance. No paid API/judge or external coding model was called. Under the repository's hardware exception, the next RC should watch `error_recovery`.

## Reproduction environment

- Linux Python 3.12.14; Windows Python version and dependencies in `windows-environment.json`; separate core and hub package profiles in `*-environment.json`.
- Core profile follows `[dev,api]`/the existing core lane. Hub profile includes the flagship/chat, UI/API/browser/parser/publish dependencies. Node/npx is on PATH for the full tool registry. Tests run as a normal Linux user, with real Docker `--init`, an executable 4 GiB test tmpfs, and BLAS thread limits.
- Re-create the two trees with the exact baseline/candidate commits, install their declared profiles, build the unchanged frontend, mount this evidence folder at `/evidence`, mount a dedicated 1 MiB snapshot tmpfs at `/state/snapshots`, and expose only loopback port 18813. `setup.py`, `launch.py`, `forward.py`, `model_base.py`, `model_boundary.py`, `http_proof.py`, `reset_fault.py`, `capture_ui.py` and `verify_runtime.py` record the executed harness. The local validation image name is not a published dependency.
- Final production source and independent installed core/chat/flagship wheel imports match; `wheel-import.json` explicitly lists module paths. This certifies import parity, not a second wheel-runtime run. The wheel build has the same missing README/long_description warning on exact baseline; both builds and Twine validation succeed.

## Validation and recovered setup failures

Final completed results and every conditional skip reason are machine-readable in `manifest.json`/`skips.json`. No test, assertion or timeout was weakened, and no unrelated production code was changed.

- The final new regression overlay on baseline production gives **4 failures / 9 passes**; the candidate endpoint suite passes all 13. It covers RuntimeError, ValueError, OSError and SnapshotError, including suppressed undo context, actual file mutation, one last terminal error and released session locks.
- The first core attempt used a container without init and a token-shaped scratch path. All 12 failing nodes fail on both revisions under that same setup, then all 12 pass on both with real init/plain scratch. The required final complete core run uses the repaired environment; its full result is separate from those controls.
- Omitting Node/npx causes the same three registry failures on baseline. Correcting PATH restores them. Repeated earlier suites also exhausted the separate 4 GiB test tmpfs; an identical oversized-file case fails with `ENOSPC` on both revisions. Only explicitly named owned scratch directories were removed, after retaining logs, before the final complete flagship rerun.
- A plain-copy assertion rejects the word `sidecar` anywhere in its output, including the *temporary directory*. Its initial contract run used that word in `--basetemp`. Both revisions fail with that path and pass with a plain path. The final full affected-contract run uses the plain path.
- An **additional fixture-enabled** relay test reaches its old fake `_Handler`, which lacks `set_relay_question`; exact baseline and candidate both report **1 failed / 3 passed**. This diagnostic is not counted as green. The normal workflow run conditionally skips the query when no real Lemonade backend is available; this patch retains that policy. The actual browser proof uses the production handler and passes through the complete affected path. No production/helper test was altered to hide the diagnostic.
- The optional old Python 3.10 environment had no installed flagship and collected no tests. That attempt is not a compatibility pass. Required Linux/Windows suites and the actual runtime versions are recorded separately.

Native independent code/architecture review approved the final patch; see `review.txt`. Human review and hosted PR CI remain distinct from local evidence. There is no merge/release/CLA attestation here.
