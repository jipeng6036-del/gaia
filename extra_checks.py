import datetime as dt
import json
import os
import subprocess
from pathlib import Path

r = Path('/evidence')
source = '/5547/candidate'
env = dict(os.environ, PATH='/core-venv/bin:/opt/node-download/node-v24.14.0-linux-x64/bin:/usr/local/bin:/usr/bin:/bin', PYTHONPATH=source+'/src', GAIA_MEMORY_DISABLED='1', PYTHONUNBUFFERED='1')
env.pop('LEMONADE_BASE_URL', None)
state = {'started': dt.datetime.now(dt.timezone.utc).isoformat()}
def run(name, command):
    state['stage'] = name
    (r/'extra-state.json').write_text(json.dumps(state, indent=2))
    with (r/(name+'.log')).open('w') as log:
        p = subprocess.run(['/usr/sbin/runuser','-u','gaia-runner','--',*command], cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT)
    state[name] = {'exit':p.returncode,'command':command}
    (r/'extra-state.json').write_text(json.dumps(state, indent=2))
    if p.returncode: raise SystemExit(p.returncode)
run('module-skip-guard',['/core-venv/bin/python','util/check_module_skips.py','--workflow','test_unit.yml','--job','unit-tests'])
run('build-core',['/hub-venv/bin/python','-m','build','--outdir','/evidence/core-dist'])
run('twine-core',['/hub-venv/bin/python','-m','twine','check',*[str(x) for x in (r/'core-dist').iterdir()]])
state['finished']=dt.datetime.now(dt.timezone.utc).isoformat()
(r/'extra-state.json').write_text(json.dumps(state,indent=2))
