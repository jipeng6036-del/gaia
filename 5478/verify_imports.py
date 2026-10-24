import json
import os
import subprocess
from pathlib import Path

root = Path(__file__).parent
checkout = Path("F:/Github-PR/inspection/gaia-office-watch")
baseline = root / "baseline-source"
env = dict(os.environ)
env.update(GAIA_HOME=str(root / "import-probe-state"), GAIA_MEMORY_DISABLED="1", PYTHONIOENCODING="utf-8")
code = "import gaia,gaia_agent,gaia_agent_chat.agent as a,pathlib,hashlib,json;print(json.dumps({'core':gaia.__file__,'flagship':gaia_agent.__file__,'chat':a.__file__,'chat_sha256':hashlib.sha256(pathlib.Path(a.__file__).read_bytes()).hexdigest()}))"
results = {}
for phase, source in (("baseline", baseline), ("candidate", checkout)):
    env["PYTHONPATH"] = os.pathsep.join(str(source / p) for p in ("src", "hub/agents/chat/python", "hub/agents/gaia/python"))
    result = subprocess.check_output([str(checkout / ".venv/Scripts/python.exe"), "-c", code], cwd=source, env=env, text=True)
    info = json.loads(result.strip().splitlines()[-1])
    for key in ("core", "flagship", "chat"):
        assert Path(info[key]).is_relative_to(source), info
    results[phase] = info
(root / "imports.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf8")
print(json.dumps(results, indent=2))
