import json
import os
import subprocess
from pathlib import Path
r=Path('/evidence')
env=dict(os.environ,PYTHONPATH='/5547/candidate/src',GAIA_MEMORY_DISABLED='1')
commands={
 'build-core-final':['/hub-venv/bin/python','-m','build','--outdir','/evidence/final-dist'],
 'twine-core-final':['/hub-venv/bin/python','-m','twine','check'],
 'capability-matrix':['/hub-venv/bin/python','hub/agents/gaia/python/packaging/capability_matrix.py','--check'],
}
state={}
for name,cmd in commands.items():
    if name=='twine-core-final':cmd += [str(p) for p in (r/'final-dist').iterdir()]
    with (r/(name+'.log')).open('w') as log:
        code=subprocess.run(['/usr/sbin/runuser','-u','gaia-runner','--',*cmd],cwd='/5547/candidate',env=env,stdout=log,stderr=subprocess.STDOUT).returncode
    state[name]={'command':cmd,'exit':code}
    (r/'package-final.json').write_text(json.dumps(state,indent=2))
    if code:raise SystemExit(code)
