import json,pathlib,sys,time,requests
r=pathlib.Path(__file__).parent;phase=sys.argv[1];port={'baseline':18913,'candidate':18933,'wheel':18943}[phase];url=f'http://127.0.0.1:{port}';headers={'X-Gaia-UI':'1','Origin':url}
for attempt in range(50):
    try:
        ready=requests.get(url+'/api/sessions',timeout=2)
        if ready.status_code==200:break
    except requests.RequestException:pass
    time.sleep(1)
else:raise RuntimeError('UI did not become ready')
def receipt_counts():
    p=r/(phase+'-receipts.jsonl');rows=[json.loads(line) for line in p.read_text().splitlines()] if p.exists() else []
    return [row for row in rows if row['path'] in ['/v1/email/init','/v1/email/query']]
results=[]
for mode in ['on','private','off']:
    response=requests.put(url+'/api/memory/settings',headers=headers,json={'memory_enabled':mode!='off'},timeout=30);response.raise_for_status()
    response=requests.post(url+'/api/sessions',headers=headers,json={'title':phase+' email '+mode+' - local receipt fixture','model':'Gemma-4-E4B-it-GGUF','device':'cpu','agent_type':'email','private':mode=='private'},timeout=30);response.raise_for_status();session=response.json();(r/(phase+'-'+mode+'-session.json')).write_text(json.dumps(session,indent=2))
    before=receipt_counts();events=[]
    response=requests.post(url+'/api/chat/send',headers=headers,json={'session_id':session['id'],'message':'EMAIL_PRIVACY_'+mode.upper()+': acknowledge this synthetic test request. Local receipt fixture only; no mail or model access.','agent_type':'email','stream':True},timeout=(5,90),stream=True);response.raise_for_status()
    with (r/(phase+'-'+mode+'-sse.txt')).open('w',encoding='utf8') as f:
        for line in response.iter_lines(chunk_size=1,decode_unicode=True):
            f.write(line+'\n');f.flush()
            if line.startswith('data: '):
                event=json.loads(line[6:]);events.append(event);print(phase,mode,event.get('type'),event.get('content','')[:160],flush=True)
                if event.get('type')=='done':break
    response.close();time.sleep(.3)
    messages=requests.get(url+'/api/sessions/'+session['id']+'/messages',headers=headers,timeout=30);messages.raise_for_status();(r/(phase+'-'+mode+'-messages.json')).write_text(messages.text,encoding='utf8')
    after=receipt_counts();sent=after[len(before):];queries=[x for x in sent if x['path']=='/v1/email/query'];inits=[x for x in sent if x['path']=='/v1/email/init'];errors=[e for e in events if e.get('type')=='agent_error'];done=[e for e in events if e.get('type')=='done'];assert len(done)==1
    if phase!='baseline' and mode!='on':
        assert not queries and not inits,(mode,sent)
        assert errors and 'email agent' in errors[0]['content'] and 'not sent' in errors[0]['content'],errors
        assert errors[0]['content'] in messages.text
    else:
        assert len(queries)==1 and len(inits)==1,(mode,sent,errors)
        assert 'memory' not in queries[0]['body'],queries
        assert not errors,errors
    results.append({'mode':mode,'session':session['id'],'http_status':response.status_code,'email_init_count':len(inits),'email_query_count':len(queries),'query_memory_present':[('memory' in x['body']) for x in queries],'errors':errors,'done':done})
(r/(phase+'-http-proof.json')).write_text(json.dumps(results,indent=2),encoding='utf8');print(json.dumps(results,indent=2),flush=True)
