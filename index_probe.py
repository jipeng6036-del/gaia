import hashlib
import json
import os
import platform
import sys
import time
import traceback
from pathlib import Path

root=Path(__file__).parent
phase=sys.argv[1]
source=Path(sys.argv[2])
os.environ['GAIA_HOME']=str(root/(phase+'-home'))
os.environ['GAIA_NO_DOTENV']='1'
os.environ['LEMONADE_BASE_URL']='http://127.0.0.1:13355/api/v1'
sys.path.insert(0,str(source/'src'))
from gaia.rag.sdk import RAGSDK,RAGConfig,EMBED_MAX_CHARS
import gaia.rag.sdk as module

started=time.monotonic()
doc=root/'CORNING_2021_10K.pdf'
assert hashlib.sha256(doc.read_bytes()).hexdigest()=='8023fac91ad417f996b692c506ee0e097effd091e698275288e4126cb8a2020e'
report={'python':sys.version,'platform':platform.platform(),'source':str(module.__file__),'sourceSha256':hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),'documentSha256':hashlib.sha256(doc.read_bytes()).hexdigest(),'embedMaxChars':EMBED_MAX_CHARS,'use_vlm':False,'use_llm_chunking':False}
print(json.dumps(report),flush=True)
try:
    config=RAGConfig(cache_dir=str(root/(phase+'-cache')),allowed_paths=[str(root)],base_url=os.environ['LEMONADE_BASE_URL'],use_vlm=False,use_llm_chunking=False,show_stats=True)
    sdk=RAGSDK(config)
    result=sdk.index_document(str(doc),progress_callback=lambda done,total: print('PROGRESS',done,total,flush=True))
    report['indexResult']=result
    report['chunks']=len(sdk.chunks)
    report['chunkNbsp']=sum(c.count('\u00a0') for c in sdk.chunks)
    report['maxChunkChars']=max(map(len,sdk.chunks),default=0)
except Exception as error:
    report['exceptionType']=type(error).__name__
    report['exception']=str(error)
    traceback.print_exc()
finally:
    report['elapsedSeconds']=time.monotonic()-started
    (root/(phase+'-index.json')).write_text(json.dumps(report,indent=2,default=str)+'\n',encoding='utf8')
    print(json.dumps(report,default=str),flush=True)
