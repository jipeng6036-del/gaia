import hashlib
import json
import subprocess
from pathlib import Path

root = Path(__file__).parent
checkout = Path("F:/Github-PR/inspection/gaia-office-watch")
relative = "hub/agents/chat/python/gaia_agent_chat/agent.py"
original = subprocess.check_output(["git", "show", "5981f2128c11d6a04166025a936db7bb36406b93:" + relative], cwd=checkout)
assert original == (root / "baseline-source" / relative).read_bytes()
results = {}
for phase in ("baseline", "candidate"):
    messages = json.loads((root / f"{phase}-messages.json").read_text(encoding="utf-8-sig"))["messages"]
    answers = [m["content"] for m in messages if m["role"] == "assistant" and "Actual indexed text returned" in m["content"]]
    assert answers
    last = answers[-1]
    if phase == "candidate":
        assert last.count("BRAVO") == 4 and "ALPHA" not in last, last
    else:
        assert last.count("ALPHA") == 3 and last.count("BRAVO") == 1, last
    results[phase] = {"last_answer": last}
results.update({"baseline_commit": "5981f2128c11d6a04166025a936db7bb36406b93", "baseline_agent_sha256": hashlib.sha256(original).hexdigest(), "candidate_agent_sha256": hashlib.sha256((checkout / relative).read_bytes()).hexdigest(), "boundary": "Only model HTTP inference and embeddings are deterministic fixtures. Actual gaia CLI, built Agent UI, HTTP routes, flagship GaiaAgent/ChatAgent tools, native watchdog, Office parsing and FAISS updates execute unpatched. No real Lemonade inference or model-generated answer quality is certified."})
(root / "proof.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf8")
print(json.dumps(results, indent=2))
