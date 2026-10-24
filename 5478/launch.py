"""Start actual production CLI with dedicated state and local model boundary."""
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
CHECKOUT = Path("F:/Github-PR/inspection/gaia-office-watch")
DOCS = ROOT / "documents"
DOCS.mkdir(exist_ok=True)
env = dict(os.environ)
for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GAIA_EVAL_AGENT_PROVIDER", "GAIA_EVAL_CLAUDE_MODEL", "LEMONADE_API_KEY"):
    env.pop(key, None)
env.update(GAIA_HOME=str(ROOT / "candidate-state"), GAIA_MEMORY_DISABLED="1", GAIA_ALLOWED_PATHS=str(DOCS), GAIA_DOCUMENT_ROOTS=str(DOCS), PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
model = subprocess.Popen([str(CHECKOUT / ".venv/Scripts/python.exe"), str(ROOT / "model_boundary.py")], env=env, stdout=(ROOT / "model.log").open("w"), stderr=subprocess.STDOUT)
command = [str(CHECKOUT / ".venv/Scripts/gaia.exe"), "chat", "--ui", "--ui-port", "18793", "--base-url", "http://127.0.0.1:18792/api/v1", "--ui-dist", str(CHECKOUT / "src/gaia/apps/webui/dist")]
ui = subprocess.Popen(command, cwd=CHECKOUT, env=env, stdout=(ROOT / "candidate-cli.log").open("w", encoding="utf8"), stderr=subprocess.STDOUT)
(ROOT / "processes.json").write_text(json.dumps({"model_pid": model.pid, "ui_pid": ui.pid, "command": command}, indent=2))
print(json.dumps({"model_pid": model.pid, "ui_pid": ui.pid, "url": "http://127.0.0.1:18793"}))
