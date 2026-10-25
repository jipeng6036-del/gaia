import argparse,json,os,sys,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
parser=argparse.ArgumentParser();parser.add_argument('--host',default='127.0.0.1');parser.add_argument('--port',type=int,required=True);args=parser.parse_args();phase=os.environ['GAIA_5482_PHASE'];port=args.port;log=Path('/evidence')/(phase+'-receipts.jsonl')
MODEL={'id':'Gemma-4-E4B-it-GGUF','model_name':'Gemma-4-E4B-it-GGUF','downloaded':True,'recipe':'llamacpp','labels':['llm'],'max_context_window':131072,'recipe_options':{'ctx_size':65536}}
EMBED=dict(MODEL,id='user.embeddinggemma-300m-GGUF',model_name='user.embeddinggemma-300m-GGUF',labels=['embedding'])
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def answer(self,payload,status=200,mime='application/json'):
        data=payload if isinstance(payload,bytes) else json.dumps(payload).encode()
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def record(self,body=None):
        with log.open('a') as f:f.write(json.dumps({'time':time.time(),'method':self.command,'path':self.path,'body':body})+'\n')
    def do_GET(self):
        self.record()
        if self.path=='/v1/email/init':return self.answer({'ready':True,'checks':[]})
        if self.path=='/version':return self.answer({'apiVersion':'2.7','agentVersion':'0.6.0'})
        if 'health' in self.path:return self.answer({'status':'ok','service':'gaia-agent-email','version':'2026.43.3','context_size':65536,'all_models_loaded':[MODEL,EMBED]})
        if '/models/' in self.path:return self.answer(EMBED if 'embedding' in self.path else MODEL)
        if 'models' in self.path:return self.answer({'object':'list','data':[MODEL,EMBED]})
        if 'system-info' in self.path:return self.answer({'Physical Memory':'64 GB','devices':{'cpu':{'name':'Receipt fixture, no inference','available':True}},'memory':{'total':68719476736,'available':51539607552}})
        if 'stats' in self.path:return self.answer({})
        return self.answer({})
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))) or '{}');self.record(body)
        if self.path.endswith('/tokenize'):return self.answer({'tokens':list(range(len(str(body.get('prompt','')).split())))})
        if self.path.endswith('/chat/completions'):
            return self.answer({'id':'fixture','object':'chat.completion','created':0,'model':MODEL['id'],'choices':[{'index':0,'message':{'role':'assistant','content':'Receipt fixture, no inference.'},'finish_reason':'stop'}],'usage':{'prompt_tokens':1,'completion_tokens':1,'total_tokens':2}})
        if self.path=='/v1/email/query':
            answer='Receipt-only email fixture: your request reached the sidecar without a memory field. No email or model was accessed.'
            data=('data: '+json.dumps({'type':'final','answer':answer})+'\n\n').encode()
            return self.answer(data,mime='text/event-stream')
        return self.answer({'ok':True})
ThreadingHTTPServer((args.host,port),Handler).serve_forever()
