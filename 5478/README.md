# Office watcher runtime evidence

Issue: https://github.com/amd/gaia/issues/5478

Baseline: `5981f2128c11d6a04166025a936db7bb36406b93`.
Candidate: `1a899844225b2b07fda06e54d756197fca0b6992`. Exact source hashes are recorded in `proof.json`.

## Observed behavior

The same real DOCX, PPTX, XLSX and text fixtures are first indexed with `ALPHA`, then saved with `BRAVO` while the directory is watched.

| Entry point | Word | PowerPoint | Excel | Text control |
| --- | --- | --- | --- | --- |
| Original, after BRAVO save | ALPHA | ALPHA | ALPHA | BRAVO |
| Candidate, after BRAVO save | BRAVO | BRAVO | BRAVO | BRAVO |

`baseline-after-bravo-save.png` and `candidate-bravo.png` are unmodified Playwright viewport screenshots from the actual built Agent UI served by `gaia chat --ui`. The persisted HTTP conversation responses are checked by `check_proof.py`; `proof.json` contains their final text.

## Boundary

Only the external model HTTP service is a deterministic fixture (`model_boundary.py`). It chooses the requested tools and formats their actual returned text; embeddings use deterministic vectors. It does not open or parse the Office documents. This does **not** validate real Lemonade/Gemma inference, model-generated answer quality, or GPU behavior.

The production `gaia` CLI, frontend, HTTP routes, flagship `GaiaAgent`/`ChatAgent`, tool dispatch, native watchdog observer, Office parsers, RAG cache and FAISS index updates run unchanged. The screenshot's model name is the fixture's protocol model ID, not a claim that Gemma was loaded. No paid service is called.

## Exact local procedure

Windows, Python 3.12.13, Node 24.14.0, npm 11.16.0. Dependency versions and the tested agent SHA-256 are recorded in `environment.txt`.

1. Install `.[dev,rag,ui,api]`, the editable chat and flagship agent packages, and the unit workflow's dependencies. Run `npm ci` and `npm run build` under `src/gaia/apps/webui`.
2. Run `model_boundary.py` on `127.0.0.1:18792`. `launch.py` starts the actual candidate CLI with a dedicated `GAIA_HOME` and filesystem roots. `prepare_baseline.py` extracts the exact baseline, verifies imports through its source roots, and starts the same CLI executable against baseline source in separate state on port 18794.
3. Actual CLI command (candidate; baseline uses port 18794):

   ```text
   .venv/Scripts/gaia.exe chat --ui --ui-port 18793 --base-url http://127.0.0.1:18792/api/v1 --ui-dist src/gaia/apps/webui/dist
   ```

   Output: `Starting GAIA Agent UI on http://127.0.0.1:18793`. The frontend is actually served from the built dist. Absolute paths used in the scripts correspond to the isolated local validation workspace.

4. Create each session through `POST /api/sessions` with `agent_type=gaia`, `device=cpu`, and a fixture-labelled title. Open its real UI with `npx --package @playwright/cli playwright-cli`.
5. Type `FIXTURE_WATCH <fixture-directory>` in the visible chat. The HTTP fixture chooses `add_watch_directory`; the real agent starts its observer. The `--watch` CLI option is not used to seed this UI-only flow.
6. Run `save_documents.py ALPHA <fixture-directory>`. In the baseline session, explicitly index each Office file using `FIXTURE_INDEX <path>` in chat, since the original watcher ignores their creation. Query `FIXTURE_SEARCH officewatch` in both UIs; the actual `search_indexed_chunks` tool returns all four ALPHA chunks. Capture initial screenshots.
7. Run the same save script with `BRAVO`. Allow native file events to settle, then issue the same search through the visible chat. Capture the before/fix comparison screenshots. The original retains three stale ALPHA chunks; the candidate returns four BRAVO chunks.
8. Fetch each session's persisted `/api/sessions/<id>/messages` response and run `check_proof.py`. It checks the original source against `git show`, then asserts baseline `3×ALPHA/1×BRAVO` and candidate `0×ALPHA/4×BRAVO`.

The browser, CLI instances and model fixture were shut down after proof capture. These scripts are validation material, not changes to the product.

## Regression checks

Commands a reviewer can run from the candidate checkout (with the chat/RAG dependencies installed):

```text
python -m pytest hub/agents/chat/python/tests/test_chat_agent_rag_offline.py -k watched -q
python -m pytest hub/agents/chat/python/tests/ tests/unit/test_file_watcher.py tests/unit/test_file_watcher_settle.py -v --timeout=180
python util/lint.py --all
```

For the failing control, extract the exact baseline into a separate directory, copy only the candidate's `hub/agents/chat/python/tests/test_chat_agent_rag_offline.py` into that directory, and run the first command with baseline source roots on `PYTHONPATH`. The production baseline file must retain the SHA-256 recorded in `proof.json`; copying the new regression tests does not apply the fix. The recorded control yielded 7 failures and 4 passes, with 25 unrelated tests deselected.

- Exact original production source with the final new regressions: **7 failed, 4 passed**. The failures are the six lower/uppercase Office saves and the Office rename-save case.
- Final chat package plus both core file-watcher suites: **185 passed, 1 conditional skip**. This includes real Office parsing/FAISS and a native observer, ordinary text preservation, owner-file exclusion, rename-save filtering and existing locked-file retries.
- `python util/lint.py --all`: **18 checks, 17 passed and 1 explicitly non-blocking advisory warning**. Final Black/isort recheck passes with no warnings.
- `python -m pytest tests/unit/test_packaging.py -q`: **13 passed**.
- Full Linux core CI profile (`.[api]`, no installed Hub-agent packages): **27427 passed, 478 skipped, 3 xfailed, 7 warnings, 41 subtests passed**; exit 0, coverage in `final-core-coverage.xml`. The upstream collection-skip allowlist passed unchanged.
- Linux affected chat/watcher lane: **184 passed, 2 Windows-lock skips**. Those real lock tests pass on Windows; the Windows affected lane skips one unavailable-symlink case.
- Initial Linux core run found four missing-pip failures. All four also failed against exact baseline in the same environment. After `python -m ensurepip --upgrade`, all four passed on both revisions; the entire core suite was then rerun successfully. No test or product code was changed for this environment repair.
- A further six-worker run on the container overlay was interrupted after three concurrency failures; it is not counted as a passing full run. The exact baseline separately reproduced the configuration lock timeout. All three focused concurrency cases then passed on both revisions with temporary files on tmpfs. The final complete core run uses four workers, a 4GiB tmpfs for `/tmp`, and a fresh 1GiB tmpfs home; it uses real filesystem/lock calls and unchanged tests/timeouts.
- Additional Windows full developer-profile run: **not successful**; pytest timer threads exhausted resources. Of eleven captured failures, exact-baseline controls also failed all eleven; after activating PATH and isolating frontend node_modules, both revisions had seven passes and the same four unrelated shell/venv failures. This is not a Windows full-suite pass. Hosted cross-platform CI remains separate.

Source review found no correctness findings. Real runtime screenshots were inspected separately; the source reviewer did not claim to validate the browser evidence.

## Full core command and provenance

Linux Python 3.12.14, Node 24.14.0, npm 11.9.0, non-root uid 1000. The `[api]` profile uses the dependencies declared by `.github/workflows/test_unit.yml`; the Hub/chat lane uses its own complete parser/agent environment.

```text
/core-venv/bin/python -m pytest tests/unit/ -n 4 --dist=worksteal --timeout=180 -v --tb=short --durations=50 --basetemp=/tmp/gaia-core-pytest --cov=src/gaia --cov-report=term-missing --cov-report=xml:/evidence/final-core-coverage.xml --junitxml=/evidence/final-core-unit.xml
```

The full log summary and coverage, focused pip controls, source hashes, and JUnit-derived counts are included here. Summary text files are explicitly tail excerpts, not complete logs. `model_boundary.py`, the document writer and launch scripts are the actual local validation helpers; their checkout/state path constants must be adjusted when reproducing in another isolated workspace. Fetch the generated session message JSON before running `check_proof.py`. The model fixture writes request bodies to a local JSONL file; that session log is not included in this evidence branch.

The Linux container reused locally installed dependencies; its image was not published. The runtime flags were `--init --cpus 4 --memory 12g --tmpfs /tmp:rw,exec,size=4g,mode=1777 --tmpfs /home/gaia-runner:rw,exec,size=1g,mode=755,uid=1000,gid=1000`. `core-requirements.txt` records its 96 non-editable package versions; GAIA itself is installed editable with `.[api]`. The first tmpfs setup had Docker's default `noexec`, so its temporary-executable failures were retained and that attempt stopped. The final setup explicitly enables execution and verifies a real executable as uid 1000 before collection.
