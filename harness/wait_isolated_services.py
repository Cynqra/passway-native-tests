"""Bounded readiness checks for strict loopback-only disposable test services."""
import sys,time,urllib.request
TARGETS={'services':['http://127.0.0.1:9099/emulator/v1/projects/demo-passway/verificationCodes','http://127.0.0.1:8080/'],'api':['http://127.0.0.1:8787/healthz']}
def wait_ready(mode,seconds=None):
 if mode not in TARGETS:raise ValueError('Unknown isolated service group')
 budget=seconds if seconds is not None else (150 if mode=='services' else 20)
 end=time.monotonic()+budget;pending=list(TARGETS[mode]);last='not responding'
 while pending:
  for url in pending[:]:
   remaining=end-time.monotonic()
   if remaining<=0:raise TimeoutError('Isolated '+mode+' readiness deadline exceeded: '+last)
   try:
    with urllib.request.urlopen(url,timeout=min(2,remaining)) as r:
     body=r.read(4096)
     if r.status==200 and (mode!='api' or body==b'isolated-demo-passway'):pending.remove(url)
   except Exception as error:last=type(error).__name__
  if pending:
   remaining=end-time.monotonic()
   if remaining<=0:raise TimeoutError('Isolated '+mode+' readiness deadline exceeded: '+last)
   time.sleep(min(1,remaining))
 return True
if __name__=='__main__':
 try:wait_ready(sys.argv[1]);print('Isolated '+sys.argv[1]+' ready')
 except Exception as error:print(str(error),file=sys.stderr);sys.exit(1)
