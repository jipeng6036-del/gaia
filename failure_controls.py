import datetime as dt
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

r = Path('/evidence')
environment = sys.argv[1]
assert environment in ['no-init-token-temp', 'init-plain-temp']
failures = []
for case in ET.parse(r / 'core-unit.xml').iter('testcase'):
    if case.find('failure') is not None:
        failures.append(case.get('classname').replace('.', '/') + '.py::' + case.get('name'))
assert len(failures) == 12, failures
env = dict(os.environ, PATH='/core-venv/bin:/opt/node-download/node-v24.14.0-linux-x64/bin:/usr/local/bin:/usr/bin:/bin', GAIA_MEMORY_DISABLED='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1', TMPDIR='/tmp')
temp = '/tmp/gaia-5666-controls' if environment.startswith('no-init') else '/tmp/gaia-snapshot-controls'
result = {'environment': environment, 'nodes': failures, 'started': dt.datetime.now(dt.timezone.utc).isoformat()}
for phase in ['baseline', 'candidate']:
    source = '/5666/' + phase
    name = 'controls-' + environment + '-' + phase
    args = ['/usr/sbin/runuser', '-u', 'gaia-runner', '--', '/core-venv/bin/python', '-m', 'pytest', *failures, '-n', '4', '--dist=worksteal', '--timeout=180', '-v', '--tb=short', '--basetemp=' + temp, '--junitxml=/evidence/' + name + '.xml']
    with (r / (name + '.log')).open('w') as out:
        code = subprocess.run(args, cwd=source, env=dict(env, PYTHONPATH=source + '/src'), stdout=out, stderr=subprocess.STDOUT).returncode
    result[phase] = {'exit': code, 'command': args}
    (r / ('controls-' + environment + '.json')).write_text(json.dumps(result, indent=2))
result['finished'] = dt.datetime.now(dt.timezone.utc).isoformat()
(r / ('controls-' + environment + '.json')).write_text(json.dumps(result, indent=2))
