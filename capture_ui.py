import json
import sys
from pathlib import Path
import requests

phase, session = sys.argv[1:]
root = Path(__file__).parent
url = 'http://127.0.0.1:18813'
headers = {'X-Gaia-UI': '1', 'Origin': url}
for resource in ['messages', 'outputs', 'changes']:
    response = requests.get(f'{url}/api/sessions/{session}/{resource}', headers=headers, timeout=30)
    response.raise_for_status()
    (root / f'{phase}-ui-{resource}.json').write_text(response.text, encoding='utf8')
text = (root / f'{phase}-ui-messages.json').read_text()
assert ('This is a bug' in text) == (phase == 'baseline')
assert ('AttributeError' in text) == (phase == 'candidate')
(root / f'{phase}-ui-session.json').write_text(json.dumps({'id': session, 'url': url + '/#' + session[:7]}, indent=2))
print(phase, 'persisted API messages match displayed behavior')
