import json
import sys
import requests
from pathlib import Path
phase=sys.argv[1]
url='http://127.0.0.1:18833/api/documents'
response=requests.get(url,headers={'X-Gaia-UI':'1','Origin':'http://127.0.0.1:18833'},timeout=20)
report={'method':'GET','url':url,'status':response.status_code,'body':response.json()}
assert response.status_code==200,report
(Path(__file__).parent/(phase+'-documents.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
