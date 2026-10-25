import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE = Path('F:/Github-PR/inspection/gaia-tool-arguments')
results = []
for phase, source in [('baseline', ROOT / 'baseline-source'), ('candidate', SOURCE), ('wheel', None)]:
    scripts = (SOURCE / '.venv/Scripts') if phase != 'wheel' else ROOT / 'wheel-venv/Scripts'
    env = dict(os.environ)
    for key in ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'LEMONADE_API_KEY', 'GAIA_EVAL_AGENT_PROVIDER', 'GAIA_EVAL_CLAUDE_MODEL', 'PYTHONPATH']:
        env.pop(key, None)
    if source:
        env['PYTHONPATH'] = os.pathsep.join(str(source / p) for p in ['src', 'hub/agents/chat/python', 'hub/agents/gaia/python'])
    env.update(PATH=str(scripts) + os.pathsep + env['PATH'], GAIA_MEMORY_DISABLED='1', GAIA_CTX_SIZE='32768', GAIA_ALLOWED_PATHS=str(ROOT / 'documents'), PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    for mode in ['JSON_STRING', 'NATIVE_LIST']:
        env['GAIA_HOME'] = str(ROOT / f'cli-{phase}-{mode}-state')
        command = [str(scripts / 'gaia.exe'), 'chat', '--device', 'cpu', '--base-url', 'http://127.0.0.1:18802/api/v1', '--allowed-paths', str(ROOT / 'documents'), '--query', 'Read metadata for proof.txt. Deterministic HTTP fixture test: ' + mode]
        with (ROOT / f'cli-{phase}-{mode}.log').open('w', encoding='utf8') as log:
            run = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=180)
        text = (ROOT / f'cli-{phase}-{mode}.log').read_text(encoding='utf8')
        recovered = 'Metadata read successfully by the real GAIA file_info tool' in text
        if phase == 'baseline':
            assert 'object has no attribute' in text and not recovered
        else:
            assert run.returncode == 0 and recovered, (phase, mode, text[-2000:])
        row = {'phase': phase, 'mode': mode, 'exit_code': run.returncode, 'recovered': recovered, 'command': command}
        results.append(row)
        print(row, flush=True)
    imports = subprocess.check_output([str(scripts / 'python.exe'), '-c', 'import gaia.agents.base.agent as a; print(a.__file__)'], env=env, cwd=ROOT, text=True).strip()
    results[-1]['agent_import'] = imports
    if phase == 'wheel':
        assert 'site-packages' in imports and 'inspection' not in imports
        assert hashlib.sha256(Path(imports).read_bytes()).digest() == hashlib.sha256((SOURCE / 'src/gaia/agents/base/agent.py').read_bytes()).digest()
(ROOT / 'cli-proof.json').write_text(json.dumps(results, indent=2))
