import datetime as dt
import json
import os
import subprocess
from pathlib import Path

r = Path('/evidence')
state = {'started': dt.datetime.now(dt.timezone.utc).isoformat(), 'source': 'Exact LF archive; only candidate three-file overlay is different.'}
env = dict(os.environ, PATH='/core-venv/bin:/opt/node-download/node-v24.14.0-linux-x64/bin:/usr/local/bin:/usr/bin:/bin', GAIA_MEMORY_DISABLED='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1', TMPDIR='/tmp')
prefix = ['/usr/sbin/runuser', '-u', 'gaia-runner', '--', '/core-venv/bin/python']
test = Path('/control/tests/unit/agents/test_tool_args_object.py')
if test.exists():
    test.unlink()  # Our copied regression file is absent from the original tree.
for phase, cwd in [('baseline', '/control'), ('candidate', '/current')]:
    state['phase'] = phase
    (r / 'full-lf-state.json').write_text(json.dumps(state, indent=2))
    command = [*prefix, '-m', 'pytest', 'tests/unit/', '-n', '4', '--dist=worksteal', '--timeout=180', '-v', '--tb=long', '--showlocals', '--durations=50', '--basetemp=/tmp/gaia-tool-args-' + phase, '--cov=src/gaia', '--cov-report=term-missing', '--cov-report=xml:/evidence/full-lf-' + phase + '-coverage.xml', '--junitxml=/evidence/full-lf-' + phase + '.xml']
    state[phase + '_command'] = command
    with (r / ('full-lf-' + phase + '.log')).open('w') as log:
        state[phase + '_exit_code'] = subprocess.run(command, cwd=cwd, env=dict(env, PYTHONPATH=cwd + '/src', COVERAGE_FILE=cwd + '/.coverage-lf'), stdout=log, stderr=subprocess.STDOUT).returncode
    (r / 'full-lf-state.json').write_text(json.dumps(state, indent=2))
state['finished'] = dt.datetime.now(dt.timezone.utc).isoformat()
(r / 'full-lf-state.json').write_text(json.dumps(state, indent=2))
subprocess.run(['/usr/local/bin/python', '/evidence/integration.py'], check=True)
