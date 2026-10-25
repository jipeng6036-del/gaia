from pathlib import Path

mount = Path('/state/snapshots')
assert mount.is_mount() and mount.stat().st_dev != mount.parent.stat().st_dev
# Remove only the two files created by this fixture, never user/host files.
(mount / 'bounded-fault.bin').unlink(missing_ok=True)
Path('/documents/proof.txt').unlink(missing_ok=True)
print('Released the bounded tmpfs filler and removed the isolated proof file.')
