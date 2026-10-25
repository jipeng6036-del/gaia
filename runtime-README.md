# GAIA #5482: bounded email relay refusal

## Verified scope

Exact baseline: `82ad2a771c7ed5b6b26f4521b3e4eaad40820f85`. Dedicated candidate: `F:/Github-PR/inspection/sol-high-agent-gaia5482`, branch `fix/refuse-email-turns-with-memory-disabled`. The four-file patch refuses private or globally memory-disabled email turns before sidecar `/init` or `/query`. It does not implement the missing email memory contract. The issue marks the full contract as needing a human; this is its explicitly requested interim refusal, with maintainer review pending. Use `Refs #5482`.

The current frontend deliberately makes every non-`gaia` chat read-only. These screenshots show persisted history, not an email composer send. The current HTTP API explicitly preserves other clients: `security.flagship_only` documents and implements “Requests from other clients pass through unchanged.” Real `/api/sessions` creation and `/api/chat/send` accepted `agent_type=email`; no database was edited by this harness. `X-Gaia-UI: 1` is the route security header, distinct from the optional Agent UI client marker. See `api-contract-evidence.json` for source excerpts.

## Production chain and fixture boundary

Unmodified CLI, ASGI routes, security/memory resolution, database, SSE processing, daemon discovery/startup, installed-artifact SHA verification, version handshake, `acquire_handle`, `SidecarProxy`, and browser history rendering run locally. `launch.py` creates an isolated `HOME/.gaia`, a synthetic `.installed` receipt, and a hash-verified local email executable. The actual daemon spawns that executable and negotiates `apiVersion=2.7`, `agentVersion=0.6.0`. `*-daemon.log` records the spawn, health, and version handshake.

Only the email executable and local Lemonade metadata endpoints are fixtures. `receipt_server.py` records synthetic `/v1/email/init` and `/v1/email/query` bodies and returns a clearly labeled receipt response. Model names/loaded metadata in the UI are synthetic metadata, not model inference. No mailbox credentials, real messages, inference, or paid judge/model were used. The daemon logs an expected nonfatal credential-forwarding warning because this isolated container has no keyring; the sidecar is healthy, and mailbox use is not tested. Launch-secret files are created by the actual daemon; receipt logs omit request headers and tokens. No `acquire_handle` or product-runtime shim is installed; `sitecustomize.py` is only a comment and is absent from `PYTHONPATH`.

The unchanged frontend `/webui` was reused from the prior GAIA validation build. Browser setup-check requests use the supported `skip_chat_model=true` parameter via `scope_browser.js`; their responses still come from the actual route. This avoids claiming model installation/inference acceptance for a relay-only proof.

## Commands and isolation

Container: `ghpr-gaia-5482-ui-ram`, image `ghpr-gaia-snapshot-errors-validation:20261025`, executable `/tmp` tmpfs, `PYTHONDONTWRITEBYTECODE=1`. `baseline.tar` is `git archive` of the exact base; `launch.py` extracts it in `/tmp/gaia5482/<phase>` and overlays the four candidate files only for the candidate. Baseline HTTP/UI proof completed before candidate proof. Distinct homes, SQLite files, daemons, metadata ports, and fixture logs are used per phase.

Run the production entry and controls inside the container:

```text
/core-venv/bin/python /evidence/launch.py baseline
/core-venv/bin/python /evidence/forward.py 18903 18913
/core-venv/bin/python /evidence/http_proof.py baseline
/core-venv/bin/python /evidence/launch.py candidate
/core-venv/bin/python /evidence/forward.py 18923 18933
/core-venv/bin/python /evidence/http_proof.py candidate
```

Each `*-launch.json` records the exact real console command. It is `/core-venv/bin/gaia chat --ui --ui-port <port> --base-url http://127.0.0.1:<metadata-port>/api/v1 --ui-dist /webui`, with `PYTHONPATH` selecting the exact source. The HTTP script uses real memory settings PUT, session POST, chat POST/SSE, and persisted messages GET. Its synthetic user text explicitly says no mail or model access.

Independent wheel verification:

```text
/core-venv/bin/python -m pip install --no-deps --target /tmp/gaia5482-wheel /evidence/amd_gaia-0.25.1-py3-none-any.whl
/core-venv/bin/python /evidence/launch.py wheel
/core-venv/bin/python /evidence/http_proof.py wheel
```

Wheel `PYTHONPATH` contains only `/tmp/gaia5482-wheel`; assertions require both changed modules to resolve there. `wheel-import-proof.json` and `wheel-integrity-proof.json` confirm their runtime hashes equal both checkout and wheel ZIP members. Wheel source does not take precedence through an editable checkout. The wheel used the independently built candidate before the later documentation-only wording correction; the Python contents are identical.

## Actual results

| Production entry | mode | `/init` count | `/query` count | result |
|---|---|---:|---:|---|
| Exact baseline source | on | 1 | 1 | receipt answer; query omits `memory` |
| Exact baseline source | private | 1 | 1 | receipt answer; query omits `memory` |
| Exact baseline source | off | 1 | 1 | receipt answer; query omits `memory` |
| Candidate source | on | 1 | 1 | same receipt answer; query omits `memory` |
| Candidate source | private | 0 | 0 | explicit `agent_error`, failed completion, persisted error |
| Candidate source | off | 0 | 0 | explicit `agent_error`, failed completion, persisted error |
| Independently installed wheel | on | 1 | 1 | same receipt answer; query omits `memory` |
| Independently installed wheel | private | 0 | 0 | explicit refusal, persisted error |
| Independently installed wheel | off | 0 | 0 | explicit refusal, persisted error |

Counts are per-request deltas over actual receipt logs, asserted by `http_proof.py`. Each stream has exactly one `done`. See `baseline-http-proof.json`, `candidate-http-proof.json`, `wheel-http-proof.json`; each also has precise `*-sse.txt`, `*-session.json`, and `*-messages.json` files.

Actual browser screenshots: `baseline-private-before.png`, `baseline-private-refresh.png`, `candidate-private-after.png`, `candidate-private-refresh.png`, and `candidate-off-after.png`. The private toggle, synthetic request, baseline receipt/candidate refusal, and the current retired-composer limitation are visible. Screenshots were visually inspected; browser reload retains the same persisted result.

Focused regression: exact baseline plus the new cases gives 6 failures/3 passes; candidate related relay/profile/proxy/daemon suites give 267 passes. Root owns independent full core/quality/build evidence. No full mail-memory leak is claimed: the baseline proves unsupported flags were dropped, and the candidate proves refusal before dispatch.

Initial environment/setup attempts are retained for audit but are not acceptance evidence: metadata shape, HOME/GAIA_HOME nesting, and Docker overlay I/O caused startup failures. Final RAM runs and the named proof JSON/SSE/log/screenshots are the completed evidence. No other containers were restarted or cleaned.


## Final release wheel verification (completed)

The final release artifact includes the newly built frontend (29 files) and the final LF documentation source. Its exact SHA-256 is `79be6b201ec16223f0b3e2407514b3a38e36aea0bc7a981ba979c466e99d5e8a`. All four recorded release gates in `final-wheel-release-package.json` have exit code 0 (frontend dist verification, build, twine, packaged dist verification).

The final artifact was installed independently with `pip install --no-deps --target /tmp/gaia5482-final-wheel /evidence/final-wheel-dist/amd_gaia-0.25.1-py3-none-any.whl`. New scripts `launch-final-wheel.py` and `http-final-wheel.py` leave the earlier evidence scripts unchanged. This run used a fresh isolated HOME `/tmp/gaia5482-homes/final-wheel`, GAIA_HOME `HOME/.gaia`, metadata port 18962, and real console UI port 18963. `PYTHONPATH` contains only the new installation target; the real console uses `--ui-dist /tmp/gaia5482-final-wheel/gaia/apps/webui/dist`, the final wheel's own bundle.

Actual results are saved in `final-wheel-http-proof.json`: ordinary email-on gives one init and one query with no memory field; private and memory-off each give zero init/query calls, a clear agent_error, a failed terminal completion, and the persisted error. Every request completes once. Precise CLI/SSE/receipt/session/message artifacts use the `final-wheel-` prefix. `final-wheel-daemon.log` confirms actual verified executable startup and version handshake. The same local receipt-only email/metadata boundaries above apply; no mailbox or inference validation is implied.

`final-wheel-integrity-proof.json` asserts the entire wheel SHA, both changed runtime modules against release source hashes and ZIP entries, 29 frontend files, and real HTTP 200 for `/` with a response body exactly equal to the packaged index.html (SHA `ae9dfcabbf82599f0b10bc3056a471cae176ba03080d08379ba9ef75eda89b88`). The installed modules resolve only under `/tmp/gaia5482-final-wheel`.

After collecting evidence, only the owned UI containers were stopped; see `final-wheel-cleanup.json`. Logs and evidence are retained. Product source, root validation containers, and other users' containers were not changed.
