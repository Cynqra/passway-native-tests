"""Validate an uncommitted public release edit. Never commit, upload, or change IAM."""
import json,os
from pathlib import Path
from play_api_access import access_token,SafeError,PUBLISHER
from internal_release import send
VERSION=13
BUNDLE_SHA='209d204b75a9e5f8d4041ca29a6a06adb61f9d604d162a62050d5a657528711f'

def reason_from_error(status,raw):
    try:text=json.loads(raw).get('error',{}).get('message','').lower()
    except (ValueError,AttributeError,TypeError):text=''
    if not isinstance(text,str):text=''
    groups=[('APP_SETUP_REQUIRED',('only releases with status draft','draft app')),('PRODUCTION_ACCESS_REQUIRED',('production access','access to production')),('AUTHORIZATION_OR_ACCOUNT_RESTRICTION',('permission','not authorized','not authorised')),('STORE_DECLARATIONS_REQUIRED',('declaration','privacy policy','data safety','content rating','target audience')),('STORE_LISTING_REQUIRED',('store listing','listing','screenshots','short description','full description')),('REVIEW_REQUIRED',('sent for review','send for review','changesnotsentforreview'))]
    return {'httpStatus':status,'requirement':next((name for name,patterns in groups if any(p in text for p in patterns)),'GOOGLE_VALIDATION_REJECTED')}

def verified_candidate(call,edit):
    tracks=call(PUBLISHER+'/'+edit+'/tracks').get('tracks',[])
    internal=next((t for t in tracks if t.get('track')=='internal'),{})
    if not any(r.get('status')=='completed' and r.get('versionCodes')==[str(VERSION)] for r in internal.get('releases',[])):raise SafeError('Expected verified internal candidate is not current')
    production=next((t for t in tracks if t.get('track')=='production'),{})
    if production.get('releases'):raise SafeError('Production track changed; existing releases will not be overwritten')
    bundles=call(PUBLISHER+'/'+edit+'/bundles').get('bundles',[])
    matches=[b for b in bundles if b.get('versionCode')==VERSION and b.get('sha256','').lower()==BUNDLE_SHA]
    if len(matches)!=1:raise SafeError('Verified existing bundle hash unavailable; no upload attempted')
    details=call(PUBLISHER+'/'+edit+'/details')
    listing=call(PUBLISHER+'/'+edit+'/listings').get('listings',[])
    return details,listing

def preflight(token,request=send):
    headers={'Authorization':'Bearer '+token};edit=None;report={'package':'com.passway.app','versionCode':VERSION,'publicProductionRollout':False,'commitAttempted':False,'uploadAttempted':False,'scope':'Uncommitted production edit validation only; not Google review approval, live public availability, attestation or SMS proof'}
    def observed(status,raw):report['googleRequirement']=reason_from_error(status,raw)
    def call(url,**kwargs):return request(url,headers=headers,error_observer=observed,**kwargs)
    try:
        edit=call(PUBLISHER,method='POST',body={}).get('id')
        if not isinstance(edit,str) or not edit.isdigit():raise SafeError('Invalid temporary edit identifier')
        details,listing=verified_candidate(call,edit)
        report['storeMetadata']={'defaultLanguagePresent':bool(details.get('defaultLanguage')),'contactEmailPresent':bool(details.get('contactEmail')),'listingCount':len(listing),'completeTextListings':sum(bool(x.get('title') and x.get('shortDescription') and x.get('fullDescription')) for x in listing)}
        call(PUBLISHER+'/'+edit+'/tracks/production',method='PUT',body={'track':'production','releases':[{'name':'0.3.7 (13)','versionCodes':[str(VERSION)],'status':'completed'}]})
        report['temporaryProductionEditPrepared']=True
        call(PUBLISHER+'/'+edit+':validate',method='POST',body={})
        report['validated']=True
    except Exception as e:
        report['validated']=False;report['error']=str(e) if isinstance(e,SafeError) else type(e).__name__
    finally:
        if edit:
            try:call(PUBLISHER+'/'+edit,method='DELETE');report['temporaryEditDeleted']=True
            except Exception:report['temporaryEditDeleted']=False;report['validated']=False;report['cleanupFailed']=True
    return report
if __name__=='__main__':
    try:result=preflight(access_token(os.environ))
    except Exception as e:result={'validated':False,'publicProductionRollout':False,'commitAttempted':False,'error':str(e) if isinstance(e,SafeError) else type(e).__name__}
    Path('public-release-preflight.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));raise SystemExit(0 if result.get('validated') and result.get('temporaryEditDeleted') else 1)
