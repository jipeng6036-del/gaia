import hashlib
import json
from pathlib import Path

r = Path(__file__).parent
result = {}
for phase in ['baseline', 'candidate']:
    for suffix in ['', '-success', '-process-only']:
        name = phase + suffix
        events = [json.loads(line[6:]) for line in (r / (name + '-sse.txt')).read_text(encoding='utf-8-sig').splitlines() if line.startswith('data: ')]
        errors = [e for e in events if e['type'] == 'agent_error']
        done = [e for e in events if e['type'] == 'done']
        assert len(done) == 1 and events[-1] is done[0], name
        assert any(e['type'] == 'tool_result' and e.get('tool') == 'write_file' and e.get('success') for e in events), name
        undo_warnings = [i for i, e in enumerate(events) if e['type'] == 'status' and 'Undo may not work' in e.get('message', '')]
        if suffix == '-success':
            assert not errors and not done[0].get('failed')
            assert 'The file was written successfully' in done[0]['content']
            assert undo_warnings
        else:
            assert len(errors) == 1 and done[0].get('failed'), name
            expect_generic = phase == 'baseline' and not suffix
            assert ('This is a bug' in errors[0]['content']) == expect_generic, name
            assert ('AttributeError' in errors[0]['content']) == (not expect_generic), name
            if suffix:
                assert not undo_warnings
            else:
                assert undo_warnings and max(undo_warnings) < events.index(errors[0])
        result[name] = {'events': len(events), 'terminal': done[0], 'undoWarnings': len(undo_warnings)}
    messages = (r / (phase + '-ui-messages.json')).read_text()
    assert ('This is a bug' in messages) == (phase == 'baseline')
    assert ('AttributeError' in messages) == (phase == 'candidate')
log = (r / 'candidate-final-sidecar.log').read_text(errors='replace')
assert "AttributeError: 'str' object has no attribute 'get'" in log
assert 'OSError: [Errno 28] No space left on device' in log
assert log.count('Traceback (most recent call last):') >= 2
assert '/query run failed for run_id=' in log and 'SnapshotError: Could not save' in log
faults = [json.loads(line) for line in (r / 'faults.jsonl').read_text().splitlines()]
assert len(faults) >= 6 and all(f['errno'] == 28 and f['written'] <= 1048576 for f in faults)
for phase in ['baseline', 'candidate']:
    for suffix in ['', '-reloaded']:
        image = r / (phase + '-ui' + suffix + '.png')
        assert image.stat().st_size > 10000
        result[image.name] = hashlib.sha256(image.read_bytes()).hexdigest()
(r / 'runtime-proof.json').write_text(json.dumps(result, indent=2))
print('All six actual UI→daemon→GaiaAgent→file tool→sidecar HTTP controls and four raw screenshots/persistence checks passed. Model boundary is scripted; no inference/eval claim.')
