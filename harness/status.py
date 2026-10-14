import os,json,base64,urllib.request,urllib.error,pathlib,time,sys
ROOT=pathlib.Path(os.environ.get('PASSWAY_RESULTS','native-results'))
def request(method,path,data=None):
 req=urllib.request.Request('https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+'/'+path,data=json.dumps(data).encode() if data else None,method=method,headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json','X-GitHub-Api-Version':'2022-11-28'})
 with urllib.request.urlopen(req,timeout=15) as r:return json.load(r)
def publish(stage,**extra):
 if not os.environ.get('GITHUB_RUN_ID') or not os.environ.get('GH_TOKEN'):return
 try:
  branch='native-runtime-'+os.environ['GITHUB_RUN_ID']
  try:request('GET','git/ref/heads/'+branch)
  except urllib.error.HTTPError as e:
   if e.code!=404:raise
   request('POST','git/refs',{'ref':'refs/heads/'+branch,'sha':os.environ['GITHUB_SHA']})
  target='contents/runtime/status.json';sha=None
  try:sha=request('GET',target+'?ref='+branch)['sha']
  except urllib.error.HTTPError as e:
   if e.code!=404:raise
  body={'stage':stage,'at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'attempt':os.environ.get('PASSWAY_ATTEMPT','0'),**extra}
  if (ROOT/'results.json').exists():body['checks']=json.loads((ROOT/'results.json').read_text())
  payload={'message':'runtime: '+stage,'branch':branch,'content':base64.b64encode(json.dumps(body).encode()).decode()}
  if sha:payload['sha']=sha
  request('PUT',target,payload)
 except Exception as e:print('Runtime status delivery warning:',type(e).__name__,str(e)[:180],flush=True)
if __name__=='__main__':publish(sys.argv[1] if len(sys.argv)>1 else 'setup')
