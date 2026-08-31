package com.differentfreelancer.model3d;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ContentValues;
import android.content.Intent;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.DocumentsContract;
import android.provider.MediaStore;
import android.util.Base64;
import android.view.View;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.widget.Toast;

import androidx.webkit.WebViewAssetLoader;
import androidx.webkit.WebViewClientCompat;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

public class MainActivity extends Activity {
    private static final int FILE_CHOOSER_REQUEST = 1001;
    private static final int PROJECT_FOLDER_REQUEST = 1002;
    private static final String PREFS = "model3d_project_storage";
    private static final String PREF_PROJECT_TREE = "project_tree_uri";
    private static final String ASSET_BASE = "https://appassets.androidplatform.net/assets/";
    private WebView webView;
    private ValueCallback<Uri[]> fileCallback;
    private WebViewAssetLoader assetLoader;
    private String pendingProjectName;
    private String pendingProjectJson;

    @SuppressLint({"SetJavaScriptEnabled", "JavascriptInterface"})
    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState); enableImmersiveFullscreen();
        webView=new WebView(this); webView.setSystemUiVisibility(fullscreenFlags()); setContentView(webView);
        WebSettings settings=webView.getSettings(); settings.setJavaScriptEnabled(true); settings.setDomStorageEnabled(true); settings.setAllowFileAccess(true); settings.setAllowContentAccess(true); settings.setMediaPlaybackRequiresUserGesture(false); settings.setBuiltInZoomControls(false); settings.setDisplayZoomControls(false); settings.setCacheMode(WebSettings.LOAD_DEFAULT);

        assetLoader = new WebViewAssetLoader.Builder()
                .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
                .build();
        webView.setWebViewClient(new WebViewClientCompat(){
            @Override public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request){
                WebResourceResponse r=assetLoader.shouldInterceptRequest(request.getUrl());
                return r!=null?r:super.shouldInterceptRequest(view,request);
            }
            @Override public WebResourceResponse shouldInterceptRequest(WebView view,String url){
                WebResourceResponse r=assetLoader.shouldInterceptRequest(Uri.parse(url));
                return r!=null?r:super.shouldInterceptRequest(view,url);
            }
        });
        webView.addJavascriptInterface(new AndroidBridge(),"Android");
        webView.setWebChromeClient(new WebChromeClient(){@Override public boolean onShowFileChooser(WebView w,ValueCallback<Uri[]> callback,FileChooserParams params){if(fileCallback!=null)fileCallback.onReceiveValue(null);fileCallback=callback;try{Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("*/*");i.putExtra(Intent.EXTRA_MIME_TYPES,new String[]{"model/gltf-binary","model/gltf+json","application/octet-stream","application/x-fbx","application/vnd.autodesk.fbx","image/png"});i.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,false);i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);startActivityForResult(Intent.createChooser(i,"Pilih GLB / FBX / PNG"),FILE_CHOOSER_REQUEST);return true;}catch(Exception e){fileCallback=null;Toast.makeText(MainActivity.this,"Tidak dapat membuka file picker",Toast.LENGTH_SHORT).show();return false;}}});
        loadEditorHtml();
    }

    private void loadEditorHtml(){try{String html=readAssetText("index.html");String marker="function registerModel(obj,name,animations=[]){";String helper="function prepareFBXForViewer(obj){\n  obj.updateMatrixWorld(true);\n  obj.traverse(o=>{\n    if(o.isSkinnedMesh){\n      o.frustumCulled=false;\n      try{o.normalizeSkinWeights?.();}catch(e){}\n      if(o.skeleton){try{o.skeleton.pose();o.skeleton.update();o.bindMode='attached';if(o.bindMatrix)o.bind(o.skeleton,o.bindMatrix);}catch(e){console.warn('FBX skeleton repair',e);}}\n      o.updateMatrixWorld(true);\n    }\n  });\n  obj.updateMatrixWorld(true);\n  return obj;\n}\n\n";if(html.contains(marker)&&!html.contains("function prepareFBXForViewer"))html=html.replace(marker,helper+marker);String oldFbx="const obj=await new Promise((res,rej)=>new FBXLoader().load(url,res,undefined,rej));\n      registerModel(obj,f.name,obj.animations||[]);";String newFbx="const obj=await new Promise((res,rej)=>new FBXLoader().load(url,res,undefined,rej));\n      prepareFBXForViewer(obj);\n      registerModel(obj,f.name,obj.animations||[]);\n      requestAnimationFrame(()=>requestAnimationFrame(()=>{\n        if(root===obj){prepareFBXForViewer(obj);centerAndFit(obj);updateTransformFields();}\n      }));";if(html.contains(oldFbx))html=html.replace(oldFbx,newFbx);webView.loadDataWithBaseURL(ASSET_BASE,html,"text/html","UTF-8",null);}catch(Exception e){webView.loadUrl(ASSET_BASE+"index.html");}}
    private String readAssetText(String f)throws Exception{StringBuilder out=new StringBuilder();InputStream input=getAssets().open(f);BufferedReader r=new BufferedReader(new InputStreamReader(input,"UTF-8"));String line;while((line=r.readLine())!=null)out.append(line).append('\n');r.close();input.close();return out.toString();}
    private int fullscreenFlags(){return View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY|View.SYSTEM_UI_FLAG_FULLSCREEN|View.SYSTEM_UI_FLAG_HIDE_NAVIGATION|View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN|View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION|View.SYSTEM_UI_FLAG_LAYOUT_STABLE;}
    private void enableImmersiveFullscreen(){getWindow().getDecorView().setSystemUiVisibility(fullscreenFlags());}
    @Override protected void onResume(){super.onResume();enableImmersiveFullscreen();}
    @Override public void onWindowFocusChanged(boolean h){super.onWindowFocusChanged(h);if(h)enableImmersiveFullscreen();}

    private SharedPreferences prefs(){return getSharedPreferences(PREFS,MODE_PRIVATE);}
    private Uri projectTree(){String s=prefs().getString(PREF_PROJECT_TREE,null);return s==null?null:Uri.parse(s);}
    private void chooseProjectFolder(){Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION|Intent.FLAG_GRANT_PREFIX_URI_PERMISSION);Uri old=projectTree();if(old!=null&&Build.VERSION.SDK_INT>=26)i.putExtra(DocumentsContract.EXTRA_INITIAL_URI,old);startActivityForResult(i,PROJECT_FOLDER_REQUEST);}
    private String safeName(String n){String v=n==null?"Project":n.trim().replaceAll("[\\\\/:*?\"<>|]","_");return v.isEmpty()?"Project":v;}
    private Uri findChild(Uri tree,String name)throws Exception{Uri children=DocumentsContract.buildChildDocumentsUriUsingTree(tree,DocumentsContract.getTreeDocumentId(tree));try(Cursor c=getContentResolver().query(children,new String[]{DocumentsContract.Document.COLUMN_DOCUMENT_ID,DocumentsContract.Document.COLUMN_DISPLAY_NAME},null,null,null)){if(c!=null)while(c.moveToNext())if(name.equals(c.getString(1)))return DocumentsContract.buildDocumentUriUsingTree(tree,c.getString(0));}return null;}
    private Uri ensureProjectDir(Uri tree,String project)throws Exception{String name=safeName(project);Uri dir=findChild(tree,name);if(dir!=null)return dir;return DocumentsContract.createDocument(getContentResolver(),tree,DocumentsContract.Document.MIME_TYPE_DIR,name);}
    private Uri upsertFile(Uri dir,String name,String mime)throws Exception{Uri file=findChild(dir,name);if(file!=null)return file;return DocumentsContract.createDocument(getContentResolver(),dir,mime,name);}
    private void saveProjectJson(String project,String json){runOnUiThread(()->{try{Uri tree=projectTree();if(tree==null){pendingProjectName=project;pendingProjectJson=json;Toast.makeText(this,"Pilih folder project. Setelah dipilih project akan langsung disimpan.",Toast.LENGTH_LONG).show();chooseProjectFolder();return;}Uri dir=ensureProjectDir(tree,project);if(dir==null)throw new Exception("Folder project gagal dibuat");Uri file=upsertFile(dir,"project.json","application/json");if(file==null)throw new Exception("project.json gagal dibuat");try(OutputStream out=getContentResolver().openOutputStream(file,"rwt")){if(out==null)throw new Exception("Output tidak tersedia");out.write(json.getBytes(StandardCharsets.UTF_8));out.flush();}pendingProjectName=null;pendingProjectJson=null;Toast.makeText(this,"Project tersimpan: "+safeName(project),Toast.LENGTH_SHORT).show();webView.evaluateJavascript("window.onProjectSaveSuccess&&window.onProjectSaveSuccess("+quoteJs(safeName(project))+\")",null);webView.evaluateJavascript("window.onProjectFolderChosen&&window.onProjectFolderChosen("+quoteJs(safeName(project))+\")",null);}catch(Exception e){Toast.makeText(this,"Save project gagal: "+e.getMessage(),Toast.LENGTH_LONG).show();webView.evaluateJavascript("window.onProjectSaveError&&window.onProjectSaveError("+quoteJs(e.getMessage()==null?"Save project gagal":e.getMessage())+\")",null);}});}
    private String quoteJs(String s){return "\""+s.replace("\\","\\\\").replace("\"","\\\"").replace("\n","\\n")+"\"";}

    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data){super.onActivityResult(requestCode,resultCode,data);if(requestCode==PROJECT_FOLDER_REQUEST){if(resultCode==RESULT_OK&&data!=null&&data.getData()!=null){Uri uri=data.getData();try{getContentResolver().takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION);}catch(Exception ignored){}prefs().edit().putString(PREF_PROJECT_TREE,uri.toString()).apply();webView.evaluateJavascript("window.onProjectFolderChosen&&window.onProjectFolderChosen('Folder selected')",null);if(pendingProjectJson!=null){String n=pendingProjectName;String j=pendingProjectJson;pendingProjectName=null;pendingProjectJson=null;saveProjectJson(n,j);}}else{pendingProjectName=null;pendingProjectJson=null;webView.evaluateJavascript("window.onProjectFolderError&&window.onProjectFolderError('Pemilihan folder dibatalkan')",null);webView.evaluateJavascript("window.onProjectSaveError&&window.onProjectSaveError('Pemilihan folder dibatalkan')",null);}enableImmersiveFullscreen();return;}if(requestCode==FILE_CHOOSER_REQUEST&&fileCallback!=null){Uri[] result=null;if(resultCode==RESULT_OK&&data!=null&&data.getData()!=null){Uri uri=data.getData();result=new Uri[]{uri};try{int flags=data.getFlags()&(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION);if((flags&Intent.FLAG_GRANT_READ_URI_PERMISSION)!=0)getContentResolver().takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION);}catch(Exception ignored){}}fileCallback.onReceiveValue(result);fileCallback=null;enableImmersiveFullscreen();}}
    @Override public void onBackPressed(){if(webView!=null&&webView.canGoBack())webView.goBack();else super.onBackPressed();}

    private class AndroidBridge{
        @JavascriptInterface public void chooseProjectFolder(){runOnUiThread(MainActivity.this::chooseProjectFolder);}
        @JavascriptInterface public void saveProjectFile(String projectName,String json){saveProjectJson(projectName,json);}
        @JavascriptInterface public void saveBase64File(String base64Data,String fileName,String mimeType){runOnUiThread(()->{try{byte[] bytes=Base64.decode(base64Data,Base64.DEFAULT);OutputStream outputStream;if(Build.VERSION.SDK_INT>=Build.VERSION_CODES.Q){ContentValues values=new ContentValues();values.put(MediaStore.Downloads.DISPLAY_NAME,fileName);values.put(MediaStore.Downloads.MIME_TYPE,mimeType);values.put(MediaStore.Downloads.RELATIVE_PATH,Environment.DIRECTORY_DOWNLOADS+"/3D-Model");Uri uri=getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI,values);if(uri==null)throw new IllegalStateException("Gagal membuat file output");outputStream=getContentResolver().openOutputStream(uri);}else{File dir=new File(getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS),"3D-Model");if(!dir.exists()&&!dir.mkdirs())throw new IllegalStateException("Gagal membuat folder output");outputStream=new FileOutputStream(new File(dir,fileName));}if(outputStream==null)throw new IllegalStateException("Output stream tidak tersedia");outputStream.write(bytes);outputStream.flush();outputStream.close();Toast.makeText(MainActivity.this,"Tersimpan: "+fileName,Toast.LENGTH_LONG).show();}catch(Exception e){Toast.makeText(MainActivity.this,"Export gagal: "+e.getMessage(),Toast.LENGTH_LONG).show();}});}
    }
}
