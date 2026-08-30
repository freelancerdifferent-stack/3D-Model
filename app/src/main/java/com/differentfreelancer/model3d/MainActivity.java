package com.differentfreelancer.model3d;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.ContentValues;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Base64;
import android.view.View;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;

public class MainActivity extends Activity {
    private static final int FILE_CHOOSER_REQUEST = 1001;
    private WebView webView;
    private ValueCallback<Uri[]> fileCallback;

    @SuppressLint({"SetJavaScriptEnabled", "JavascriptInterface"})
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        enableImmersiveFullscreen();

        webView = new WebView(this);
        webView.setSystemUiVisibility(fullscreenFlags());
        setContentView(webView);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);

        webView.setWebViewClient(new WebViewClient());
        webView.addJavascriptInterface(new AndroidBridge(), "Android");
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (fileCallback != null) {
                    fileCallback.onReceiveValue(null);
                }
                fileCallback = callback;

                try {
                    Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                    intent.addCategory(Intent.CATEGORY_OPENABLE);
                    intent.setType("*/*");
                    intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[]{
                            "model/gltf-binary",
                            "model/gltf+json",
                            "application/octet-stream",
                            "application/x-fbx",
                            "application/vnd.autodesk.fbx",
                            "image/png"
                    });
                    intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, false);
                    intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);

                    startActivityForResult(
                            Intent.createChooser(intent, "Pilih GLB / FBX / PNG"),
                            FILE_CHOOSER_REQUEST
                    );
                    return true;
                } catch (Exception e) {
                    fileCallback = null;
                    Toast.makeText(MainActivity.this, "Tidak dapat membuka file picker", Toast.LENGTH_SHORT).show();
                    return false;
                }
            }
        });

        loadEditorHtml();
    }

    private void loadEditorHtml() {
        try {
            String html = readAssetText("index.html");

            // Inject an FBX-only compatibility pass into the existing module code.
            // GLB loading code is deliberately left unchanged.
            String marker = "function registerModel(obj,name,animations=[]){";
            String helper =
                    "function prepareFBXForViewer(obj){\n" +
                    "  obj.updateMatrixWorld(true);\n" +
                    "  obj.traverse(o=>{\n" +
                    "    if(o.isSkinnedMesh){\n" +
                    "      o.frustumCulled=false;\n" +
                    "      try{o.normalizeSkinWeights?.();}catch(e){}\n" +
                    "      if(o.skeleton){\n" +
                    "        try{\n" +
                    "          o.skeleton.pose();\n" +
                    "          o.skeleton.update();\n" +
                    "          o.bindMode='attached';\n" +
                    "          if(o.bindMatrix) o.bind(o.skeleton,o.bindMatrix);\n" +
                    "        }catch(e){console.warn('FBX skeleton repair',e);}\n" +
                    "      }\n" +
                    "      o.updateMatrixWorld(true);\n" +
                    "    }\n" +
                    "  });\n" +
                    "  obj.updateMatrixWorld(true);\n" +
                    "  return obj;\n" +
                    "}\n\n";

            if (html.contains(marker) && !html.contains("function prepareFBXForViewer")) {
                html = html.replace(marker, helper + marker);
            }

            String oldFbx =
                    "const obj=await new Promise((res,rej)=>new FBXLoader().load(url,res,undefined,rej));\n" +
                    "      registerModel(obj,f.name,obj.animations||[]);";
            String newFbx =
                    "const obj=await new Promise((res,rej)=>new FBXLoader().load(url,res,undefined,rej));\n" +
                    "      prepareFBXForViewer(obj);\n" +
                    "      registerModel(obj,f.name,obj.animations||[]);\n" +
                    "      requestAnimationFrame(()=>requestAnimationFrame(()=>{\n" +
                    "        if(root===obj){\n" +
                    "          prepareFBXForViewer(obj);\n" +
                    "          centerAndFit(obj);\n" +
                    "          updateTransformFields();\n" +
                    "        }\n" +
                    "      }));";

            if (html.contains(oldFbx)) {
                html = html.replace(oldFbx, newFbx);
            }

            webView.loadDataWithBaseURL(
                    "file:///android_asset/",
                    html,
                    "text/html",
                    "UTF-8",
                    null
            );
        } catch (Exception e) {
            // Safe fallback: if injection ever fails, open the untouched editor.
            webView.loadUrl("file:///android_asset/index.html");
        }
    }

    private String readAssetText(String fileName) throws Exception {
        StringBuilder out = new StringBuilder();
        InputStream input = getAssets().open(fileName);
        BufferedReader reader = new BufferedReader(new InputStreamReader(input, "UTF-8"));
        String line;
        while ((line = reader.readLine()) != null) {
            out.append(line).append('\n');
        }
        reader.close();
        input.close();
        return out.toString();
    }

    private int fullscreenFlags() {
        return View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                | View.SYSTEM_UI_FLAG_FULLSCREEN
                | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_LAYOUT_STABLE;
    }

    private void enableImmersiveFullscreen() {
        getWindow().getDecorView().setSystemUiVisibility(fullscreenFlags());
    }

    @Override
    protected void onResume() {
        super.onResume();
        enableImmersiveFullscreen();
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) {
            enableImmersiveFullscreen();
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == FILE_CHOOSER_REQUEST && fileCallback != null) {
            Uri[] result = null;

            if (resultCode == RESULT_OK && data != null && data.getData() != null) {
                Uri uri = data.getData();
                result = new Uri[]{uri};

                try {
                    final int takeFlags = data.getFlags() &
                            (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                    if ((takeFlags & Intent.FLAG_GRANT_READ_URI_PERMISSION) != 0) {
                        getContentResolver().takePersistableUriPermission(
                                uri,
                                Intent.FLAG_GRANT_READ_URI_PERMISSION
                        );
                    }
                } catch (Exception ignored) {
                }
            }

            fileCallback.onReceiveValue(result);
            fileCallback = null;
            enableImmersiveFullscreen();
        }
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    private class AndroidBridge {
        @JavascriptInterface
        public void saveBase64File(String base64Data, String fileName, String mimeType) {
            runOnUiThread(() -> {
                try {
                    byte[] bytes = Base64.decode(base64Data, Base64.DEFAULT);
                    OutputStream outputStream;

                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                        ContentValues values = new ContentValues();
                        values.put(MediaStore.Downloads.DISPLAY_NAME, fileName);
                        values.put(MediaStore.Downloads.MIME_TYPE, mimeType);
                        values.put(MediaStore.Downloads.RELATIVE_PATH,
                                Environment.DIRECTORY_DOWNLOADS + "/3D-Model");
                        Uri uri = getContentResolver().insert(
                                MediaStore.Downloads.EXTERNAL_CONTENT_URI,
                                values
                        );
                        if (uri == null) {
                            throw new IllegalStateException("Gagal membuat file output");
                        }
                        outputStream = getContentResolver().openOutputStream(uri);
                    } else {
                        File dir = new File(
                                getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS),
                                "3D-Model"
                        );
                        if (!dir.exists() && !dir.mkdirs()) {
                            throw new IllegalStateException("Gagal membuat folder output");
                        }
                        outputStream = new FileOutputStream(new File(dir, fileName));
                    }

                    if (outputStream == null) {
                        throw new IllegalStateException("Output stream tidak tersedia");
                    }
                    outputStream.write(bytes);
                    outputStream.flush();
                    outputStream.close();
                    Toast.makeText(MainActivity.this,
                            "Tersimpan: " + fileName,
                            Toast.LENGTH_LONG).show();
                } catch (Exception e) {
                    Toast.makeText(MainActivity.this,
                            "Export gagal: " + e.getMessage(),
                            Toast.LENGTH_LONG).show();
                }
            });
        }
    }
}
