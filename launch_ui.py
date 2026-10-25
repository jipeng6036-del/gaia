import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
r=Path('/evidence')
phase=sys.argv[1]
source=Path('/5547')/phase
Path('/documents').mkdir(exist_ok=True)
shutil.copyfile(r/'CORNING_2021_10K.pdf','/documents/CORNING_2021_10K.pdf')
state=Path('/ui-state')/phase
state.mkdir(parents=True,exist_ok=True)
installed=state/'agents'/'gaia'
installed.mkdir(parents=True,exist_ok=True)
(installed/'.installed').write_text(json.dumps({'id':'gaia','version':'0.1.0','language':'python','artifact_kind':'binary','installed_at':'2026-10-25T04:07:49Z'}))
env=dict(os.environ)
for key in list(env):
    if key.endswith('API_KEY') or key.startswith('GAIA_EVAL_'):env.pop(key)
env.update(PYTHONPATH=os.pathsep.join(str(source/p) for p in ['src','hub/agents/chat/python','hub/agents/gaia/python']),GAIA_HOME=str(state),GAIA_MEMORY_DISABLED='1',GAIA_NO_DOTENV='1',GAIA_GAIA_AGENT_MODE='dev',LEMONADE_BASE_URL='http://host.docker.internal:13355/api/v1',GAIA_ALLOWED_PATHS='/documents',GAIA_DOCUMENT_ROOTS='/documents',PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
command=['/core-venv/bin/gaia','chat','--ui','--ui-port','18823','--base-url',env['LEMONADE_BASE_URL'],'--ui-dist','/webui']
proc=subprocess.Popen(command,cwd=source,env=env,stdout=(r/(phase+'-ui-cli.log')).open('w'),stderr=subprocess.STDOUT)
(r/(phase+'-ui-launch.json')).write_text(json.dumps({'pid':proc.pid,'command':command,'source':str(source),'state':str(state)},indent=2))
print(proc.pid)
