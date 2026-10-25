import json
import os
import shutil
import subprocess
from pathlib import Path

r = Path('/evidence')
env = dict(os.environ, PATH='/hub-venv/bin:/opt/node-download/node-v24.14.0-linux-x64/bin:/usr/local/bin:/usr/bin:/bin', GAIA_MEMORY_DISABLED='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
node = 'hub/agents/gaia/python/tests/test_publish_to_r2_by_reference.py::test_the_preflight_names_every_oversized_file_when_credentials_are_absent'
state = {'before': shutil.disk_usage('/tmp')._asdict()}
for phase in ['baseline', 'candidate']:
    name = phase + '-full-tmpfs-control'
    command = ['/usr/sbin/runuser', '-u', 'gaia-runner', '--', '/hub-venv/bin/python', '-m', 'pytest', node, '-q', '--tb=short', '--basetemp=/tmp/gaia-snapshot-hub-path', '--junitxml=/evidence/' + name + '.xml']
    with (r / (name + '.log')).open('w') as out:
        state[name] = subprocess.run(command, cwd='/5666/' + phase, env=dict(env, PYTHONPATH='/5666/' + phase + '/src'), stdout=out, stderr=subprocess.STDOUT).returncode
    assert 'No space left on device' in (r / (name + '.log')).read_text()
removed = []
for name in ['gaia-5666-core', 'gaia-5666-hub', 'gaia-snapshot-hub', 'gaia-snapshot-hub-path', 'gaia-5666-controls']:
    path = Path('/tmp', name)
    assert path.resolve().parent == Path('/tmp') and not path.is_symlink()
    if path.exists():
        shutil.rmtree(path)
        removed.append(str(path))
state.update(removedOwnedScratch=removed, after=shutil.disk_usage('/tmp')._asdict())
(r / 'tmpfs-space-controls.json').write_text(json.dumps(state, indent=2))
with (r / 'final-flagship-complete.log').open('w') as out:
    command = ['/usr/sbin/runuser', '-u', 'gaia-runner', '--', '/hub-venv/bin/python', '-m', 'pytest', 'hub/agents/gaia/python/tests/', '-v', '--tb=short', '--timeout=180', '--basetemp=/tmp/gaia-snapshot-hub', '--junitxml=/evidence/final-flagship-complete.xml']
    state['finalCommand'] = command
    state['finalExit'] = subprocess.run(command, cwd='/5666/candidate', env=dict(env, PYTHONPATH='/5666/candidate/src'), stdout=out, stderr=subprocess.STDOUT).returncode
(r / 'tmpfs-space-controls.json').write_text(json.dumps(state, indent=2))
assert state['finalExit'] == 0
