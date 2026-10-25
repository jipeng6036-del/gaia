import datetime as dt
import json
import os
import subprocess
from pathlib import Path

root = Path('/evidence')
env = dict(os.environ, PATH='/core-venv/bin:/opt/node-download/node-v24.14.0-linux-x64/bin:/usr/local/bin:/usr/bin:/bin', GAIA_MEMORY_DISABLED='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1', TMPDIR='/tmp')
files = [
    'tests/integration/test_cli_tool_confirmation.py',
    'tests/integration/test_database_mixin_integration.py',
    'tests/integration/test_database_agent.py',
    'tests/integration/test_context_override_reload.py',
]
command = ['/usr/sbin/runuser', '-u', 'gaia-runner', '--', '/core-venv/bin/python', '-m', 'pytest', *files, '-v', '--tb=short', '--timeout=300', '--junitxml=/evidence/integration.xml']
state = {'started': dt.datetime.now(dt.timezone.utc).isoformat(), 'command': command}
(root / 'integration-state.json').write_text(json.dumps(state, indent=2))
with (root / 'integration.log').open('w') as log:
    state['exit_code'] = subprocess.run(command, cwd='/current', env=env, stdout=log, stderr=subprocess.STDOUT).returncode
state['finished'] = dt.datetime.now(dt.timezone.utc).isoformat()
(root / 'integration-state.json').write_text(json.dumps(state, indent=2))
