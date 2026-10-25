import json
from pathlib import Path

import requests

ROOT = Path(__file__).parent
results = []
for phase, port in [('baseline', 18804), ('candidate', 18803)]:
    url = f'http://127.0.0.1:{port}'
    headers = {'X-Gaia-UI': '1', 'Origin': url}
    first = json.loads((ROOT / f'{phase}-session.json').read_text())
    for mode in ['JSON_STRING', 'JSON_LIST', 'NATIVE_STRING', 'NATIVE_LIST']:
        if mode == 'JSON_STRING':
            session = first
        else:
            response = requests.post(url + '/api/sessions', headers=headers, json={
                'title': f'{phase} {mode} (HTTP fixture, no inference)',
                'model': 'Gemma-4-E4B-it-GGUF', 'device': 'cpu', 'agent_type': 'gaia',
            }, timeout=30)
            response.raise_for_status()
            session = response.json()
            response = requests.post(url + '/api/chat/send', headers=headers, json={
                'session_id': session['id'], 'message': 'Read metadata for proof.txt. Deterministic HTTP fixture test: ' + mode,
                'agent_type': 'gaia', 'stream': True,
            }, timeout=120)
            response.raise_for_status()
            (ROOT / f'{phase}-{mode}-sse.txt').write_text(response.text, encoding='utf8')
        response = requests.get(url + '/api/sessions/' + session['id'] + '/messages', headers=headers, timeout=30)
        response.raise_for_status()
        messages = response.json()
        (ROOT / f'{phase}-{mode}-messages.json').write_text(json.dumps(messages, indent=2), encoding='utf8')
        text = json.dumps(messages)
        passed = 'Metadata read successfully by the real GAIA file_info tool' in text and '37 B' in text
        if phase == 'baseline':
            assert 'object has no attribute' in text, (phase, mode, text[:1000])
            assert not passed
        else:
            assert passed, (phase, mode, text[:1000])
            assert 'Agent error:' not in text
        row = {'phase': phase, 'mode': mode, 'session': session['id'], 'browser_url': url + '/#' + session['id'][:7], 'metadata_answer': passed}
        results.append(row)
        print(row, flush=True)
(ROOT / 'http-proof.json').write_text(json.dumps(results, indent=2))
