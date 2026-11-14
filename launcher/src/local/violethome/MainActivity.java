package local.violethome;

import android.app.Activity;
import android.app.Dialog;
import android.app.AlertDialog;
import android.net.Uri;
import android.text.InputType;
import android.content.SharedPreferences;
import android.widget.EditText;
import android.widget.TextClock;
import android.content.Intent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.IntentFilter;
import android.os.UserManager;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.graphics.Canvas;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.RectF;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Shader;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.GridLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class MainActivity extends Activity {
    private PackageManager pm;
    private SharedPreferences prefs;
    private TextView dateView;
    private static final String PROMO_SOURCE_URL = "https://lmnprj.github.io/api/announcement.json";
    private static final long PROMO_REFRESH_MS = 15 * 60 * 1000L;
    private final android.os.Handler promoHandler = new android.os.Handler(android.os.Looper.getMainLooper());
    private final Runnable promoTimer = new Runnable(){public void run(){refreshRemotePromo();promoHandler.postDelayed(this,PROMO_REFRESH_MS);}};
    private volatile boolean promoLoading;
    private long promoLastAttempt;
    private void updateDate(){if(dateView!=null)dateView.setText(new java.text.SimpleDateFormat("EEEE, d MMMM",java.util.Locale.ENGLISH).format(new java.util.Date()));}
    private final BroadcastReceiver dateReceiver=new BroadcastReceiver(){@Override public void onReceive(Context c,Intent i){updateDate();}};
    private final BroadcastReceiver unlockReceiver = new BroadcastReceiver() { @Override public void onReceive(Context context, Intent intent) { render(); } };
    private final int bg = Color.rgb(7, 5, 14);
    private int dp(float v) { return (int)(v * getResources().getDisplayMetrics().density + .5f); }
    private GradientDrawable shape(int color, int border, int radius) {
        GradientDrawable d = new GradientDrawable(); d.setColor(color); d.setCornerRadius(dp(radius));
        if (border != 0) d.setStroke(dp(1), border); return d;
    }
    private class Wallpaper extends View {
        private final Paint paint = new Paint(3);
        private final Bitmap mark;
        Wallpaper() { super(MainActivity.this); mark=BitmapFactory.decodeResource(getResources(),getResources().getIdentifier("af_mark","drawable",getPackageName())); }
        @Override protected void onDraw(Canvas canvas) {
            float w=getWidth(), h=getHeight(); canvas.drawColor(bg);
            Path ribbon=new Path(); ribbon.moveTo(0,h*.94f);
            ribbon.cubicTo(w*.12f,h*.56f,w*.18f,h*.51f,w*.40f,h*.47f);
            ribbon.cubicTo(w*.67f,h*.42f,w*.86f,h*.29f,w*1.04f,h*.04f);
            ribbon.cubicTo(w*.94f,h*.30f,w*.82f,h*.48f,w*.60f,h*.57f);
            ribbon.cubicTo(w*.33f,h*.68f,w*.13f,h*.69f,0,h*1.04f); ribbon.close();
            paint.setShader(new LinearGradient(0,h*.7f,w,h*.15f,new int[]{0xff15091f,0xff3a0c68,0xff180526},null,Shader.TileMode.CLAMP)); canvas.drawPath(ribbon,paint); paint.setShader(null);
            if(mark!=null){float mw=Math.min(w*.52f,dp(560)), mh=mw;paint.setAlpha(55);canvas.drawBitmap(mark,null,new RectF((w-mw)/2f,h*.50f-mh*.54f,(w+mw)/2f,h*.50f+mh*.46f),paint);paint.setAlpha(255);}
            paint.setColor(0xff9a78b5);paint.setStrokeWidth(dp(1));paint.setStyle(Paint.Style.STROKE);Path beam=new Path();beam.moveTo(w*.04f,h*.77f);beam.cubicTo(w*.22f,h*.42f,w*.62f,h*.65f,w*.97f,h*.19f);paint.setAlpha(55);canvas.drawPath(beam,paint);paint.setAlpha(255);paint.setStyle(Paint.Style.FILL);
            paint.setColor(0xff84639e); paint.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL)); paint.setTextSize(Math.min(w*.043f,dp(38))); paint.setTextAlign(Paint.Align.CENTER);
            canvas.drawText("A L L   F I C T I O N", w*.5f, h*.50f, paint);
        }
    }

    @Override public void onCreate(Bundle b) {
        super.onCreate(b); getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN, WindowManager.LayoutParams.FLAG_FULLSCREEN); pm=getPackageManager(); prefs=createDeviceProtectedStorageContext().getSharedPreferences("all_fiction", MODE_PRIVATE); getWindow().setStatusBarColor(Color.BLACK); getWindow().setNavigationBarColor(bg); registerReceiver(unlockReceiver, new IntentFilter(Intent.ACTION_USER_UNLOCKED), Context.RECEIVER_NOT_EXPORTED); IntentFilter df=new IntentFilter(Intent.ACTION_TIME_TICK);df.addAction(Intent.ACTION_TIME_CHANGED);df.addAction(Intent.ACTION_TIMEZONE_CHANGED);registerReceiver(dateReceiver,df,Context.RECEIVER_NOT_EXPORTED); render(); promoHandler.postDelayed(promoTimer,PROMO_REFRESH_MS);
    }
    @Override protected void onDestroy() { promoHandler.removeCallbacks(promoTimer); unregisterReceiver(unlockReceiver); unregisterReceiver(dateReceiver); super.onDestroy(); }
    private void launch(String pkg) {
        Intent i=pm.getLaunchIntentForPackage(pkg);
        if(i==null && pkg.equals("com.android.settings")) i=new Intent(android.provider.Settings.ACTION_SETTINGS);
        try { if(i!=null) startActivity(i); else Toast.makeText(this,"Приложение недоступно",Toast.LENGTH_SHORT).show(); }
        catch(Exception e) { Toast.makeText(this,"Не удалось открыть приложение",Toast.LENGTH_SHORT).show(); }
    }
    private void addDockIcon(LinearLayout dock, final String pkg, String title) {
        ImageView icon=new ImageView(this);
        icon.setPadding(dp(6),dp(6),dp(6),dp(6));
        icon.setBackground(shape(0xff1c1428,0xff493650,9));
        try { icon.setImageDrawable(pm.getApplicationIcon(pkg)); } catch(Exception e) { return; }
        icon.setContentDescription(title); icon.setScaleType(ImageView.ScaleType.FIT_CENTER);
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(dp(42),dp(42));p.setMargins(dp(2),dp(2),dp(2),dp(2)); dock.addView(icon,p);
        icon.setOnClickListener(new View.OnClickListener(){ public void onClick(View v){launch(pkg);} });
    }
    private boolean addRailIcon(GridLayout grid,final String pkg,String title) {
        android.graphics.drawable.Drawable appIcon;try { appIcon=pm.getApplicationIcon(pkg); } catch(Exception e){ return false; }
        LinearLayout cell=new LinearLayout(this);cell.setOrientation(1);cell.setGravity(Gravity.CENTER);cell.setPadding(dp(3),dp(4),dp(3),dp(4));cell.setBackground(shape(0xff271534,0xff4b315d,12));
        ImageView icon=new ImageView(this);icon.setImageDrawable(appIcon);icon.setScaleType(ImageView.ScaleType.FIT_CENTER);cell.addView(icon,new LinearLayout.LayoutParams(dp(38),dp(38)));
        TextView label=new TextView(this);label.setText(title);label.setTextColor(0xffe9dbf5);label.setTextSize(10);label.setTypeface(Typeface.DEFAULT,Typeface.BOLD);label.setGravity(Gravity.CENTER);label.setSingleLine(true);label.setEllipsize(android.text.TextUtils.TruncateAt.END);cell.addView(label,new LinearLayout.LayoutParams(dp(62),dp(20)));cell.setContentDescription(title);
        GridLayout.LayoutParams lp=new GridLayout.LayoutParams();lp.width=dp(68);lp.height=dp(70);lp.setMargins(dp(3),dp(3),dp(3),dp(3));grid.addView(cell,lp);cell.setOnClickListener(v->launch(pkg));if(pkg.equals("com.android.settings"))cell.setOnLongClickListener(v->{showAbout();return true;});
        cell.setOnHoverListener(new View.OnHoverListener(){
            private boolean hovered;
            @Override public boolean onHover(View v, android.view.MotionEvent event){
                int action=event.getActionMasked();
                boolean inside=action==android.view.MotionEvent.ACTION_HOVER_ENTER || action==android.view.MotionEvent.ACTION_HOVER_MOVE;
                if(inside && !hovered){hovered=true;v.animate().cancel();v.animate().scaleX(1.06f).scaleY(1.06f).setDuration(150).start();}
                else if(action==android.view.MotionEvent.ACTION_HOVER_EXIT && hovered){hovered=false;v.animate().cancel();v.animate().scaleX(1f).scaleY(1f).setDuration(180).start();}
                return false;
            }
        });return true;
    }
    @Override protected void onResume(){super.onResume();if(pm!=null)render();}
    private void render() {
        FrameLayout root=new FrameLayout(this); root.addView(new Wallpaper(),new FrameLayout.LayoutParams(-1,-1));
        UserManager users=(UserManager)getSystemService(Context.USER_SERVICE);
        if (users != null && !users.isUserUnlocked()) { setContentView(root); return; }
        LinearLayout rail=new LinearLayout(this);rail.setOrientation(LinearLayout.VERTICAL);rail.setPadding(dp(8),dp(12),dp(8),dp(12));rail.setBackground(shape(0xed180b26,0xff4a2a60,18));
        TextView railTitle=new TextView(this);railTitle.setText("ПРИЛОЖЕНИЯ");railTitle.setTextColor(0xffc49de5);railTitle.setTextSize(8);railTitle.setTypeface(Typeface.DEFAULT,Typeface.BOLD);railTitle.setLetterSpacing(.08f);railTitle.setGravity(Gravity.CENTER);rail.addView(railTitle);
        ScrollView scroller=new ScrollView(this);scroller.setFillViewport(false);scroller.setVerticalScrollBarEnabled(true);GridLayout grid=new GridLayout(this);grid.setColumnCount(1);grid.setPadding(0,dp(8),0,0);scroller.addView(grid);rail.addView(scroller,new LinearLayout.LayoutParams(-2,0,1));
        Set<String> shown=new HashSet<String>();String[][] common={{"com.android.vending","Play Маркет"},{"com.google.android.play.games","Play Игры"},{"com.android.chromium","Браузер"},{"com.android.documentsui","Файлы"},{"com.android.gallery3d","Галерея"},{"com.android.settings","Настройки"}};
        for(String[] item:common)if(addRailIcon(grid,item[0],item[1]))shown.add(item[0]);
        Intent all=new Intent(Intent.ACTION_MAIN);all.addCategory(Intent.CATEGORY_LAUNCHER);List<ResolveInfo> available=pm.queryIntentActivities(all,0);Collections.sort(available,new ResolveInfo.DisplayNameComparator(pm));for(ResolveInfo r:available){String pkg=r.activityInfo.packageName;if(pkg.equals(getPackageName())||shown.contains(pkg))continue;try{if(!pm.getApplicationInfo(pkg,0).enabled)continue;}catch(Exception ex){continue;}if(addRailIcon(grid,pkg,String.valueOf(r.loadLabel(pm))))shown.add(pkg);}
        int railHeight=Math.max(dp(170),Math.min(dp(600),getResources().getDisplayMetrics().heightPixels-dp(36)));FrameLayout.LayoutParams rp=new FrameLayout.LayoutParams(dp(92),railHeight,Gravity.RIGHT|Gravity.CENTER_VERTICAL);rp.rightMargin=dp(16);root.addView(rail,rp);
        LinearLayout timeBox=new LinearLayout(this);timeBox.setOrientation(1);timeBox.setGravity(Gravity.CENTER);TextClock clock=new TextClock(this);clock.setFormat12Hour("HH:mm");clock.setFormat24Hour("HH:mm");clock.setTextSize(38);clock.setTextColor(0xfff2e9fa);clock.setTypeface(Typeface.create("sans-serif-light",Typeface.NORMAL));clock.setGravity(Gravity.CENTER);timeBox.addView(clock,new LinearLayout.LayoutParams(-1,-2));TextView date=new TextView(this);dateView=date;updateDate();date.setTextSize(12);date.setTextColor(0xffaa94ba);date.setGravity(Gravity.CENTER);timeBox.addView(date,new LinearLayout.LayoutParams(-1,-2));FrameLayout.LayoutParams tp=new FrameLayout.LayoutParams(-2,-2,Gravity.TOP|Gravity.CENTER_HORIZONTAL);tp.topMargin=dp(24);root.addView(timeBox,tp);
        LinearLayout about=new LinearLayout(this);about.setOrientation(LinearLayout.VERTICAL);about.setPadding(dp(16),dp(13),dp(16),dp(13));about.setBackground(shape(0xe91b1028,0xff43304f,16));about.setContentDescription("Об эмуляторе ALL FICTION");
        TextView aboutEyebrow=new TextView(this);aboutEyebrow.setText("ALL FICTION  /  ОБ ЭМУЛЯТОРЕ");aboutEyebrow.setTextSize(10);aboutEyebrow.setTypeface(Typeface.DEFAULT,Typeface.BOLD);aboutEyebrow.setLetterSpacing(.08f);aboutEyebrow.setTextColor(0xffae8ec7);about.addView(aboutEyebrow);
        TextView aboutTitle=new TextView(this);aboutTitle.setText("Играй с комфортом");aboutTitle.setTextSize(15);aboutTitle.setTypeface(Typeface.DEFAULT,Typeface.BOLD);aboutTitle.setTextColor(0xfff2eafa);aboutTitle.setPadding(0,dp(7),0,0);about.addView(aboutTitle);
        TextView aboutText=new TextView(this);aboutText.setText("Android-эмулятор для Windows от LIMINAL PROJECT на базе MuMu Player.");aboutText.setTextSize(13);aboutText.setTextColor(0xffd5c4e5);aboutText.setPadding(0,dp(6),0,dp(6));about.addView(aboutText);
        String[] aboutNames={"САЙТ", "ALL FICTION", "TELEGRAM", "YOUTUBE"};String[] aboutUrls={"https://lmnprj.github.io/","https://lmnprj.github.io/all-fiction.html","https://t.me/lmnprj","https://www.youtube.com/@lmnprj"};for(int row=0;row<2;row++){LinearLayout links=new LinearLayout(this);links.setOrientation(LinearLayout.HORIZONTAL);for(int col=0;col<2;col++){int i=row*2+col;TextView link=new TextView(this);link.setText(aboutNames[i]+"  ↗");link.setTextSize(10);link.setTypeface(Typeface.DEFAULT,Typeface.BOLD);link.setTextColor(0xffc894f4);link.setPadding(0,dp(7),dp(4),dp(7));final String url=aboutUrls[i];link.setOnClickListener(v->openUrl(url));links.addView(link,new LinearLayout.LayoutParams(0,-2,1));}about.addView(links);}
        TextView email=new TextView(this);email.setText("ПОЧТА  ·  lmnpr@proton.me");email.setTextSize(11);email.setTypeface(Typeface.DEFAULT,Typeface.BOLD);email.setTextColor(0xffc894f4);email.setPadding(0,dp(6),0,dp(2));email.setOnClickListener(v->{android.content.ClipboardManager clipboard=(android.content.ClipboardManager)getSystemService(Context.CLIPBOARD_SERVICE);clipboard.setPrimaryClip(android.content.ClipData.newPlainText("Email", "lmnpr@proton.me"));Toast.makeText(this,"Почта скопирована",Toast.LENGTH_SHORT).show();});about.addView(email);
        FrameLayout.LayoutParams ap=new FrameLayout.LayoutParams(dp(270),-2,Gravity.TOP|Gravity.LEFT);ap.leftMargin=dp(20);ap.topMargin=dp(24);root.addView(about,ap);
        String ad=displayPromoTitle();
        if (!ad.isEmpty()) {
            LinearLayout promo=new LinearLayout(this);promo.setOrientation(1);promo.setPadding(dp(16),dp(13),dp(16),dp(13));promo.setBackground(shape(0xe91b1028,0xff43304f,16));
            TextView eyebrow=new TextView(this);eyebrow.setText("ALL FICTION  /  ОБЪЯВЛЕНИЕ");eyebrow.setTextSize(10);eyebrow.setTypeface(Typeface.DEFAULT,Typeface.BOLD);eyebrow.setLetterSpacing(.10f);eyebrow.setTextColor(0xffae8ec7);promo.addView(eyebrow);
            TextView title=new TextView(this);title.setText(ad);title.setTextSize(15);title.setTypeface(Typeface.DEFAULT,Typeface.BOLD);title.setTextColor(0xfff2eafa);title.setPadding(0,dp(7),0,0);promo.addView(title);
            ScrollView descriptionScroll=new ScrollView(this){
                private float downX,downY;
                @Override protected void onMeasure(int w,int h){super.onMeasure(w,View.MeasureSpec.makeMeasureSpec(dp(165),View.MeasureSpec.AT_MOST));}
                @Override public boolean dispatchTouchEvent(android.view.MotionEvent e){int a=e.getActionMasked();if(a==android.view.MotionEvent.ACTION_DOWN){downX=e.getX();downY=e.getY();}boolean handled=super.dispatchTouchEvent(e);if(a==android.view.MotionEvent.ACTION_UP&&Math.abs(e.getX()-downX)<dp(8)&&Math.abs(e.getY()-downY)<dp(8)){promo.performClick();return true;}return handled||a==android.view.MotionEvent.ACTION_DOWN;}
            };
            descriptionScroll.setFillViewport(false);TextView description=new TextView(this);description.setText(prefs.getString("promo_remote_text",""));description.setTextSize(13);description.setTextColor(0xffd5c4e5);description.setPadding(0,dp(6),0,0);descriptionScroll.addView(description);promo.addView(descriptionScroll,new LinearLayout.LayoutParams(-1,-2));
            TextView action=new TextView(this);action.setText("ОТКРЫТЬ  ↗");action.setTextSize(10);action.setTypeface(Typeface.DEFAULT,Typeface.BOLD);action.setLetterSpacing(.08f);action.setTextColor(0xffc894f4);action.setPadding(0,dp(8),0,0);promo.addView(action);
            FrameLayout.LayoutParams pp=new FrameLayout.LayoutParams(dp(270),-2,Gravity.BOTTOM|Gravity.LEFT);pp.leftMargin=dp(20);pp.bottomMargin=dp(64);root.addView(promo,pp);promo.setOnClickListener(v->{String u=displayPromoUrl();if(!u.isEmpty())openUrl(u);});
        }
        setContentView(root);
        refreshRemotePromo();
    }

    private void openUrl(String url) {
        final String target = url.trim();
        if (!httpsUrl(target)) { Toast.makeText(this, "Некорректная HTTPS-ссылка", Toast.LENGTH_SHORT).show(); return; }
        new Thread(() -> {
            java.net.HttpURLConnection connection = null;
            try {
                connection = (java.net.HttpURLConnection) new java.net.URL("http://127.0.0.1:38471/open").openConnection();
                connection.setConnectTimeout(3000); connection.setReadTimeout(3000);
                connection.setRequestMethod("POST"); connection.setDoOutput(true);
                connection.setRequestProperty("Content-Type", "text/plain; charset=utf-8");
                connection.setRequestProperty("X-AF-Token", "REPLACE_WITH_SHARED_BRIDGE_TOKEN");
                byte[] body = target.getBytes(java.nio.charset.StandardCharsets.UTF_8);
                connection.setFixedLengthStreamingMode(body.length);
                try (java.io.OutputStream out = connection.getOutputStream()) { out.write(body); }
                if (connection.getResponseCode() != 204) throw new java.io.IOException("Bridge error");
            } catch (Exception e) {
                runOnUiThread(() -> Toast.makeText(this, "Мост Windows не запущен или MuMu не подключён", Toast.LENGTH_LONG).show());
            } finally { if (connection != null) connection.disconnect(); }
        }, "af-open-windows").start();
    }
    private LinearLayout form() { LinearLayout l=new LinearLayout(this);l.setOrientation(1);int pad=dp(20);l.setPadding(pad,dp(8),pad,0);return l; }
    private EditText field(LinearLayout l,String hint,String value) { EditText e=new EditText(this);e.setSingleLine(true);e.setTextColor(0xfff4ecfa);e.setHintTextColor(0xff8d7c9a);e.setHint(hint);e.setText(value);e.setInputType(InputType.TYPE_CLASS_TEXT);l.addView(e,new LinearLayout.LayoutParams(-1,dp(52)));return e; }
    private boolean httpsUrl(String url) { try { Uri u=Uri.parse(url);return "https".equalsIgnoreCase(u.getScheme()) && u.getHost()!=null && u.getUserInfo()==null; } catch(Exception e){return false;} }
    private String displayPromoTitle(){String title=prefs.getString("promo_remote_title","");String text=prefs.getString("promo_remote_text","");String url=prefs.getString("promo_remote_url","");return !title.isEmpty()&&!text.isEmpty()&&httpsUrl(url)?title:"";}
    private String displayPromoUrl(){return prefs.getString("promo_remote_url","");}
    private void refreshRemotePromo(){
        final String source=PROMO_SOURCE_URL;long now=android.os.SystemClock.elapsedRealtime();
        if(promoLoading||(promoLastAttempt!=0&&now-promoLastAttempt<PROMO_REFRESH_MS))return;
        promoLoading=true;promoLastAttempt=now;
        new Thread(()->{java.net.HttpURLConnection conn=null;String title=null,text=null,url=null;
            try{java.net.URL u=new java.net.URL(source);conn=(java.net.HttpURLConnection)u.openConnection();conn.setInstanceFollowRedirects(false);conn.setConnectTimeout(7000);conn.setReadTimeout(7000);conn.setRequestProperty("Accept","application/json");conn.setRequestProperty("Cache-Control","no-cache, no-store, max-age=0");conn.setRequestProperty("Pragma","no-cache");conn.setUseCaches(false);
                if(conn.getResponseCode()!=200)throw new java.io.IOException("HTTP response");
                try(java.io.InputStream in=conn.getInputStream();java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream()){byte[] b=new byte[2048];int n;while((n=in.read(b))!=-1){if(out.size()+n>16384)throw new java.io.IOException("Response too large");out.write(b,0,n);}org.json.JSONObject json=new org.json.JSONObject(out.toString("UTF-8"));Object t=json.get("title"),d=json.get("text"),l=json.get("url");if(!(t instanceof String)||!(d instanceof String)||!(l instanceof String))throw new java.io.IOException("Invalid fields");title=((String)t).trim();text=((String)d).trim();url=((String)l).trim();if(title.isEmpty()||title.length()>200||text.isEmpty()||text.length()>4096||!httpsUrl(url))throw new java.io.IOException("Invalid announcement");}
            }catch(Exception ignored){title=null;}finally{if(conn!=null)conn.disconnect();}
            final String resultTitle=title,resultText=text,resultUrl=url;runOnUiThread(()->{promoLoading=false;if(isFinishing()||isDestroyed())return;if(resultTitle!=null){String previous=prefs.getString("promo_remote_title","");String previousText=prefs.getString("promo_remote_text","");String previousUrl=prefs.getString("promo_remote_url","");if(!resultTitle.equals(previous)||!resultText.equals(previousText)||!resultUrl.equals(previousUrl)){prefs.edit().putString("promo_remote_title",resultTitle).putString("promo_remote_text",resultText).putString("promo_remote_url",resultUrl).apply();render();}}});
        },"af-promo-fetch").start();
    }
    private void editLinks() { LinearLayout f=form();EditText site=field(f,"Сайт — https://",prefs.getString("link_site",""));EditText tg=field(f,"Telegram — https://",prefs.getString("link_telegram",""));EditText video=field(f,"Видео — https://",prefs.getString("link_video",""));new AlertDialog.Builder(this).setTitle("Мои ссылки").setView(f).setNegativeButton("Отмена",null).setPositiveButton("Сохранить",(d,w)->{String[] values={site.getText().toString().trim(),tg.getText().toString().trim(),video.getText().toString().trim()};for(String v:values)if(!v.isEmpty()&&(!v.startsWith("https://")||Uri.parse(v).getHost()==null)){Toast.makeText(this,"Ссылки должны начинаться с https://",Toast.LENGTH_SHORT).show();return;}prefs.edit().putString("link_site",values[0]).putString("link_telegram",values[1]).putString("link_video",values[2]).apply();}).show(); }
    private void showAbout() { LinearLayout body=form();TextView description=new TextView(this);description.setText("ALL FICTION — игровой Android-эмулятор для Windows от LIMINAL PROJECT на базе MuMu Player.\n\nПроизводительность, стабильность и удобство игры.");description.setTextColor(0xffe8dbf5);description.setTextSize(14);description.setPadding(0,0,0,dp(12));body.addView(description);String[] names={"Сайт проекта  ↗","Страница ALL FICTION  ↗","Telegram  ↗","YouTube  ↗"};String[] urls={"https://lmnprj.github.io/","https://lmnprj.github.io/all-fiction.html","https://t.me/lmnprj","https://www.youtube.com/@lmnprj"};for(int i=0;i<names.length;i++){final String url=urls[i];TextView link=new TextView(this);link.setText(names[i]);link.setTextSize(15);link.setTypeface(Typeface.DEFAULT,Typeface.BOLD);link.setTextColor(0xffc894f4);link.setPadding(dp(6),dp(10),dp(6),dp(10));link.setOnClickListener(v->openUrl(url));body.addView(link);}new AlertDialog.Builder(this).setTitle("Об эмуляторе · ALL FICTION").setView(body).setNegativeButton("Закрыть",null).show(); }

    private void showApps() {
        final Dialog dialog=new Dialog(this); dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        LinearLayout panel=new LinearLayout(this);panel.setOrientation(LinearLayout.VERTICAL);panel.setPadding(dp(20),dp(18),dp(20),dp(18));panel.setBackground(shape(0xff110b1b,0xff493650,18));
        TextView header=new TextView(this);header.setText("ИГРЫ И ПРИЛОЖЕНИЯ");header.setTextSize(14);header.setTextColor(0xffc0a2da);header.setLetterSpacing(.12f);panel.addView(header);
        Intent query=new Intent(Intent.ACTION_MAIN);query.addCategory(Intent.CATEGORY_LAUNCHER);List<ResolveInfo> list=pm.queryIntentActivities(query,0);Collections.sort(list,new ResolveInfo.DisplayNameComparator(pm));
        ScrollView scroll=new ScrollView(this);GridLayout grid=new GridLayout(this);grid.setColumnCount(4);scroll.addView(grid);panel.addView(scroll);
        Set<String> seen=new HashSet<String>();int count=0;
        for(ResolveInfo r:list){final String pkg=r.activityInfo.packageName;if(pkg.equals(getPackageName())||!seen.add(pkg))continue;
            try{ApplicationInfo info=pm.getApplicationInfo(pkg,0);if((info.flags & ApplicationInfo.FLAG_SYSTEM)!=0 || !info.enabled)continue;}catch(Exception ex){continue;}
            count++;LinearLayout item=new LinearLayout(this);item.setOrientation(1);item.setGravity(Gravity.CENTER);item.setPadding(dp(8),dp(10),dp(8),dp(10));
            ImageView icon=new ImageView(this);icon.setImageDrawable(r.loadIcon(pm));item.addView(icon,new LinearLayout.LayoutParams(dp(42),dp(42)));
            TextView name=new TextView(this);name.setText(r.loadLabel(pm));name.setTextSize(11);name.setTextColor(0xffeae3ef);name.setGravity(Gravity.CENTER);name.setMaxLines(2);item.addView(name,new LinearLayout.LayoutParams(dp(100),dp(38)));
            grid.addView(item);item.setOnClickListener(new View.OnClickListener(){public void onClick(View v){dialog.dismiss();launch(pkg);}});
        }
        if(count==0){TextView empty=new TextView(this);empty.setText("Установленные игры появятся здесь автоматически.");empty.setTextColor(0xff9f8eaa);empty.setPadding(0,dp(20),0,dp(10));panel.addView(empty);}
        dialog.setContentView(panel);Window window=dialog.getWindow();if(window!=null){window.setBackgroundDrawableResource(android.R.color.transparent);window.setLayout(Math.min(getResources().getDisplayMetrics().widthPixels-dp(32),dp(480)),WindowManager.LayoutParams.WRAP_CONTENT);}dialog.show();
        if(window!=null)window.setLayout(Math.min(getResources().getDisplayMetrics().widthPixels-dp(32),dp(480)),WindowManager.LayoutParams.WRAP_CONTENT);
    }
}

