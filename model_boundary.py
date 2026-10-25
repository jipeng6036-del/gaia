"""Script malformed model HTTP responses; production GAIA code stays unchanged.

No real inference, Lemonade deployment, or model-quality claim is made.
"""
import importlib.util
import json
import re
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
spec = importlib.util.spec_from_file_location('boundary', ROOT / 'model_base.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
PROOF = ROOT / 'documents' / 'proof.txt'


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
            return self.send_json({'error': 'unsupported fixture request'}, 404)
        messages = payload['messages']
        text = '\n'.join(str(m.get('content', '')) for m in messages)
        mode = re.search(r'(JSON|NATIVE)_(STRING|LIST)', text)
        # Session-title calls must not consume the first scripted tool call.
        if not mode:
            content, calls = 'Deterministic model fixture (no inference).', None
        else:
            native = mode[1] == 'NATIVE'
            tool_results = [m for m in messages if m.get('role') == 'tool']
            json_results = [m for m in messages if str(m.get('content', '')).startswith('[Tool result:')]
            if tool_results or json_results:
                result = (tool_results or json_results)[-1]['content']
                content, calls = 'Metadata read successfully by the real GAIA file_info tool:\n' + str(result), None
            else:
                corrected = any('Your last tool call could not be used:' in str(m.get('content', '')) for m in messages)
                args = {'path': str(PROOF)} if corrected else ('oops' if mode[2] == 'STRING' else ['oops'])
                calls = [{'id': 'call_fixture', 'type': 'function', 'function': {'name': 'file_info', 'arguments': json.dumps(args)}}] if native else None
                content = None if native else json.dumps({'tool': 'file_info', 'tool_args': args})
        message = {'role': 'assistant', 'content': content}
        if calls:
            message['tool_calls'] = calls
        reason = 'tool_calls' if calls else 'stop'
        if payload.get('stream'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.end_headers()
            delta = {'role': 'assistant'}
            if calls:
                delta['tool_calls'] = [dict(index=i, **call) for i, call in enumerate(calls)]
            else:
                delta['content'] = content
            for part, finish in [(delta, None), ({}, reason)]:
                self.wfile.write(('data: ' + json.dumps({'id': 'fixture', 'object': 'chat.completion.chunk', 'created': 0, 'model': base.CHAT, 'choices': [{'index': 0, 'delta': part, 'finish_reason': finish}]}) + '\n\n').encode())
            self.wfile.write(b'data: [DONE]\n\n')
            self.wfile.flush()
        else:
            self.send_json({'id': 'fixture', 'object': 'chat.completion', 'created': 0, 'model': base.CHAT, 'choices': [{'index': 0, 'message': message, 'finish_reason': reason}], 'usage': {'prompt_tokens': 1, 'completion_tokens': 1, 'total_tokens': 2}})


if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', 18802), Handler).serve_forever()
