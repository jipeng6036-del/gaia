"""Deterministic HTTP model boundary only; GAIA/parser/watcher/RAG remain real.

No inference or real Lemonade compatibility is claimed by this fixture.
"""
import hashlib
import json
import math
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
CHAT = "Gemma-4-E4B-it-GGUF"
EMBED = "user.embeddinggemma-300m-GGUF"
MODELS = [
    {"id": CHAT, "model_name": CHAT, "downloaded": True, "recipe": "llamacpp", "labels": ["llm"], "max_context_window": 131072, "recipe_options": {"ctx_size": 65536}},
    {"id": EMBED, "model_name": EMBED, "downloaded": True, "recipe": "llamacpp", "labels": ["embedding"], "recipe_options": {"ctx_size": 2048}},
]

def embedding(text):
    vector = [0.0] * 64
    for word in re.findall(r"\w+", text.lower()):
        vector[int(hashlib.md5(word.encode()).hexdigest(), 16) % 64] += 1
    if not any(vector):
        vector[0] = 1
    norm = math.sqrt(sum(v * v for v in vector))
    return [v / norm for v in vector]

def reply(payload):
    messages = payload.get("messages", [])
    latest_user = max((i for i, m in enumerate(messages) if m.get("role") == "user"), default=0)
    query = str(messages[latest_user].get("content", ""))
    if query.startswith("[Tool result:"):
        result = json.loads(query.split("] ", 1)[1])
        matches = result.get("matches")
        if matches is not None:
            return "Actual indexed text returned by GAIA (deterministic model fixture):\n\n" + "\n\n".join(str(item) for item in matches)
        return "Actual GAIA tool result (deterministic model fixture): " + str(result.get("message", result.get("status", result.get("error"))))
    after = messages[latest_user + 1:]
    # Only choose a tool on the first model call of a turn. All results below
    # come from GAIA's real tool output, never by reading fixture files here.
    results = [m for m in after if m.get("role") == "tool"]
    if results:
        return "Fixture model received the real tool result:\n" + str(results[-1].get("content", ""))
    command = re.search(r"FIXTURE_(WATCH|INDEX|SEARCH)\s+(.+)", query)
    if not command:
        return "Local deterministic model fixture. No real model inference."
    action, value = command.groups()
    names = {"WATCH": ("add_watch_directory", "directory"), "INDEX": ("index_document", "file_path"), "SEARCH": ("search_indexed_chunks", "pattern")}
    name, argument = names[action]
    return json.dumps({"tool": name, "tool_args": {argument: value.strip()}})

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_json(self, body, status=200):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        route = self.path.split("?")[0]
        if route.endswith("/health"):
            return self.send_json({"status": "ok", "version": "2026.43.3", "context_size": 65536, "all_models_loaded": MODELS})
        if route.endswith("/models"):
            return self.send_json({"object": "list", "data": MODELS})
        if "/models/" in route:
            return self.send_json(MODELS[1] if "embedding" in route else MODELS[0])
        if route.endswith("/system-info"):
            return self.send_json({"Physical Memory": "64 GB", "devices": {"cpu": {"name": "HTTP test fixture", "available": True}}, "memory": {"total": 68719476736, "available": 51539607552}})
        if route.endswith("/stats"):
            return self.send_json({"time_to_first_token": 0.001, "tokens_per_second": 1000})
        self.send_json({"error": "unsupported fixture GET", "path": self.path}, 404)

    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        with (ROOT / "requests.jsonl").open("a", encoding="utf8") as out:
            out.write(json.dumps({"path": self.path, "body": payload}) + "\n")
        if self.path.endswith("/embeddings"):
            texts = payload["input"]
            if isinstance(texts, str):
                texts = [texts]
            return self.send_json({"object": "list", "model": EMBED, "data": [{"index": i, "object": "embedding", "embedding": embedding(t)} for i, t in enumerate(texts)], "usage": {"prompt_tokens": 1, "total_tokens": 1}})
        if self.path.endswith(("/load", "/unload", "/pull")):
            return self.send_json({"status": "success"})
        if self.path.endswith("/tokenize"):
            return self.send_json({"tokens": list(range(len(str(payload.get("prompt", "")).split())))})
        if self.path.endswith("/chat/completions"):
            content = reply(payload)
            if payload.get("stream"):
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                for delta, reason in [({"role": "assistant", "content": content}, None), ({}, "stop")]:
                    data = {"id": "fixture", "object": "chat.completion.chunk", "created": 0, "model": CHAT, "choices": [{"index": 0, "delta": delta, "finish_reason": reason}]}
                    self.wfile.write(("data: " + json.dumps(data) + "\n\n").encode())
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
                return
            return self.send_json({"id": "fixture", "object": "chat.completion", "created": 0, "model": CHAT, "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}})
        self.send_json({"error": "unsupported fixture POST", "path": self.path}, 404)

if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 18792), Handler).serve_forever()
