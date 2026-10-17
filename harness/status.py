"""Write CI evidence locally, without synchronous network calls or repo writes."""
import json, os, pathlib, sys, time
ROOT=pathlib.Path(os.environ.get('PASSWAY_RESULTS','native-results'))
def publish(stage,**extra):
 ROOT.mkdir(parents=True,exist_ok=True)
 body={'stage':stage,'at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
       'attempt':os.environ.get('PASSWAY_ATTEMPT','0'),**extra}
 # Details stay in the short-lived evidence artifact, not repository branches.
 temporary=ROOT/'status.json.tmp'
 temporary.write_text(json.dumps(body,indent=2))
 temporary.replace(ROOT/'status.json')
 with (ROOT/'stages.jsonl').open('a') as f:f.write(json.dumps(body)+'\n')
 print('Native test stage: '+stage,flush=True)
if __name__=='__main__':publish(sys.argv[1] if len(sys.argv)>1 else 'setup')
