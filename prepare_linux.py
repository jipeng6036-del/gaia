import os
import shutil
import subprocess
import tarfile
from pathlib import Path
r=Path('/evidence')
for flavor in ['baseline','candidate']:
    root=Path('/5547')/flavor;root.mkdir(parents=True,exist_ok=True)
    with tarfile.open(r/'baseline.tar') as archive:archive.extractall(root,filter='data')
    if flavor=='candidate':
        with tarfile.open(r/'candidate-files.tar') as archive:archive.extractall(root,filter='data')
    else:
        with tarfile.open(r/'candidate-files.tar') as archive:
            members=[m for m in archive.getmembers() if m.name.startswith('tests/')]
            archive.extractall(root,members=members,filter='data')
    if not (root/'.git').exists():
        shutil.copytree('/control/.git',root/'.git')
    subprocess.run(['git','config','--global','--add','safe.directory',str(root)],check=True)
subprocess.run(['chown','-R','gaia-runner:gaia-runner','/5547'],check=True)
print('Exact base source + isolated new regression overlay prepared')
