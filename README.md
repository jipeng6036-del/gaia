# Non-object tool arguments: real CLI and Agent UI proof

Issue: https://github.com/amd/gaia/issues/5471

Baseline: `82ad2a771c7ed5b6b26f4521b3e4eaad40820f85`.
Candidate: `ada550c412069392b14df926401d4fcadcf15cb3`. Per-file Git blobs are recorded in the manifest.

## Observed behavior

| Model HTTP reply | Original Agent UI / persisted response | Candidate |
| --- | --- | --- |
| JSON tool call, string arguments | `Agent error: 'str' object has no attribute 'get'` | Model receives the named parse error, corrects to an object, real `file_info` runs and answers |
| JSON tool call, list arguments | `Agent error: 'list' object has no attribute 'get'` | Same successful recovery |
| Native OpenAI tool call, string arguments | `Agent error: 'str' object has no attribute 'get'` | Same successful recovery |
| Native OpenAI tool call, list arguments | `Agent error: 'list' object has no attribute 'get'` | Same successful recovery |

`http-proof.json` records eight fresh sessions and their real persisted messages.
The four screenshots are unmodified Playwright viewport captures (1440×1000).
The candidate answer also survives a browser reload.

## Runtime boundary

Only the external model HTTP responses are scripted by `model_boundary.py` (shared
health/metadata handlers are in `model_base.py`). Native cases return real
OpenAI-shaped `message.tool_calls` / SSE `delta.tool_calls`; they are not injected
directly into GAIA's parser. The next request must contain GAIA's actual recovery
message before the fixture returns corrected object arguments. The fixture formats
the actual returned tool text. It never reads `proof.txt` itself.

The real `gaia chat --ui` CLI, built frontend, HTTP/SSE routes, flagship GaiaAgent,
base parser/recovery loop, registered `file_info` and filesystem calls run unchanged.
Session titles explicitly say HTTP fixture/no inference. This is not a claim of
real Gemma/Lemonade inference, GPU validation, or model answer quality. No paid
service is called.

Windows runtime: Python3.12.13, Node24.14.0. The original and candidate use the same
built frontend and model boundary, separate GAIA_HOME directories, and explicit
CPU sessions with access limited to the proof directory.

## Reproduce the user flow

Adjust the checkout constant in `launch.py` / `cli_proof.py` to your isolated clone.
Install the core UI extras and the local chat/flagship hub packages, then build the
frontend using the repository's current development instructions.

1. Export the exact baseline into `baseline.tar`. On Git for Windows use
   `git -c core.autocrlf=false archive <baseline> --output baseline.tar` when preparing
   a POSIX run; otherwise the archive can rewrite shell scripts to CRLF.
2. Run `python launch.py`. It starts the model fixture at127.0.0.1:18802, original
   Agent UI at18804, and candidate at18803 with isolated state. It strips the API
   credential variables listed in the script.
3. Create CPU sessions using `POST /api/sessions` (`agent_type=gaia`,
   `model=Gemma-4-E4B-it-GGUF`, `device=cpu`), with the standard `X-Gaia-UI: 1` header.
   Use a custom title so session-title generation is separate from the test.
4. In the actual visible chat send
   `Read metadata for proof.txt. Deterministic HTTP fixture test: JSON_STRING`.
   The original shows the exception; the candidate reads the real file metadata.
5. `http_proof.py` runs the same HTTP/SSE entry for JSON_LIST, NATIVE_STRING and
   NATIVE_LIST in separate sessions and checks all persisted responses. Open each
   recorded browser URL to inspect it. Refresh the candidate page to check recovery.
6. `cli_proof.py` runs the real non-interactive `gaia chat --query ... --device cpu`
   in original, candidate and installed-wheel environments. Original exits1 in
   both sampled modes; candidate and wheel exit0 and return real metadata.

The wheel probe runs outside the source tree with no PYTHONPATH, verifies that
`gaia.agents.base.agent` imports from its own site-packages, and checks its bytes
against the built candidate source. Exact commands/output are in `cli-proof.json`
and `cli-*.log`.

## Regression and review scope

`tests/unit/agents/test_tool_args_object.py` runs real process_query with scripted
model responses, both streaming and non-streaming. It covers direct/embedded JSON,
native calls, string/list/empty-list/null/bool/number arguments, correction and
actual tool execution, no-argument compatibility, falsy tool names, the existing
three-error budget, no partial execution of a malformed parallel batch, and the
step-cap closing reply's retry without tools. The new70 tests produce48FAIL/22PASS
on the exact original production code and70PASS on the candidate.

Native independent code and architecture review found and corrected two initial
regressions (falsy tool names and closing replies), then reported no remaining
material findings. Its independent16-case rerun passed. This is not human approval.
Plan-only malformed arguments are a preexisting adjacent limitation, outside5471.

`gaia eval agent` was not run: the current project convention explicitly allows
contributors without the Strix Halo pool to list the next RC categories. Watch
`tool_selection` and `error_recovery`; no Claude/paid judge was invoked here.

Full-suite results, environment versions, initial failed attempts and repairs are
recorded in the final manifest and validation logs. Hosted CI is separate and can
only be triggered after the PR exists.

Two local harness pitfalls were diagnosed without changing production or tests:
the first Windows archive converted extensionless Debian scripts to CRLF (the same
six failures reproduced on both revisions, then both149-test controls passed from
the LF archive); and `/tmp/gaia-5471-baseline` resembled a credential token to the
existing conservative memory redactor. Its source-path provenance made an unrelated
memory test redact its inventory. The unchanged original and candidate each fail
that test under a credential-shaped temp path and pass under a plain-letter path.
Final complete runs use `/tmp/gaia-tool-args-baseline` and
`/tmp/gaia-tool-args-candidate`. No credential filter, assertion, test or timeout was
weakened. The original failed logs remain separate from successful validation.

The additional Hub package suites run separately, matching their CI workflows;
combining their un-packaged test directories initially caused duplicate Python
module names at collection. A subsequent run exhausted the container's isolated
4 GiB scratch tmpfs because completed full-core runs had retained 3.2 GiB there.
Only the verified generated pytest scratch directories were reclaimed. Final
serial package runs reuse one scratch directory, without changing source, tests
or assertions. Both unsuccessful attempts remain separate local artifacts.
The email lane also uses its own workflow environment: unlike chat/flagship, it
must not inherit `GAIA_MEMORY_DISABLED=1`, since its memory tests mock the
embedder and deliberately check persisted learning. The initial email run with
that inherited flag was interrupted and is not counted as a pass.
The root package installer also left ignored email `egg-info` metadata owned by
root; nonroot pytest could not update it in the real sdist test. Restoring the
generated metadata's ownership permits the unchanged complete email lane to run.


## Completed local validation

```text
full-lf-baseline.log: = 27508 passed, 478 skipped, 3 xfailed, 7 warnings, 41 subtests passed in 506.06s (0:08:26) =
full-lf-candidate.log: = 27578 passed, 478 skipped, 3 xfailed, 7 warnings, 41 subtests passed in 514.86s (0:08:34) =
integration.log: ============================== 77 passed in 8.94s ==============================
hub-chat-tests.log: ======================= 109 passed, 2 skipped in 32.26s ========================
hub-gaia-tests.log: ======================= 792 passed, 3 skipped in 54.07s ========================
hub-tests.log: ============ 3524 passed, 4 skipped, 2 warnings in 65.79s (0:01:05) ============
Windows affected agents:4170PASS/55conditionalSKIP; focused75PASS; Python3.10 compatibility72PASS/1config warning.
Lint:17PASS/1configured advisory; packaging13PASS; frontend/wheel builds and source+installed-wheel CLI proof passed.
```
