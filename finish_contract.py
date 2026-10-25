import datetime as dt
import json
import os
import shutil
import subprocess
from pathlib import Path

r = Path('/evidence')
state = json.loads((r / 'final-tests-state.json').read_text())
assert state['final-core-unit']['exit'] == 0
for suffix in ['log', 'xml']:
    shutil.copyfile(r / ('final-sidecar-contract.' + suffix), r / ('contract-forbidden-temp.' + suffix))
env = dict(os.environ, PATH='/hub-venv/bin:/opt/node-download/node-v24.14.0-linux-x64/bin:/usr/local/bin:/usr/bin:/bin', GAIA_MEMORY_DISABLED='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
node = 'tests/unit/chat/ui/test_sidecar_relay_profiles.py::TestPlainUserCopy::test_a_failed_start_shows_plain_words_and_logs_the_detail'
prefix = ['/usr/sbin/runuser', '-u', 'gaia-runner', '--', '/hub-venv/bin/python', '-m', 'pytest']
for phase in ['baseline', 'candidate']:
    source = '/5666/' + phase
    for label, temp in [('forbidden-word', '/tmp/gaia-snapshot-sidecar'), ('plain', '/tmp/gaia-query-contract')]:
        name = 'contract-temp-' + phase + '-' + label
        with (r / (name + '.log')).open('w') as out:
            code = subprocess.run([*prefix, node, '-q', '--tb=short', '--basetemp=' + temp], cwd=source, env=dict(env, PYTHONPATH=':'.join([source+'/src',source+'/hub/agents/chat/python',source+'/hub/agents/gaia/python'])), stdout=out, stderr=subprocess.STDOUT).returncode
        assert code == (1 if label == 'forbidden-word' else 0), (name, code)
        state[name] = code
command = list(state['final-sidecar-contract']['command'])
command = [x.replace('/tmp/gaia-snapshot-sidecar', '/tmp/gaia-query-contract') for x in command]
source = '/5666/candidate'
with (r / 'final-sidecar-contract.log').open('w') as out:
    code = subprocess.run(command, cwd=source, env=dict(env, PYTHONPATH=':'.join([source+'/src',source+'/hub/agents/chat/python',source+'/hub/agents/gaia/python'])), stdout=out, stderr=subprocess.STDOUT).returncode
state['final-sidecar-contract'] = {'exit': code, 'command': command, 'childImportPaths': [source+'/src',source+'/hub/agents/chat/python',source+'/hub/agents/gaia/python']}
state['finished'] = dt.datetime.now(dt.timezone.utc).isoformat()
(r / 'final-tests-state.json').write_text(json.dumps(state, indent=2))
assert code == 0
