import datetime as dt
import json
import os
import subprocess
from pathlib import Path
r=Path('/evidence')
state={'started':dt.datetime.now(dt.timezone.utc).isoformat()}
for phase,expected in [('baseline',1),('candidate',0)]:
    source='/5547/'+phase
    env=dict(os.environ,PYTHONPATH=source+'/src',GAIA_HOME='/live-state/'+phase,GAIA_MEMORY_DISABLED='1',GAIA_NO_DOTENV='1',LEMONADE_BASE_URL='http://host.docker.internal:13355/api/v1',PYTHONUNBUFFERED='1')
    command=['/core-venv/bin/python','-m','pytest','tests/integration/test_rag_no_break_spaces.py','-v','-s','--tb=short','--timeout=300','--junitxml=/evidence/'+phase+'-live.xml']
    state['stage']=phase
    (r/'live-state.json').write_text(json.dumps(state,indent=2))
    with (r/(phase+'-live.log')).open('w') as log:
        code=subprocess.run(command,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
    state[phase]={'exit':code,'expected':expected,'command':command}
    (r/'live-state.json').write_text(json.dumps(state,indent=2))
    if code!=expected:raise SystemExit(code or 99)
state['finished']=dt.datetime.now(dt.timezone.utc).isoformat()
(r/'live-state.json').write_text(json.dumps(state,indent=2))
