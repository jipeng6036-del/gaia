import datetime as dt
import json
import os
import subprocess
from pathlib import Path

r = Path('/evidence')
source = '/5666/candidate'
env = dict(os.environ, PATH='/core-venv/bin:/opt/node-download/node-v24.14.0-linux-x64/bin:/usr/local/bin:/usr/bin:/bin', GAIA_MEMORY_DISABLED='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1', TMPDIR='/tmp', PYTHONPATH=source + '/src')
state = {'started': dt.datetime.now(dt.timezone.utc).isoformat(), 'init': Path('/proc/1/comm').read_text().strip()}
assert state['init'] == 'docker-init', state
prefix = ['/usr/sbin/runuser', '-u', 'gaia-runner', '--']
def run(name, python, args):
    state['stage'] = name
    (r / 'final-tests-state.json').write_text(json.dumps(state, indent=2))
    command = [*prefix, python, *args]
    with (r / (name + '.log')).open('w') as log:
        code = subprocess.run(command, cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
    state[name] = {'exit': code, 'command': command}
    (r / 'final-tests-state.json').write_text(json.dumps(state, indent=2))
    if code:
        raise SystemExit(code)

run('final-core-unit', '/core-venv/bin/python', ['-m', 'pytest', 'tests/unit/', '-n', '4', '--dist=worksteal', '--timeout=180', '-v', '--tb=short', '--durations=50', '--basetemp=/tmp/gaia-snapshot-core', '--junitxml=/evidence/final-core-unit.xml'])
run('final-sidecar-contract', '/hub-venv/bin/python', ['-m', 'pytest', 'tests/unit/agents/test_binary_install_dispatch.py', 'tests/unit/agents/test_sidecar_card_drift.py', 'tests/unit/chat/ui/test_sidecar_dispatch_coverage.py', 'tests/unit/chat/ui/test_sidecar_relay_profiles.py', 'tests/integration/test_gaia_sidecar_relay_live.py', 'tests/unit/chat/ui/test_turn_changes_recording.py', 'tests/unit/chat/ui/test_changes_router.py', 'tests/unit/agents/test_file_snapshots.py', '-v', '--tb=short', '--timeout=180', '--basetemp=/tmp/gaia-snapshot-sidecar', '--junitxml=/evidence/final-sidecar-contract.xml'])
state['finished'] = dt.datetime.now(dt.timezone.utc).isoformat()
(r / 'final-tests-state.json').write_text(json.dumps(state, indent=2))
