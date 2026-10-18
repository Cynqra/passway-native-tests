"""Bounded, hash-pinned store artwork upload. Never delete or replace existing images."""
import hashlib,json,struct,urllib.request,urllib.error
from pathlib import Path
from play_api_access import SafeError,NoRedirect,safe_http_error
ROOT=Path(__file__).parent/'store-assets'
def load_assets(root=ROOT):
    manifest=json.loads((root/'manifest.json').read_text())
    if len(manifest)!=8:raise SafeError('Expected eight approved store assets')
    result=[]
    for row in manifest:
        name=row['file'];kind=row['kind']
        if Path(name).name!=name or kind not in ('icon','featureGraphic','phoneScreenshots'):raise SafeError('Invalid store asset path or kind')
        data=(root/name).read_bytes()
        if not 24<=len(data)<=8*1024*1024 or data[:16]!=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR':raise SafeError('Invalid bounded PNG asset')
        size=list(struct.unpack('>II',data[16:24]))
        if size!=row['dimensions'] or hashlib.sha256(data).hexdigest()!=row['sha256']:raise SafeError('Store asset integrity mismatch')
        if size!=({'icon':[512,512],'featureGraphic':[1024,500],'phoneScreenshots':[1080,1920]}[kind]):raise SafeError('Unexpected store artwork dimensions')
        result.append((row,data))
    if [r['kind'] for r,d in result]!=['icon','featureGraphic']+['phoneScreenshots']*6:raise SafeError('Unexpected store asset ordering')
    return result

def upload_png(url,headers,data,error_observer=None):
    if not url.startswith('https://androidpublisher.googleapis.com/upload/androidpublisher/v3/applications/com.passway.app/edits/') or not url.endswith('?uploadType=media'):raise SafeError('Unexpected image upload endpoint')
    req=urllib.request.Request(url,data=data,headers={**headers,'Content-Type':'image/png'},method='POST')
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=60) as response:
            raw=response.read(65537)
            if len(raw)>65536:raise SafeError('Oversized store image response')
            return json.loads(raw)
    except urllib.error.HTTPError as error:
        raw=error.read(65536)
        if error_observer:error_observer(error.code,raw)
        raise safe_http_error(url,error.code,raw) from None
    except (urllib.error.URLError,TimeoutError,ValueError):raise SafeError('Store image upload transport or JSON validation failed') from None

def stage_assets(path,inventory,assets,headers,upload=upload_png,error_observer=None):
    # Refuse to touch unrelated existing artwork, and never retry uploads blindly.
    expected={k:[r['sha256'] for r,d in assets if r['kind']==k] for k in inventory}
    for kind,images in inventory.items():
        hashes=[x.get('sha256','').lower() for x in images]
        if images and hashes!=expected[kind]:raise SafeError('Existing store artwork differs; no replacement attempted')
    uploaded=[]
    for row,data in assets:
        if inventory[row['kind']]:continue
        url=path.replace('/androidpublisher/v3/','/upload/androidpublisher/v3/')+'/'+row['kind']+'?uploadType=media'
        response=upload(url,headers,data,error_observer=error_observer)
        if response.get('image',{}).get('sha256','').lower()!=row['sha256']:raise SafeError('Uploaded store image hash not confirmed')
        uploaded.append(row['file'])
    return uploaded
