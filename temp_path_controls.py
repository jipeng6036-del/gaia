import json
import os
import subprocess
from pathlib import Path

r = Path('/evidence')
env = dict(os.environ, PATH='/core-venv/bin:/opt/node-download/node-v24.14.0-linux-x64/bin:/usr/local/bin:/usr/bin:/bin', GAIA_MEMORY_DISABLED='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
prefix = ['/usr/sbin/runuser', '-u', 'gaia-runner', '--', '/core-venv/bin/python']
case = 'tests/unit/agents/test_document_extraction.py::test_existing_memory_hook_records_source_summary_and_recall'
results = {}
for phase, cwd in [('baseline', '/control'), ('candidate', '/current')]:
    for label, temp in [('credential-shaped', '/tmp/gaia-5471-' + phase), ('plain', '/tmp/gaia-tool-args-' + phase)]:
        name = f'temp-control-{phase}-{label}'
        with (r / (name + '.log')).open('w') as log:
            code = subprocess.run([*prefix, '-m', 'pytest', case, '-q', '--basetemp=' + temp, '--junitxml=/evidence/' + name + '.xml'], cwd=cwd, env=dict(env, PYTHONPATH=cwd + '/src'), stdout=log, stderr=subprocess.STDOUT).returncode
        results[name] = code
assert results == {'temp-control-baseline-credential-shaped': 1, 'temp-control-baseline-plain': 0, 'temp-control-candidate-credential-shaped': 1, 'temp-control-candidate-plain': 0}, results
(r / 'temp-path-controls.json').write_text(json.dumps(results, indent=2))
subprocess.run(['/usr/local/bin/python', '/evidence/full_lf.py'], check=True)
