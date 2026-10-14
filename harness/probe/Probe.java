package com.passway.nativeprobe;
import android.app.*;import android.os.*;import android.accessibilityservice.AccessibilityServiceInfo;import android.view.*;import android.view.accessibility.AccessibilityNodeInfo;import android.graphics.Rect;import android.util.*;import org.xmlpull.v1.XmlSerializer;import java.io.StringWriter;
public class Probe extends Instrumentation {
 Bundle options;
 public void onCreate(Bundle b){super.onCreate(b);options=b;start();}
 String text(CharSequence v){return v==null?"":v.toString().replaceAll("[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F]","");}
 String arg(String k)throws Exception{return new String(Base64.decode(options.getString(k,""),Base64.DEFAULT),"UTF-8");}
 AccessibilityNodeInfo locate(AccessibilityNodeInfo n,String s){
  if(n==null)return null;
  if(n.isVisibleToUser()&&(s.equals(text(n.getViewIdResourceName()))||s.equals(text(n.getText()))||s.equals(text(n.getContentDescription()))))return n;
  for(int i=0;i<n.getChildCount();i++){AccessibilityNodeInfo f=locate(n.getChild(i),s);if(f!=null)return f;}return null;
 }
 void walk(XmlSerializer x,AccessibilityNodeInfo n,int depth)throws Exception{
  if(n==null||depth>70)return;x.startTag("","node");Rect r=new Rect();n.getBoundsInScreen(r);
  x.attribute("","resource-id",text(n.getViewIdResourceName()));x.attribute("","text",text(n.getText()));x.attribute("","content-desc",text(n.getContentDescription()));x.attribute("","class",text(n.getClassName()));x.attribute("","package",text(n.getPackageName()));
  x.attribute("","bounds","["+r.left+","+r.top+"]["+r.right+","+r.bottom+"]");x.attribute("","visible-to-user",String.valueOf(n.isVisibleToUser()));x.attribute("","enabled",String.valueOf(n.isEnabled()));x.attribute("","clickable",String.valueOf(n.isClickable()));
  for(int i=0;i<n.getChildCount();i++)walk(x,n.getChild(i),depth+1);x.endTag("","node");
 }
 public void onStart(){Bundle result=new Bundle();try{
  UiAutomation a=getUiAutomation();AccessibilityServiceInfo info=a.getServiceInfo();info.flags|=AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS|AccessibilityServiceInfo.FLAG_INCLUDE_NOT_IMPORTANT_VIEWS|AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS;a.setServiceInfo(info);
  AccessibilityNodeInfo root=null;for(int i=0;i<20&&root==null;i++){root=a.getRootInActiveWindow();if(root==null)Thread.sleep(200);}if(root==null)throw new Exception("No active native accessibility root");root.refresh();
  String action=options.getString("action","");
  if(!action.isEmpty()){
   String selector=arg("selectorB64");AccessibilityNodeInfo target=null;for(int tries=0;tries<30&&target==null;tries++){root=a.getRootInActiveWindow();if(root!=null){root.refresh();target=locate(root,selector);}if(target==null)Thread.sleep(200);}if(target==null)throw new Exception("Visible action target missing: "+selector);
   if(action.equals("setText")){Bundle value=new Bundle();value.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE,arg("valueB64"));boolean changed=false;for(int tries=0;tries<12&&!changed;tries++){if(target!=null&&target.refresh()&&"android.widget.EditText".equals(text(target.getClassName())))changed=target.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT,value);if(!changed){Thread.sleep(200);root=a.getRootInActiveWindow();if(root!=null)root.refresh();target=locate(root,selector);}}if(!changed)throw new Exception("Native setText rejected after refreshing editable target: "+selector);}
   else if(action.equals("touch")){Rect r=new Rect();target.getBoundsInScreen(r);if(r.width()<=0||r.height()<=0)throw new Exception("Target outside visible viewport");float px=r.exactCenterX(),py=r.exactCenterY();long t=SystemClock.uptimeMillis();MotionEvent d=MotionEvent.obtain(t,t,MotionEvent.ACTION_DOWN,px,py,0);d.setSource(InputDevice.SOURCE_TOUCHSCREEN);if(!a.injectInputEvent(d,true))throw new Exception("Touch down rejected");Thread.sleep(100);MotionEvent u=MotionEvent.obtain(t,SystemClock.uptimeMillis(),MotionEvent.ACTION_UP,px,py,0);u.setSource(InputDevice.SOURCE_TOUCHSCREEN);if(!a.injectInputEvent(u,true))throw new Exception("Touch up rejected");d.recycle();u.recycle();}
   else throw new Exception("Unknown native action");result.putString("action_result","performed");Thread.sleep(500);root=a.getRootInActiveWindow();
  }
  StringWriter writer=new StringWriter();XmlSerializer x=Xml.newSerializer();x.setOutput(writer);x.startDocument("UTF-8",true);x.startTag("","hierarchy");walk(x,root,0);
  for(android.view.accessibility.AccessibilityWindowInfo w:a.getWindows()){Rect r=new Rect();w.getBoundsInScreen(r);x.startTag("","window");x.attribute("","type",String.valueOf(w.getType()));x.attribute("","layer",String.valueOf(w.getLayer()));x.attribute("","bounds","["+r.left+","+r.top+"]["+r.right+","+r.bottom+"]");x.endTag("","window");}
  x.endTag("","hierarchy");x.endDocument();result.putString("hierarchy",Base64.encodeToString(writer.toString().getBytes("UTF-8"),Base64.NO_WRAP));finish(0,result);
 }catch(Throwable e){result.putString("probe_error",e.toString());finish(1,result);}}
}
