import json
import os
import subprocess
import shutil
import tarfile
from pathlib import Path

root = Path('/evidence')
for phase in ['baseline', 'candidate']:
    dest = Path('/5666') / phase
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(root / 'baseline.tar') as archive:
        archive.extractall(dest, filter='data')
    if phase == 'candidate':
        with tarfile.open(root / 'candidate-files.tar') as archive:
            archive.extractall(dest, filter='data')
    metadata = dest / '.git'
    assert metadata.resolve().parent in [Path('/5666/baseline'), Path('/5666/candidate')]
    if metadata.exists():
        shutil.rmtree(metadata)
    shutil.copytree('/control/.git', metadata)
    subprocess.run(['git', 'config', '--global', '--add', 'safe.directory', str(dest)], check=True)
    subprocess.run(['chown', '-R', 'gaia-runner:gaia-runner', str(dest)], check=True)
Path('/documents').mkdir(exist_ok=True)
Path('/documents/proof.txt').unlink(missing_ok=True)
Path('/state/agents/gaia').mkdir(parents=True, exist_ok=True)
Path('/state/agents/gaia/.installed').write_text(json.dumps({
    'id': 'gaia', 'version': '0.1.0', 'language': 'python',
    'artifact_kind': 'binary', 'installed_at': '2026-10-25T02:08:47Z',
}))
print('Exact LF baseline and candidate trees extracted; isolated local binary-install receipt seeds the documented dev-sidecar route, without a binary download.')
