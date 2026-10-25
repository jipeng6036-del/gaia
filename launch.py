import json
import os
import subprocess
import sys
from pathlib import Path

phase = sys.argv[1]
source = Path('/5666') / phase
root = Path('/evidence')
env = dict(os.environ)
for key in list(env):
    if key.endswith('API_KEY') or key.startswith('GAIA_EVAL_'):
        env.pop(key)
env.update(PYTHONPATH=os.pathsep.join(str(source / part) for part in ['src', 'hub/agents/chat/python', 'hub/agents/gaia/python']),
           GAIA_HOME='/state', GAIA_MEMORY_DISABLED='1', GAIA_CTX_SIZE='32768',
           GAIA_GAIA_AGENT_MODE='dev', LEMONADE_BASE_URL='http://127.0.0.1:18802/api/v1',
           GAIA_ALLOWED_PATHS='/documents', GAIA_DOCUMENT_ROOTS='/documents',
           PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
command = ['/core-venv/bin/gaia', 'chat', '--ui', '--ui-port', '18803', '--base-url', env['LEMONADE_BASE_URL'], '--ui-dist', '/webui']
proc = subprocess.Popen(command, cwd=source, env=env, stdout=(root / f'{phase}-cli.log').open('w'), stderr=subprocess.STDOUT)
(root / f'{phase}-launch.json').write_text(json.dumps({'phase': phase, 'pid': proc.pid, 'command': command, 'source': str(source), 'pythonpath': env['PYTHONPATH']}, indent=2))
print(proc.pid)
