import hashlib,json,os,pathlib,subprocess,sys,tarfile
r=pathlib.Path('/evidence');phase='final-wheel';source=pathlib.Path('/tmp/gaia5482-final-wheel')
state=pathlib.Path('/tmp/gaia5482-homes')/phase/'.gaia';state.mkdir(parents=True,exist_ok=True)
installed=state/'agents'/'email';installed.mkdir(parents=True,exist_ok=True)
executable=installed/'email-agent'
executable.write_text("#!/core-venv/bin/python\nimport runpy\nrunpy.run_path('/evidence/receipt_server.py',run_name='__main__')\n")
executable.chmod(0o755)
(installed/'.installed').write_text(json.dumps({'id':'email','version':'0.6.0','language':'python','artifact_kind':'binary','installed_at':'2026-10-25T06:00:00Z','artifact_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(),'executable':'email-agent'}))
env={k:v for k,v in os.environ.items() if not k.endswith('API_KEY') and not k.startswith('GAIA_EVAL_')}
fixture_port=18962;ui_port=18963
model_env=dict(env,GAIA_5482_PHASE=phase)
fixture=subprocess.Popen(['/core-venv/bin/python',str(r/'receipt_server.py'),'--host','127.0.0.1','--port',str(fixture_port)],env=model_env,stdout=(r/(phase+'-receipt.log')).open('w'),stderr=subprocess.STDOUT)
env.update(HOME=str(state.parent),XDG_CONFIG_HOME=str(state/'config'),XDG_CACHE_HOME=str(state/'cache'),PYTHONPATH=str(source),GAIA_HOME=str(state),GAIA_MEMORY_DISABLED='1',GAIA_NO_DOTENV='1',GAIA_5482_PHASE=phase,LEMONADE_BASE_URL=f'http://127.0.0.1:{fixture_port}/api/v1',PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
command=['/core-venv/bin/gaia','chat','--ui','--ui-port',str(ui_port),'--base-url',env['LEMONADE_BASE_URL'],'--ui-dist',str(source/'gaia/apps/webui/dist')]
if phase=='final-wheel':
    checker="import pathlib,hashlib,json;import gaia.ui._chat_helpers as h;import gaia.ui.email_sidecar.profiles as p;root=pathlib.Path('/tmp/gaia5482-final-wheel');rows=[];\nfor m in [h,p]:\n f=pathlib.Path(m.__file__).resolve();assert f.is_relative_to(root),f;rows.append({'module':m.__name__,'path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})\nprint(json.dumps(rows,indent=2))"
    check=subprocess.run(['/core-venv/bin/python','-c',checker],cwd='/tmp',env=env,text=True,capture_output=True,check=True)
    (r/'final-wheel-import-proof.json').write_text(check.stdout)
proc=subprocess.Popen(command,cwd=source,env=env,stdout=(r/(phase+'-ui-cli.log')).open('w'),stderr=subprocess.STDOUT)
(r/(phase+'-launch.json')).write_text(json.dumps({'pid':proc.pid,'receiptPid':fixture.pid,'command':command,'source':str(source),'fixture':'receipt-only executable registered through isolated hash-verified .installed metadata; actual daemon owns startup/handshake, unmodified handle/proxy/relay/UI','home':str(state)},indent=2))
print(proc.pid)
