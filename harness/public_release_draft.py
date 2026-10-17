"""Save accurate listing copy and a nonpublic production draft of verified code 13."""
import json,os,re,urllib.parse
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

def prepare_draft(token,request=send):
    headers={'Authorization':'Bearer '+token};edit=None;committed=False
    report={'package':'com.passway.app','versionCode':VERSION,'publicProductionRollout':False,'reviewSubmitted':False,'scope':'Production track DRAFT and factual store text only; no public availability, review approval, privacy declarations, real SMS or positive attestation claimed'}
    def observed(status,raw):report['googleRequirement']=reason_from_error(status,raw)
    def call(url,**kwargs):return request(url,headers=headers,error_observer=observed,**kwargs)
    try:
        edit=call(PUBLISHER,method='POST',body={}).get('id')
        if not isinstance(edit,str) or not edit.isdigit():raise SafeError('Invalid temporary edit identifier')
        details,listings=verified_candidate(call,edit)
        locale=details.get('defaultLanguage','')
        if not isinstance(locale,str) or not re.fullmatch(r'[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]{2,8}){0,2}',locale):raise SafeError('Default listing language unavailable')
        if not (1<=len(SHORT)<=80 and 80<=len(FULL)<=4000):raise SafeError('Listing copy outside Play bounds')
        path=PUBLISHER+'/'+edit+'/listings/'+urllib.parse.quote(locale,safe='')
        call(path,method='PUT',body={'language':locale,'title':'Passway','shortDescription':SHORT,'fullDescription':FULL})
        report['listingLanguage']=locale
        report['imageCounts']={kind:len(call(path+'/'+kind).get('images',[])) for kind in ['icon','featureGraphic','phoneScreenshots']}
        call(PUBLISHER+'/'+edit+'/tracks/production',method='PUT',body={'track':'production','releases':[{'name':'0.3.7 (13)','versionCodes':[str(VERSION)],'status':'draft'}]})
        call(PUBLISHER+'/'+edit+':validate',method='POST',body={})
        report['validated']=True
        report['commitAttempted']=True
        call(PUBLISHER+'/'+edit+':commit?changesNotSentForReview=true',method='POST',body={})
        committed=True;report['draftCommitted']=True;report['listingTextSaved']=True
    except Exception as e:
        report['draftCommitted']=False;report['error']=str(e) if isinstance(e,SafeError) else type(e).__name__
    finally:
        if edit and not committed:
            try:call(PUBLISHER+'/'+edit,method='DELETE');report['temporaryEditDeleted']=True
            except Exception:report['cleanupFailed']=True
    return report
if __name__=='__main__':
    try:result=prepare_draft(access_token(os.environ))
    except Exception as e:result={'draftCommitted':False,'publicProductionRollout':False,'error':str(e) if isinstance(e,SafeError) else type(e).__name__}
    Path('public-release-draft.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));raise SystemExit(0 if result.get('draftCommitted') else 1)
