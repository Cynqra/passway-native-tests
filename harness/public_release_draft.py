"""Save accurate listing copy and a nonpublic production draft of verified code 13."""
import argparse,json,os,re,urllib.parse
from pathlib import Path
from play_api_access import access_token,SafeError,PUBLISHER
from internal_release import send
from public_release_preflight import VERSION,verified_candidate,reason_from_error
SHORT='Meet in person. Keep chatting without sharing your phone number.'
FULL='''A real hello can become a private chat.

Passway helps adults aged 18 and over stay in touch with people they meet in person, without giving them their phone number or social profiles.

Connect by code
Create a four character code and show it to the person you have met. Each code works once and expires after five minutes. See the name on a connection request and choose whether to accept or decline it.

Keep the conversation going
Send text messages after you connect. Add a private note to help remember where you met someone. Only you can see that note.

Choose your boundaries
End a connection, block an account or report a conversation from inside the chat. Reporting closes the chat and blocks that account from reconnecting with you.

Know how messages are handled
Messages are available in chat for up to 72 hours. Physical deletion happens through cleanup, and reported content and related records may be retained longer for safety review. Passway does not promise immediate physical deletion at exactly 72 hours.

Your phone number is used to sign in and help prevent abuse. It is not shown to people you connect with. You can request account deletion inside Settings.

Stay safe
Never share a verification code, password, PIN or bank details with another person. Be careful with requests for money, gifts or remote access to your device.

Support: Limerencetechnologies@gmail.com'''

def sanitized_google_error(status,raw,operation):
    try:
        error=json.loads(raw).get('error',{})
        message=error.get('message','') if isinstance(error,dict) else ''
        enum=error.get('status','') if isinstance(error,dict) else ''
    except (ValueError,AttributeError,TypeError):message='';enum=''
    if not isinstance(message,str):message=''
    message=re.sub(r'(?i)Bearer\s+\S+','[redacted]',message)
    message=re.sub(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+','[redacted]',message)
    message=re.sub(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}','[email]',message)
    return {'httpStatus':status,'operation':operation,'status':enum if isinstance(enum,str) and re.fullmatch(r'[A-Z_]{1,48}',enum) else '','message':message[:1000]}


def prepare_draft(token,request=send,commit=True,allow_automatic_review=False,include_assets=False,upload=None):
    from public_store_assets import load_assets,stage_assets,upload_png
    assets=load_assets() if include_assets else []
    headers={'Authorization':'Bearer '+token};edit=None;committed=False
    report={'package':'com.passway.app','versionCode':VERSION,'publicProductionRollout':False,'reviewSubmitted':False,'scope':'Production track DRAFT and factual store text only; no public availability, review approval, privacy declarations, real SMS or positive attestation claimed'}
    report['diagnosticOnly']=not commit
    report['automaticReviewAllowed']=allow_automatic_review
    report['reviewAcceptanceConfirmed']=False
    def observed(status,raw):
        if 'googleError' not in report:
            report['googleRequirement']=reason_from_error(status,raw)
            report['googleError']=sanitized_google_error(status,raw,report.get('operation','unknown'))
    def call(url,**kwargs):return request(url,headers=headers,error_observer=observed,**kwargs)
    try:
        report['operation']='create_temporary_edit'
        edit=call(PUBLISHER,method='POST',body={}).get('id')
        if not isinstance(edit,str) or not edit.isdigit():raise SafeError('Invalid temporary edit identifier')
        report['operation']='verify_candidate_and_read_store_metadata'
        details,listings=verified_candidate(call,edit)
        locale=details.get('defaultLanguage','')
        if not isinstance(locale,str) or not re.fullmatch(r'[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]{2,8}){0,2}',locale):raise SafeError('Default listing language unavailable')
        if not (1<=len(SHORT)<=80 and 80<=len(FULL)<=4000):raise SafeError('Listing copy outside Play bounds')
        path=PUBLISHER+'/'+edit+'/listings/'+urllib.parse.quote(locale,safe='')
        report['operation']='stage_listing_text'
        call(path,method='PUT',body={'language':locale,'title':'Passway','shortDescription':SHORT,'fullDescription':FULL})
        report['listingLanguage']=locale
        report['operation']='read_image_inventory'
        inventory={kind:call(path+'/'+kind).get('images',[]) for kind in ['icon','featureGraphic','phoneScreenshots']}
        report['imageCounts']={kind:len(images) for kind,images in inventory.items()}
        if include_assets:
            report['operation']='stage_approved_store_assets'
            report['artworkUploaded']=stage_assets(path,inventory,assets,headers,upload=upload or upload_png,error_observer=observed)
            readback={kind:call(path+'/'+kind).get('images',[]) for kind in inventory}
            for kind in inventory:
                if [x.get('sha256','').lower() for x in readback[kind]]!=[r['sha256'] for r,d in assets if r['kind']==kind]:raise SafeError('Store artwork readback mismatch')
            report['imageCounts']={kind:len(images) for kind,images in readback.items()}
        report['operation']='stage_production_draft'
        call(PUBLISHER+'/'+edit+'/tracks/production',method='PUT',body={'track':'production','releases':[{'name':'0.3.7 (13)','versionCodes':[str(VERSION)],'status':'draft'}]})
        report['operation']='validate_draft_edit'
        call(PUBLISHER+'/'+edit+':validate',method='POST',body={})
        report['validated']=True
        if not commit:
            report['draftCommitted']=False
            return report
        report['operation']='commit_draft_with_automatic_review' if allow_automatic_review else 'commit_draft_without_review'
        report['commitAttempted']=True
        # Google explicitly requires omitting this parameter for this draft app.
        # No automatic fallback or repeated commit after an ambiguous response.
        suffix='' if allow_automatic_review else '?changesNotSentForReview=true'
        call(PUBLISHER+'/'+edit+':commit'+suffix,method='POST',body={})
        report['automaticReviewMayHaveStarted']=allow_automatic_review
        committed=True;report['draftCommitted']=True;report['listingTextSaved']=True
    except Exception as e:
        report['draftCommitted']=False;report['error']=str(e) if isinstance(e,SafeError) else type(e).__name__
    finally:
        if edit and not committed:
            try:call(PUBLISHER+'/'+edit,method='DELETE');report['temporaryEditDeleted']=True
            except Exception:report['cleanupFailed']=True
    return report
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--diagnose',action='store_true');parser.add_argument('--allow-automatic-review',action='store_true');parser.add_argument('--store-assets',action='store_true');args=parser.parse_args()
    try:result=prepare_draft(access_token(os.environ),commit=not args.diagnose,allow_automatic_review=args.allow_automatic_review,include_assets=args.store_assets)
    except Exception as e:result={'draftCommitted':False,'publicProductionRollout':False,'error':str(e) if isinstance(e,SafeError) else type(e).__name__}
    Path('public-release-draft.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));raise SystemExit(0 if result.get('draftCommitted') or (args.diagnose and result.get('validated') and result.get('temporaryEditDeleted')) else 1)
