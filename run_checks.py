import datetime as dt
import json
import os
import subprocess
from pathlib import Path
r=Path('/evidence')
state={'started':dt.datetime.now(dt.timezone.utc).isoformat(),'init':Path('/proc/1/comm').read_text().strip()}
assert state['init']=='docker-init'
prefix=['/usr/sbin/runuser','-u','gaia-runner','--','/core-venv/bin/python']
def run(name,flavor,args,expected=0):
    source='/5547/'+flavor
    env=dict(os.environ,PATH='/core-venv/bin:/opt/node-download/node-v24.14.0-linux-x64/bin:/usr/local/bin:/usr/bin:/bin',GAIA_MEMORY_DISABLED='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',TMPDIR='/tmp',PYTHONPATH=source+'/src')
    env.pop('LEMONADE_BASE_URL',None)
    state['stage']=name
    (r/'checks-state.json').write_text(json.dumps(state,indent=2))
    cmd=prefix+args
    with (r/(name+'.log')).open('w') as log:
        code=subprocess.run(cmd,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
    state[name]={'exit':code,'command':cmd,'expectedExit':expected}
    (r/'checks-state.json').write_text(json.dumps(state,indent=2))
    if code!=expected:raise SystemExit(code or 99)
run('baseline-focused','baseline',['-m','pytest','tests/unit/rag/test_embed_input_cap.py','-v','--tb=short','--junitxml=/evidence/baseline-focused.xml'],expected=1)
run('candidate-rag','candidate',['-m','pytest','tests/unit/rag','tests/test_rag.py','-v','--tb=short','--timeout=180','--junitxml=/evidence/candidate-rag.xml'])
run('candidate-core','candidate',['-m','pytest','tests/unit/','-n','4','--dist=worksteal','--timeout=180','-v','--tb=short','--durations=50','--basetemp=/tmp/gaia-core','--junitxml=/evidence/candidate-core.xml'])
run('candidate-lint','candidate',['util/lint.py','--all'])
state['finished']=dt.datetime.now(dt.timezone.utc).isoformat()
(r/'checks-state.json').write_text(json.dumps(state,indent=2))
