import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
r=Path('/evidence')
target='/5547-wheel'
if len(sys.argv)==1:
    wheel=str(next((r/'core-dist').glob('*.whl')))
    subprocess.run(['uv','pip','install','--python','/core-venv/bin/python','--target',target,'--no-deps',wheel],check=True)
    env=dict(os.environ,PYTHONPATH=target+':/core-venv/lib/python3.12/site-packages',GAIA_HOME='/wheel-runtime-state',GAIA_NO_DOTENV='1',GAIA_MEMORY_DISABLED='1',LEMONADE_BASE_URL='http://host.docker.internal:13355/api/v1')
    subprocess.run(['/core-venv/bin/python','-S',str(Path(__file__)),'--verify'],cwd='/tmp',env=env,check=True)
else:
    import gaia.rag.sdk as module
    from gaia.rag.sdk import RAGSDK, RAGConfig
    actual=Path(module.__file__)
    assert str(actual).startswith(target+'/'),str(actual)
    digest=hashlib.sha256(actual.read_bytes()).hexdigest()
    assert digest==json.loads((r/'source-manifest.json').read_text())['files']['src/gaia/rag/sdk.py']
    doc=r/'wheel-table.txt'
    doc.write_text('7\u00a0'*950,encoding='utf8')
    config=RAGConfig(cache_dir='/wheel-table-cache',allowed_paths=[str(r)],use_vlm=False,use_llm_chunking=False)
    results=[]
    for cached in [False,True]:
        sdk=RAGSDK(config)
        result=sdk.index_document(str(doc))
        assert result['success'] and result.get('from_cache',False)==cached,result
        assert sdk.chunks==[doc.read_text().strip()]
        chunks,scores=sdk._retrieve_chunks('7 7')
        assert chunks and chunks[0]==sdk.chunks[0]
        results.append({'index':result,'retrievedChunks':len(chunks),'topScore':float(scores[0]),'originalNbsp':sdk.chunks[0].count('\u00a0')})
    report={'python':sys.version,'sdkPath':str(actual),'sdkSha256':digest,'results':results,'boundary':'Real target-installed wheel RAGSDK.index_document with local embedding model. Auxiliary retrieval exercises the real FAISS search using the existing internal retrieval method; no chat answer generation or model mock.'}
    (r/'wheel-runtime.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
