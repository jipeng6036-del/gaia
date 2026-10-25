from pathlib import Path
import hashlib,json,zipfile,requests
r=Path('/evidence');target=Path('/tmp/gaia5482-final-wheel');name='amd_gaia-0.25.1-py3-none-any.whl';wheel=r/'final-wheel-dist'/name
manifest=json.loads((r/'final-wheel-release-package.json').read_text());assert all(c['code']==0 for c in manifest['checks'])
actual=hashlib.sha256(wheel.read_bytes()).hexdigest();assert actual==manifest['files'][name]
imports=json.loads((r/'final-wheel-import-proof.json').read_text());rows=[]
with zipfile.ZipFile(wheel) as z:
 frontend=[n for n in z.namelist() if 'gaia/apps/webui/dist/' in n];assert len(frontend)==29
 for row in imports:
  path=Path(row['path']);assert path.is_relative_to(target)
  rel=path.relative_to(target).as_posix();runtime=hashlib.sha256(path.read_bytes()).hexdigest();expected=manifest['sourceModuleParity'][rel]
  assert runtime==row['sha256']==expected==hashlib.sha256(z.read(rel)).hexdigest();rows.append(dict(row,matches_release_source_and_wheel=True))
 response=requests.get('http://127.0.0.1:18963/',timeout=30);response.raise_for_status();index=z.read('gaia/apps/webui/dist/index.html');assert response.content==index
 result={'wheel':name,'sha256':actual,'release_gates_all_zero':True,'wheel_frontend_files':len(frontend),'served_frontend_index_status':response.status_code,'served_frontend_matches_wheel':True,'index_sha256':hashlib.sha256(index).hexdigest(),'imports':rows}
(r/'final-wheel-integrity-proof.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
log=Path('/tmp/gaia5482-homes/final-wheel/.gaia/host/daemon.log');(r/'final-wheel-daemon.log').write_bytes(log.read_bytes())
