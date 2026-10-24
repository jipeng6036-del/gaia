import io
import json
import os
import subprocess
import zipfile
from pathlib import Path

root = Path(__file__).parent
checkout = Path("F:/Github-PR/inspection/gaia-office-watch")
baseline = root / "baseline-source"
sha = "5981f2128c11d6a04166025a936db7bb36406b93"
archive = subprocess.check_output(["git", "archive", "--format=zip", sha], cwd=checkout)
with zipfile.ZipFile(io.BytesIO(archive)) as source:
    source.extractall(baseline)
docs = root / "baseline-documents"
docs.mkdir(exist_ok=True)
state = root / "baseline-state"
state.mkdir(exist_ok=True)
(state / "config.json").write_text('{"default_device":"cpu"}')
env = dict(os.environ)
for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GAIA_EVAL_AGENT_PROVIDER", "GAIA_EVAL_CLAUDE_MODEL", "LEMONADE_API_KEY"):
    env.pop(key, None)
env.update(GAIA_HOME=str(state), GAIA_MEMORY_DISABLED="1", GAIA_ALLOWED_PATHS=str(docs), GAIA_DOCUMENT_ROOTS=str(docs), PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONPATH=os.pathsep.join(str(baseline / p) for p in ("src", "hub/agents/chat/python", "hub/agents/gaia/python")))
command = [str(checkout / ".venv/Scripts/gaia.exe"), "chat", "--ui", "--ui-port", "18794", "--base-url", "http://127.0.0.1:18792/api/v1", "--ui-dist", str(checkout / "src/gaia/apps/webui/dist")]
proc = subprocess.Popen(command, cwd=baseline, env=env, stdout=(root / "baseline-cli.log").open("w", encoding="utf8"), stderr=subprocess.STDOUT)
print(json.dumps({"baseline": sha, "ui_pid": proc.pid, "command": command, "pythonpath": env["PYTHONPATH"]}))
(root / "baseline-process.json").write_text(json.dumps({"baseline": sha, "ui_pid": proc.pid, "command": command, "pythonpath": env["PYTHONPATH"]}, indent=2))
