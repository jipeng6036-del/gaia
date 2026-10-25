import json
import sys
from pathlib import Path

import requests

root = Path(__file__).parent
phase = sys.argv[1]
mode = sys.argv[2] if len(sys.argv) > 2 else 'SNAPSHOT_DOUBLE_FAULT'
url = 'http://127.0.0.1:18813'
headers = {'X-Gaia-UI': '1', 'Origin': url}
response = requests.post(url + '/api/sessions', headers=headers, json={
    'title': phase + ' undo double fault (HTTP fixture, no inference)',
    'model': 'Gemma-4-E4B-it-GGUF', 'device': 'cpu', 'agent_type': 'gaia',
}, timeout=30)
response.raise_for_status()
session = response.json()
(root / f'{phase}-session.json').write_text(json.dumps(session, indent=2))
requests.put(url + '/api/chat/permissions/' + session['id'], headers=headers,
             json={'mode': 'full_access'}, timeout=30).raise_for_status()
response = requests.post(url + '/api/chat/send', headers=headers, json={
    'session_id': session['id'], 'message': mode + ': Create /documents/proof.txt with the requested fixture text, then inspect it. Local deterministic model HTTP fixture; no inference.',
    'agent_type': 'gaia', 'stream': True,
}, timeout=180, stream=True)
chunks = []
with (root / f'{phase}-sse.txt').open('w', encoding='utf8') as out:
    for line in response.iter_lines(decode_unicode=True):
        chunks.append(line)
        out.write(line + '\n')
        out.flush()
print(response.status_code, '\n'.join(chunks)[-4500:])
response.raise_for_status()
response = requests.get(url + '/api/sessions/' + session['id'] + '/messages', headers=headers, timeout=30)
(root / f'{phase}-messages.json').write_text(response.text, encoding='utf8')
print('persisted', response.text[-1200:])
