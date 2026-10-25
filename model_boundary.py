"""HTTP response fixture and bounded OS fault, no production Python monkeypatch.

The real agent writes /documents/proof.txt. Only after receiving its actual tool
result do we fill the dedicated 1 MiB tmpfs mounted at /state/snapshots. The next
scripted malformed JSON tool arguments trigger the original processing exception.
"""
import errno
import importlib.util
import json
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
spec = importlib.util.spec_from_file_location('base', ROOT / 'model_base.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def fill_snapshot_volume():
    target = Path('/state/snapshots')
    assert target.is_mount() and target.stat().st_dev != target.parent.stat().st_dev
    capacity = __import__('os').statvfs(target)
    assert capacity.f_blocks * capacity.f_frsize <= 1024 * 1024
    written = 0
    try:
        with (target / 'bounded-fault.bin').open('wb', buffering=0) as stream:
            while True:
                written += stream.write(b'x' * 4096)
    except OSError as exc:
        assert exc.errno == errno.ENOSPC, exc
        with (ROOT / 'faults.jsonl').open('a') as out:
            out.write(json.dumps({'errno': exc.errno, 'written': written, 'mount': str(target)}) + '\n')


class Handler(base.Handler):
    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
        with (ROOT / 'requests.jsonl').open('a', encoding='utf8') as out:
            out.write(json.dumps({'path': self.path, 'body': payload}) + '\n')
        if self.path.endswith(('/load', '/unload', '/pull')):
            return self.send_json({'status': 'success'})
        if self.path.endswith('/tokenize'):
            return self.send_json({'tokens': list(range(len(str(payload.get('prompt', '')).split())))})
        if not self.path.endswith('/chat/completions'):
            return self.send_json({'error': 'unsupported fixture route'}, 404)
        messages = payload['messages']
        text = '\n'.join(str(m.get('content', '')) for m in messages)
        result_count = sum(m.get('role') == 'tool' or str(m.get('content', '')).startswith('[Tool result:') for m in messages)
        if not any(marker in text for marker in ['SNAPSHOT_DOUBLE_FAULT', 'SNAPSHOT_SUCCESS_CONTROL', 'SNAPSHOT_PROCESS_ONLY']):
            content = 'Deterministic HTTP boundary fixture; no inference.'
        elif result_count == 0:
            content = json.dumps({'tool': 'write_file', 'tool_args': {'file_path': '/documents/proof.txt', 'content': 'Written by the real GaiaAgent write_file tool.\n'}})
        else:
            # Enforce the real write before injecting the second fault.
            assert Path('/documents/proof.txt').read_text() == 'Written by the real GaiaAgent write_file tool.\n'
            if 'SNAPSHOT_PROCESS_ONLY' not in text and not Path('/state/snapshots/bounded-fault.bin').exists():
                fill_snapshot_volume()
            content = ('The file was written successfully (model boundary fixture).' if 'SNAPSHOT_SUCCESS_CONTROL' in text
                       else json.dumps({'tool': 'file_info', 'tool_args': 'oops'}))
        response = {'id': 'fixture', 'object': 'chat.completion', 'created': 0, 'model': base.CHAT,
                    'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': content}, 'finish_reason': 'stop'}],
                    'usage': {'prompt_tokens': 1, 'completion_tokens': 1, 'total_tokens': 2}}
        if not payload.get('stream'):
            return self.send_json(response)
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.end_headers()
        for delta, finish in [({'role': 'assistant', 'content': content}, None), ({}, 'stop')]:
            self.wfile.write(('data: ' + json.dumps({'id': 'fixture', 'object': 'chat.completion.chunk', 'created': 0, 'model': base.CHAT, 'choices': [{'index': 0, 'delta': delta, 'finish_reason': finish}]}) + '\n\n').encode())
        self.wfile.write(b'data: [DONE]\n\n')
        self.wfile.flush()


if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', 18802), Handler).serve_forever()
