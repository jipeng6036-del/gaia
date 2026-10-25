import json
import os
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE = Path('F:/Github-PR/inspection/gaia-tool-arguments')
BASE = ROOT / 'baseline-source'
BASE.mkdir(exist_ok=True)
with tarfile.open(ROOT / 'baseline.tar') as archive:
    archive.extractall(BASE, filter='data')
(ROOT / 'documents').mkdir(exist_ok=True)
(ROOT / 'documents/proof.txt').write_text('GAIA_TOOL_ARGS_OBJECT_RUNTIME_PROOF\n', encoding='utf8')
env = dict(os.environ)
for key in ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'LEMONADE_API_KEY', 'GAIA_EVAL_AGENT_PROVIDER', 'GAIA_EVAL_CLAUDE_MODEL']:
    env.pop(key, None)
python = str(SOURCE / '.venv/Scripts/python.exe')
model = subprocess.Popen([python, str(ROOT / 'model_boundary.py')], env=env, stdout=(ROOT / 'model.log').open('w'), stderr=subprocess.STDOUT)
processes = {'model': model.pid}
for phase, source, port in [('baseline', BASE, 18804), ('candidate', SOURCE, 18803)]:
    paths = [source / 'src', source / 'hub/agents/chat/python', source / 'hub/agents/gaia/python']
    run_env = dict(env, PYTHONPATH=os.pathsep.join(map(str, paths)), GAIA_HOME=str(ROOT / (phase + '-state')), GAIA_MEMORY_DISABLED='1', GAIA_CTX_SIZE='32768', GAIA_ALLOWED_PATHS=str(ROOT / 'documents'), GAIA_DOCUMENT_ROOTS=str(ROOT / 'documents'), PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    command = [str(SOURCE / '.venv/Scripts/gaia.exe'), 'chat', '--ui', '--ui-port', str(port), '--base-url', 'http://127.0.0.1:18802/api/v1', '--ui-dist', str(SOURCE / 'src/gaia/apps/webui/dist')]
    proc = subprocess.Popen(command, cwd=source, env=run_env, stdout=(ROOT / (phase + '-cli.log')).open('w', encoding='utf8'), stderr=subprocess.STDOUT)
    processes[phase] = {'pid': proc.pid, 'port': port, 'source': str(source), 'command': command}
(ROOT / 'processes.json').write_text(json.dumps(processes, indent=2))
print(json.dumps(processes))
