from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import os

app = FastAPI(title="Typing Master Pro")

HTML_PAGE = r"""<!doctype html>
<html lang="ar" dir="rtl" data-theme="Dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>Typing Master Pro</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#0b0d14; --panel:rgba(20,24,35,.85); --surface:rgba(255,255,255,.05);
  --text:#f1f5f9; --muted:#94a3b8; --border:rgba(255,255,255,.1);
  --accent:#8b5cf6; --accent2:#06b6d4; --success:#10b981; --danger:#ef4444;
  --grad: linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%);
  --shadow: 0 20px 60px rgba(0,0,0,.4);
}
html[data-theme="Light"]{--bg:#f0f4f8;--panel:rgba(255,255,255,.9);--surface:rgba(0,0,0,.04);--text:#0f172a;--muted:#64748b;--border:rgba(0,0,0,.1);--shadow:0 10px 40px rgba(0,0,0,.1)}
html[data-theme="Midnight"]{--bg:#030712;--panel:rgba(10,15,30,.9);--accent:#3b82f6;--accent2:#8b5cf6;--grad:linear-gradient(135deg,#3b82f6,#8b5cf6)}
html[data-theme="Ocean"]{--bg:#041c2c;--panel:rgba(8,40,60,.88);--accent:#06b6d4;--accent2:#10b981;--grad:linear-gradient(135deg,#06b6d4,#10b981)}
html[data-theme="Sunset"]{--bg:#2a1017;--panel:rgba(50,20,30,.88);--accent:#f97316;--accent2:#ec4899;--grad:linear-gradient(135deg,#f97316,#ec4899)}
html[data-theme="Forest"]{--bg:#0a1f14;--panel:rgba(15,40,25,.88);--accent:#10b981;--accent2:#84cc16;--grad:linear-gradient(135deg,#10b981,#84cc16)}
html[data-theme="Cyberpunk"]{--bg:#1a0b2e;--panel:rgba(30,15,55,.9);--accent:#ec4899;--accent2:#f59e0b;--grad:linear-gradient(135deg,#ec4899,#f59e0b)}

*{box-sizing:border-box;margin:0;padding:0}
body{min-height:100vh;background:radial-gradient(ellipse at top, var(--surface), transparent 50%), var(--bg);color:var(--text);font:13px 'Inter','IBM Plex Sans Arabic',sans-serif;display:flex;justify-content:center;align-items:center;padding:12px;transition:background .3s,color .3s}
html[lang="ar"] body,html[lang="ar"] button,html[lang="ar"] input,html[lang="ar"] textarea{font-family:'IBM Plex Sans Arabic',sans-serif}
button{cursor:pointer;font:inherit;border:none;background:none;color:inherit}
input,textarea,select{font:inherit;outline:none}
svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}

/* Panel */
.glass-panel{width:min(100%,440px);height:min(760px,calc(100vh - 24px));min-height:600px;border:1px solid var(--border);border-radius:20px;background:var(--panel);backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);box-shadow:var(--shadow);overflow:hidden;display:flex;flex-direction:column;position:relative}

/* Header */
header{padding:14px 18px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border);background:rgba(0,0,0,.1)}
.brand{font-weight:800;font-size:15px;background:var(--grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.header-user{display:flex;align-items:center;gap:8px;padding:4px 10px 4px 4px;background:var(--surface);border-radius:20px;font-size:11px;font-weight:600}

/* Main */
main{flex:1;overflow:auto;padding:14px;scrollbar-width:thin;scrollbar-color:var(--muted) transparent}
main::-webkit-scrollbar{width:5px}main::-webkit-scrollbar-thumb{background:var(--muted);border-radius:3px}

/* Nav */
nav{display:flex;justify-content:space-around;border-top:1px solid var(--border);padding:6px 4px calc(6px + env(safe-area-inset-bottom));background:rgba(0,0,0,.15)}
nav button{display:grid;gap:4px;justify-items:center;font-size:10px;color:var(--muted);padding:6px 10px;border-radius:12px;transition:all .2s;position:relative}
nav button.active{color:var(--text)}
nav button.active::after{content:'';position:absolute;bottom:0;left:50%;transform:translateX(-50%);width:16px;height:3px;background:var(--grad);border-radius:3px}

/* Buttons */
.btn-primary{background:var(--grad);color:#fff;border-radius:12px;padding:11px 16px;font-weight:700;font-size:12px;transition:transform .15s,box-shadow .2s;box-shadow:0 4px 15px rgba(139,92,246,.3)}
.btn-primary:active{transform:scale(.96)}
.btn-secondary{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:10px 14px;font-weight:600;font-size:12px;transition:background .15s}
.btn-secondary:active{background:rgba(255,255,255,.1)}
.btn-danger{background:var(--danger);color:#fff;border-radius:12px;padding:10px 14px;font-weight:600;font-size:12px}

/* Inputs */
.input-field{width:100%;background:var(--surface);color:var(--text);border:1.5px solid var(--border);border-radius:12px;padding:12px 14px;font-size:13px;transition:border-color .2s,box-shadow .2s}
.input-field:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(139,92,246,.15)}
label{display:block;margin:12px 0 6px;color:var(--muted);font-size:11px;font-weight:600}

/* Card */
.card{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:14px;margin:8px 0;transition:transform .2s,box-shadow .2s}
.card:hover{transform:translateY(-1px);box-shadow:0 6px 20px rgba(0,0,0,.15)}
.row{display:flex;gap:10px;align-items:center}
.row>*{flex:1}
.stack{display:grid;gap:8px}
.center{text-align:center}
.small,.muted{font-size:11px;color:var(--muted)}
.hidden{display:none!important}

/* Avatar */
.avatar{width:38px;height:38px;border-radius:50%;display:grid;place-items:center;background:var(--grad);color:#fff;font-weight:800;overflow:hidden;flex:none;font-size:14px}
.avatar img{width:100%;height:100%;object-fit:cover}

/* Badge */
.badge{display:inline-flex;vertical-align:middle;margin-inline-start:4px}
.badge svg{width:14px;height:14px}
.badge.vip svg{fill:#06b6d4;stroke:#06b6d4;filter:drop-shadow(0 0 4px rgba(6,182,212,.6))}
.badge.admin svg{fill:#f59e0b;stroke:#f59e0b;filter:drop-shadow(0 0 4px rgba(245,158,11,.6))}

/* Tabs */
.tabs{display:flex;gap:6px;margin:14px 0;background:var(--surface);padding:4px;border-radius:14px;border:1px solid var(--border)}
.tabs button{flex:1;padding:9px;border-radius:10px;font-size:12px;font-weight:600;color:var(--muted);transition:all .2s}
.tabs button.active{background:var(--grad);color:#fff;box-shadow:0 3px 12px rgba(139,92,246,.3)}

/* Chat */
.chatlog{height:360px;overflow-y:auto;display:flex;flex-direction:column;gap:10px;padding:10px 6px;scroll-behavior:smooth}
.chatlog::-webkit-scrollbar{width:3px}.chatlog::-webkit-scrollbar-thumb{background:var(--muted);border-radius:2px}
.bubble-wrap{display:flex;gap:8px;align-items:flex-end;max-width:90%}
.bubble-wrap.me{margin-inline-start:auto;flex-direction:row-reverse}
.bubble-avatar{width:26px;height:26px;border-radius:50%;display:grid;place-items:center;font-size:10px;font-weight:800;flex-shrink:0}
.bubble-wrap.bot .bubble-avatar{background:var(--grad);color:#fff}
.bubble-wrap.me .bubble-avatar{background:var(--surface);border:1px solid var(--border)}
.bubble{padding:10px 14px;border-radius:16px;line-height:1.6;font-size:12px;overflow-wrap:anywhere;white-space:pre-wrap;animation:bubbleIn .25s ease-out}
@keyframes bubbleIn{from{opacity:0;transform:translateY(8px) scale(.95)}to{opacity:1;transform:translateY(0) scale(1)}}
.bubble-wrap.bot .bubble{background:var(--surface);border:1px solid var(--border);border-bottom-inline-start-radius:4px}
.bubble-wrap.me .bubble{background:var(--grad);color:#fff;border-bottom-inline-end-radius:4px}
.bubble.typing{display:flex;gap:3px;padding:12px 16px}
.typing-dot{width:6px;height:6px;border-radius:50%;background:var(--muted);animation:dotBounce 1.4s infinite}
.typing-dot:nth-child(2){animation-delay:.2s}.typing-dot:nth-child(3){animation-delay:.4s}
@keyframes dotBounce{0%,60%,100%{transform:translateY(0);opacity:.4}30%{transform:translateY(-6px);opacity:1}}
.bubble-time{font-size:9px;color:var(--muted);margin-top:3px;text-align:center;opacity:.7}

/* Chat Input */
.chat-input-area{display:flex;gap:8px;padding:12px 4px 4px}
.chat-input-area input{flex:1;background:var(--surface);border:1.5px solid var(--border);color:var(--text);border-radius:16px;padding:12px 16px;font-size:13px;transition:border-color .2s}
.chat-input-area input:focus{border-color:var(--accent)}
.send-btn{width:44px;height:44px;border-radius:50%;background:var(--grad);color:#fff;display:grid;place-items:center;flex-shrink:0;box-shadow:0 4px 15px rgba(139,92,246,.3);transition:transform .15s}
.send-btn:active{transform:scale(.9)}

/* Typing Area */
.typing-card{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:16px;margin:12px 0;animation:bubbleIn .3s}
.typing-target{font-size:15px;line-height:2.2;user-select:none;margin-bottom:12px;font-weight:500}
.typing-target span.correct{color:var(--success)}
.typing-target span.wrong{color:var(--danger);background:rgba(239,68,68,.15);border-radius:3px}
.typing-target span.current{border-bottom:2px solid var(--accent);animation:blink 1s infinite}
@keyframes blink{50%{border-bottom-color:transparent}}
.progress-bar{height:6px;background:var(--surface);border-radius:99px;overflow:hidden;margin-bottom:12px}
.progress-fill{height:100%;background:var(--grad);width:0;transition:width .2s;border-radius:99px}
.live-stats{display:flex;justify-content:space-around;margin-top:12px;padding-top:12px;border-top:1px solid var(--border)}
.stat-item{text-align:center}
.stat-value{font-size:18px;font-weight:800;background:var(--grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.stat-label{font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px}

/* Leaderboard */
.rank-item{display:flex;align-items:center;gap:12px;padding:12px;background:var(--surface);border:1px solid var(--border);border-radius:14px;margin-bottom:8px;transition:transform .2s}
.rank-item:hover{transform:translateX(4px)}
.rank-num{font-weight:800;font-size:14px;color:var(--muted);width:24px}
.rank-item.top-1 .rank-num{color:#f59e0b;font-size:18px}
.rank-item.top-2 .rank-num{color:#94a3b8;font-size:16px}
.rank-item.top-3 .rank-num{color:#b45309;font-size:16px}

/* Toast */
#toast-container{position:fixed;top:20px;left:50%;transform:translateX(-50%);z-index:9999;display:flex;flex-direction:column;gap:8px;pointer-events:none}
.toast{padding:12px 20px;background:var(--panel);backdrop-filter:blur(20px);border:1px solid var(--border);border-radius:12px;font-size:12px;font-weight:600;box-shadow:var(--shadow);animation:toastIn .3s;display:flex;gap:8px;align-items:center;min-width:200px}
.toast.success{border-color:var(--success)}.toast.error{border-color:var(--danger)}.toast.info{border-color:var(--accent)}
@keyframes toastIn{from{transform:translateY(-20px);opacity:0}to{transform:translateY(0);opacity:1}}

/* Modal */
.modal-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.7);backdrop-filter:blur(8px);display:grid;place-items:center;padding:16px;z-index:100;animation:fadeIn .2s}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
.modal{width:min(100%,400px);max-height:90vh;overflow:auto;background:var(--panel);backdrop-filter:blur(24px);border:1px solid var(--border);border-radius:20px;padding:20px;box-shadow:var(--shadow);animation:modalIn .3s cubic-bezier(.34,1.56,.64,1)}
@keyframes modalIn{from{transform:scale(.9);opacity:0}to{transform:scale(1);opacity:1}}
.modal-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.modal-head h3{font-size:16px;font-weight:800}
.modal-head button{font-size:24px;color:var(--muted);line-height:1}

/* List */
.list-item{display:flex;gap:10px;align-items:center;justify-content:space-between;padding:10px;background:var(--surface);border:1px solid var(--border);border-radius:12px;margin-bottom:8px}
.person{display:flex;gap:10px;align-items:center;cursor:pointer;min-width:0;flex:1}
.person-info{min-width:0}
.person-name{font-weight:700;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.person-handle{font-size:10px;color:var(--muted)}

/* Social Links */
.social{display:inline-flex;align-items:center;gap:5px;text-decoration:none;margin:4px 4px 4px 0;padding:6px 12px;background:var(--surface);border-radius:8px;color:var(--text);font-size:11px;font-weight:600;border:1px solid var(--border);transition:all .2s}
.social:hover{transform:translateY(-1px)}
.social.instagram{color:#ec67a8;border-color:#ec67a844}
.social.snapchat{color:#f4dd42;border-color:#f4dd4244}

/* VIP */
.vip-card{background:linear-gradient(135deg,rgba(139,92,246,.15),rgba(6,182,212,.15));border:1.5px solid var(--accent);border-radius:16px;padding:16px;margin-bottom:12px}
.vip-plan{padding:14px;background:var(--surface);border:1.5px solid var(--border);border-radius:12px;margin-bottom:8px;cursor:pointer;transition:all .2s;display:flex;justify-content:space-between;align-items:center}
.vip-plan:hover{border-color:var(--accent);transform:translateY(-2px)}
.vip-plan.featured{border-color:var(--accent);position:relative}

/* Spinner */
.spinner{width:32px;height:32px;border:3px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .8s linear infinite;margin:24px auto}
@keyframes spin{to{transform:rotate(360deg)}}

/* Search */
.search-bar{position:relative;margin-bottom:12px}
.search-bar input{width:100%;background:var(--surface);border:1.5px solid var(--border);color:var(--text);border-radius:14px;padding:12px 16px;font-size:13px}
.search-bar input:focus{border-color:var(--accent)}

hr{border:0;border-top:1px solid var(--border);margin:14px 0}

/* Welcome screen */
.welcome-container{padding:40px 20px;text-align:center;animation:fadeIn .5s}
.welcome-logo{width:80px;height:80px;border-radius:24px;background:var(--grad);margin:0 auto 20px;display:grid;place-items:center;box-shadow:0 10px 40px rgba(139,92,246,.4)}
.welcome-logo svg{width:40px;height:40px;stroke:#fff;stroke-width:2}
.welcome-title{font-size:26px;font-weight:800;background:var(--grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:8px}
.welcome-subtitle{color:var(--muted);font-size:13px;margin-bottom:32px}
</style>
</head>
<body>

<div id="toast-container"></div>

<div class="glass-panel">
<header>
  <div class="brand">Typing Master Pro</div>
  <div class="header-user" id="headerUser"></div>
</header>
<main id="app"></main>
<nav id="nav" class="hidden">
  <button data-page="bot" class="active"><svg viewBox="0 0 24 24"><rect x="3" y="8" width="18" height="13" rx="3"/><path d="M12 8V4m-4 4a4 4 0 0 1 8 0"/><circle cx="8.5" cy="14" r="1.2" fill="currentColor"/><circle cx="15.5" cy="14" r="1.2" fill="currentColor"/></svg><span data-i="practice">تدريب</span></button>
  <button data-page="leaderboard"><svg viewBox="0 0 24 24"><path d="M8 21h8m-4-4v4M7 4h10v5a5 5 0 0 1-10 0V4Z"/><path d="M7 6H4v2a4 4 0 0 0 4 4m9-6h3v2a4 4 0 0 1-4 4"/></svg><span data-i="leaderboard">المتصدرون</span></button>
  <button data-page="community"><svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3"/><path d="M3 20v-2a6 6 0 0 1 12 0v2m2-9a3 3 0 1 0 0-6m4 15v-2a6 6 0 0 0-4-5.7"/></svg><span data-i="community">المجتمع</span></button>
  <button data-page="settings"><svg viewBox="0 0 24 24"><path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z"/><path d="m19.4 15 .1.1 1.4 1.1-1.5 2.6-1.7-.7a8 8 0 0 1-1.5.9l-.3 1.8h-3l-.3-1.8a8 8 0 0 1-1.5-.9l-1.7.7-1.5-2.6 1.4-1.1a7 7 0 0 1 0-1.8l-1.4-1.1 1.5-2.6 1.7.7a8 8 0 0 1 1.5-.9l.3-1.8h3l.3 1.8a8 8 0 0 1 1.5.9l1.7-.7 1.5 2.6-1.4 1.1a7 7 0 0 1 0 1.7Z"/></svg><span data-i="settings">الإعدادات</span></button>
</nav>
</div>
<div id="modalRoot"></div>

<script>
"use strict";
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const get=(k,d)=>{try{return JSON.parse(localStorage.getItem(k))??d}catch{return d}};
const set=(k,v)=>localStorage.setItem(k,JSON.stringify(v));

const dict={
ar:{practice:"تدريب",leaderboard:"المتصدرون",community:"المجتمع",settings:"الإعدادات",login:"دخول",register:"إنشاء حساب",welcome:"اختبر سرعتك، حسّن دقتك، وتنافس مع الأصدقاء",username:"اسم المستخدم",password:"كلمة المرور",send:"إرسال",save:"حفظ",cancel:"إلغاء",bio:"نبذة",nickname:"الاسم الظاهر",search:"ابحث عن مستخدم...",vip:"ترقية VIP",support:"الدعم الفني",logout:"تسجيل الخروج",score:"النقطة",noUsers:"لا يوجد مستخدمون بعد",typeHere:"اكتب هنا...",profile:"الملف الشخصي",edit:"تعديل الملف",monthly:"شهري",yearly:"سنوي",lifetime:"مدى الحياة",pay:"ادفع",admin:"لوحة الأدمن",theme:"الثيم",language:"اللغة",friends:"إضافة صديق",message:"مراسلة",upgrade:"ترقية الآن",wpm:"كلمة/د",accuracy:"دقة",tests:"اختبارات",best:"أفضل سرعة",retry:"حاول مرة أخرى",newText:"نص جديد",perfect:"ممتاز!",great:"رائع!",good:"جيد!",keepGoing:"استمر!",online:"متصل",offline:"غير متصل"},
en:{practice:"Practice",leaderboard:"Leaderboard",community:"Community",settings:"Settings",login:"Login",register:"Register",welcome:"Test your speed, improve accuracy, compete with friends",username:"Username",password:"Password",send:"Send",save:"Save",cancel:"Cancel",bio:"Bio",nickname:"Nickname",search:"Search users...",vip:"Upgrade VIP",support:"Support",logout:"Log out",score:"Points",noUsers:"No users yet",typeHere:"Type here...",profile:"Profile",edit:"Edit profile",monthly:"Monthly",yearly:"Yearly",lifetime:"Lifetime",pay:"Pay",admin:"Admin panel",theme:"Theme",language:"Language",friends:"Add friend",message:"Message",upgrade:"Upgrade now",wpm:"WPM",accuracy:"Accuracy",tests:"Tests",best:"Best Speed",retry:"Try Again",newText:"New Text",perfect:"Perfect!",great:"Great!",good:"Good!",keepGoing:"Keep going!",online:"Online",offline:"Offline"}
};

let lang=localStorage.getItem("typing_lang")||"ar";
let users=get("all_users",[]),current=get("typing_user",null),chats=get("chats",{}),support=get("support_messages",[]);
let page="bot",flow="",activeTarget=null,typingState=null;
const t=k=>dict[lang][k]||k;
const esc=s=>String(s||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const nowTime=()=>new Date().toLocaleTimeString(lang==='ar'?'ar-SA':'en-US',{hour:'2-digit',minute:'2-digit'});

function persist(){set("all_users",users);set("typing_user",current);set("chats",chats);set("support_messages",support)}

function toast(msg,type='info'){
  const c=$("#toast-container");const el=document.createElement("div");
  el.className=`toast ${type}`;el.textContent=msg;c.appendChild(el);
  setTimeout(()=>{el.style.animation='toastIn .3s reverse';setTimeout(()=>el.remove(),300)},2500);
}

function avatar(u,size=""){
  return `<div class="avatar ${size}">${u&&u.photo?`<img src="${u.photo}" alt="">`:esc((u&&u.avatar)||"?")}</div>`;
}

function badge(u){
  if(u?.role==="admin") return `<span class="badge admin" title="Admin"><svg viewBox="0 0 24 24"><path d="m12 2 3 6.5 7 1-5 5 1.2 7L12 18l-6.2 3.5L7 14.5l-5-5 7-1L12 2Z"/></svg></span>`;
  if(u?.vip) return `<span class="badge vip" title="VIP"><svg viewBox="0 0 24 24"><path d="M12 3 20 6v5c0 5-3.4 8.3-8 10-4.6-1.7-8-5-8-10V6l8-3Z"/><path d="m8 12 2.5 2.5L16 9"/></svg></span>`;
  return "";
}

function render(){
  document.documentElement.lang=lang;
  document.documentElement.dir=lang==="ar"?"rtl":"ltr";
  document.documentElement.dataset.theme=localStorage.getItem("typing_theme")||"Dark";
  $("#nav").classList.toggle("hidden",!current);
  $("#headerUser").innerHTML=current?`${avatar(current)}<span>${esc(current.nickname||current.name)} ${badge(current)}</span>`:"";
  if(!current){renderWelcome();return}
  if(page==="bot")renderBot();
  else if(page==="leaderboard")renderLeaderboard();
  else if(page==="community")renderCommunity();
  else renderSettings();
  $$("#nav button").forEach(b=>b.classList.toggle("active",b.dataset.page===page));
  $$("#nav [data-i]").forEach(x=>x.textContent=t(x.dataset.i));
}

/* --- WELCOME --- */
function renderWelcome(){
  $("#app").innerHTML=`
  <div class="welcome-container">
    <div class="welcome-logo"><svg viewBox="0 0 24 24"><path d="M6 9h12M6 15h8M7 3h10a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/></svg></div>
    <div class="welcome-title">Typing Master Pro</div>
    <div class="welcome-subtitle">${t("welcome")}</div>
    <div class="tabs">
      <button class="active" onclick="authForm('login',this)">${t("login")}</button>
      <button onclick="authForm('register',this)">${t("register")}</button>
    </div>
    <div id="authForm"></div>
  </div>`;
  authForm('login');
}

function authForm(mode,btn){
  $$(".tabs button").forEach(b=>b.classList.remove("active"));
  if(btn)btn.classList.add("active");
  $("#authForm").innerHTML=`
  <div class="card">
    <label>${t("username")}</label>
    <input id="authName" class="input-field" autocomplete="username" placeholder="@username">
    <label>${t("password")}</label>
    <input id="authPass" class="input-field" type="password" autocomplete="${mode==="login"?"current-password":"new-password"}" placeholder="••••••••">
    ${mode==="register"?`<label>Avatar</label><div class="row"><select id="authAvatar" class="input-field"><option value="A">A</option><option value="B">B</option><option value="C">C</option><option value="D">D</option></select><input id="authPhoto" type="file" accept="image/*" class="input-field"></div>`:""}
    <p id="authError" class="small" style="color:var(--danger);min-height:16px"></p>
    <button class="btn-primary" style="width:100%" onclick="submitAuth('${mode}')">${t(mode)}</button>
  </div>`;
}

function submitAuth(mode){
  const name=$("#authName").value.trim(),pass=$("#authPass").value;
  if(!name||!pass){$("#authError").textContent=lang==='ar'?"أدخل الاسم وكلمة المرور":"Enter name and password";return}
  if(mode==="register"){
    if(users.some(u=>u.name.toLowerCase()===name.toLowerCase())){$("#authError").textContent=lang==='ar'?"اسم المستخدم مستخدم مسبقاً":"Username already taken";return}
    const photoFile=$("#authPhoto")?.files[0];
    const finish=photo=>{
      current={id:crypto.randomUUID(),name,pass,avatar:$("#authAvatar").value,photo,nickname:name,bio:"",instagram:"",snapchat:"",score:0,role:"user",vip:false,friends:[],best:0,totalTests:0};
      users.push(current);persist();toast(lang==='ar'?"تم إنشاء الحساب":"Account created",'success');render();
    };
    if(photoFile){const r=new FileReader();r.onload=()=>finish(r.result);r.readAsDataURL(photoFile)}else finish("");
  }else{
    if(name==="bos"&&pass==="Bader@12"){
      current={id:"superadmin",name,pass,avatar:"B",nickname:"Boss Admin",bio:"Super Admin",score:99999,role:"admin",vip:true,friends:[]};
      persist();toast(lang==='ar'?"مرحباً بك أيها المدير":"Welcome Admin",'success');render();return;
    }
    const u=users.find(x=>x.name.toLowerCase()===name.toLowerCase()&&x.pass===pass);
    if(!u){$("#authError").textContent=lang==='ar'?"بيانات الدخول غير صحيحة":"Invalid credentials";return}
    current=u;persist();toast(lang==='ar'?"مرحباً بعودتك!":"Welcome back!",'success');render();
  }
}

/* --- DATA ENGINE --- */
const sentences={
ar:["القراءة تفتح أبواباً جديدة للفكر","التدريب اليومي يصنع فرقاً كبيراً","الوقت مناسب لتعلم مهارة مفيدة","النجاح يبدأ بخطوة صغيرة","الهدوء يساعد على التركيز","كل محاولة تقربك من هدفك","الكتابة السريعة تحتاج إلى ممارسة","التعلم رحلة مستمرة وممتعة","الصبر مفتاح إتقان المهارات","الأفكار الجميلة تحتاج إلى عمل","نظم وقتك لتحقق أهدافك","المعرفة قوة تبني المستقبل","الإنجاز يبدأ بالتخطيط الجيد","اللغة جسر للتواصل بين الناس","العمل المتقن يعكس شخصية صاحبه","التفاؤل يمنح اليوم بداية رائعة","التركيز يحسن جودة العمل","كل يوم يحمل فرصة جديدة","القرارات الصغيرة تصنع نتائج كبيرة","النجاح يحتاج إلى عزيمة وصبر","الابتكار يبدأ بسؤال مختلف","التعاون يجعل المهام أسهل","الاستراحة القصيرة تجدد النشاط","الاستمرار أهم من السرعة","الكتابة الواضحة تسهل الفهم","التجربة تعلمنا طرقاً جديدة","الهدف الواضح يقود إلى التقدم","العادات الجيدة تصنع حياة أفضل","ابدأ الآن ولا تنتظر الوقت المثالي","التوازن أساس يوم منتج"],
en:["Reading opens new doors for the mind","Daily practice makes a real difference","Now is a good time to learn a useful skill","Success begins with a small step","A calm mind helps you focus","Every attempt brings you closer to your goal","Fast typing takes regular practice","Learning is a continuous journey","Patience is the key to mastering skills","Good ideas need thoughtful work","Plan your time to reach your goals","Knowledge helps build the future","Progress begins with a clear plan","Language connects people across the world","Careful work reflects its creator","Optimism gives the day a bright start","Focus improves the quality of work","Every day brings a new opportunity","Small choices can create big results","Success takes patience and determination","Innovation begins with a different question","Working together makes tasks easier","A short break can renew your energy","Consistency matters more than speed","Clear writing makes ideas easier to understand","Experience teaches us new approaches","A clear goal helps you move forward","Good habits can shape a better life","Start now instead of waiting for perfect timing","Balance is the foundation of a productive day"]
};

const words={
ar:"بيت كتاب شمس قمر طريق نافذة حديقة مدرسة قلم مدينة بحر سيارة زهرة طاولة هاتف حاسوب وقت حلم نجاح صديق ماء شجرة باب غرفة طعام سفر مطر سحابة جبل نهر نجمة صباح مساء عائلة موسيقى فكرة لعبة عمل ذاكرة لغة صوت لون قصة دفتر حقيبة مفتاح كرسي ساعة خبز تفاح قهوة وردة طائر سمكة طفل معلم طبيب سوق قرية قطار طائرة سفينة طاقة رياضة صحة مهارة علم فن صبر أمل فرح سلام ضوء حجر رمل ثلج نار هواء وطن رسالة صورة شاشة لوحة حروف سرعة دقة تدريب هدف عادة اختيار ابتكار تعاون معرفة راحة".split(" "),
en:"house book sun moon road window garden school pen city sea car flower table phone computer time dream success friend water tree door room food travel rain cloud mountain river star morning evening family music idea game work memory language sound color story notebook bag key chair clock bread apple coffee bird fish child teacher doctor market village train plane ship energy sport health skill science art patience hope joy peace light stone sand snow fire air letter picture screen keyboard typing speed accuracy practice goal habit choice invention teamwork knowledge rest".split(" ")
};

const places={ar:["مدينة هادئة","قرية بعيدة","جزيرة صغيرة","حي قديم","غابة واسعة","ميناء جميل","مدرسة قريبة","سوق مزدحم","وادي أخضر","محطة قطار"],en:["a quiet city","a distant village","a small island","an old neighborhood","a wide forest","a lovely harbor","a nearby school","a busy market","a green valley","a train station"]};
const characters={ar:["كاتب شاب","مسافرة فضولية","طفل شجاع","عالم حكيم","فنان موهوب","معلمة محبة","مخترع صغير","بحار هادئ","طبيبة مجتهدة","موسيقي غامض"],en:["a young writer","a curious traveler","a brave child","a wise scientist","a talented artist","a caring teacher","a young inventor","a calm sailor","a dedicated doctor","a mysterious musician"]};
const events={ar:["اكتشاف مكان جديد","تعلم لغة مختلفة","إنقاذ حديقة جميلة","كتابة قصة ملهمة","بناء آلة ذكية","مساعدة صديق قديم","رسم خريطة غامضة","إقامة مهرجان كبير","حل لغز صعب","بدء مشروع مفيد"],en:["discovering a new place","learning a different language","saving a lovely garden","writing an inspiring story","building a clever machine","helping an old friend","drawing a mysterious map","hosting a grand festival","solving a difficult puzzle","starting a useful project"]};
const surprises={ar:["وصلت رسالة تحمل خبراً سعيداً","ظهر طريق لم يره أحد من قبل","اجتمع الأصدقاء لتقديم المساعدة","وجد خريطة مخبأة تحت شجرة","بدأ المطر يرسم ألواناً على النوافذ","اكتشف الجميع أن الحلم قريب","سمعوا لحناً يقودهم إلى الحل","تعاون أهل المكان لتحقيق الهدف"],en:["a letter arrived with joyful news","a path appeared where none had been seen","friends gathered to offer their help","a hidden map was found beneath a tree","rain painted colors across the windows","everyone discovered the dream was near","a melody led them toward the answer","the community joined forces to reach the goal"]};
const newsBits={ar:["افتتاح مركز جديد للتعلم","إطلاق مبادرة لدعم القراءة","فريق محلي يحقق إنجازاً مميزاً","باحثون يعلنون اكتشافاً مهماً","حديقة عامة تستقبل زوارها","طلاب يبتكرون مشروعاً تقنياً","مهرجان ثقافي يجمع العائلات","تطوير خدمة النقل في المدينة","مكتبة توسع أبوابها للقراء","حملة تطوعية لتنظيف الشاطئ"],en:["a new learning center opens","a reading support initiative launches","a local team reaches a milestone","researchers announce an important discovery","a public garden welcomes visitors","students create a technology project","a cultural festival brings families together","city transport service gets an upgrade","a library expands its reading space","volunteers organize a beach cleanup"]};

const pick=a=>a[Math.floor(Math.random()*a.length)];
const genSentences=(level,count=100)=>{const a=sentences[lang];return Array.from({length:count},()=>pick(a)+". "+pick(a)+(level==="hard"?" — "+pick(a):"."));};
const genStories=(level,count=100)=>{const p=places[lang],c=characters[lang],e=events[lang],s=surprises[lang];return Array.from({length:count},()=>lang==="ar"?`في ${pick(p)}، عاش ${pick(c)} يحلم بـ ${pick(e)}. وفي يوم من الأيام، ${pick(s)}.`:`In ${pick(p)}, ${pick(c)} dreamed of ${pick(e)}. One day, ${pick(s)}.`);};
const genNews=(count=100)=>Array.from({length:count},()=>pick(newsBits[lang])+". "+pick(newsBits[lang])+". "+pick(newsBits[lang])+".");

/* --- CHAT HELPERS --- */
function bubbleHTML(text,who='bot'){
  const u=who==='me'?current:{avatar:'B',name:'Bot'};
  return `<div class="bubble-wrap ${who}"><div class="bubble-avatar">${who==='me'?esc((u.avatar||'?')):'B'}</div><div><div class="bubble">${esc(text)}</div><div class="bubble-time">${nowTime()}</div></div></div>`;
}

function say(text,who="bot"){
  const log=$("#chatlog");if(!log)return;
  log.insertAdjacentHTML('beforeend',bubbleHTML(text,who));
  log.scrollTop=log.scrollHeight;
}

function botReply(text,fn){
  const log=$("#chatlog");if(!log)return;
  const id='typing_'+Date.now();
  log.insertAdjacentHTML('beforeend',`<div class="bubble-wrap bot" id="${id}"><div class="bubble-avatar">B</div><div class="bubble typing"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div></div>`);
  log.scrollTop=log.scrollHeight;
  setTimeout(()=>{const el=document.getElementById(id);if(el)el.remove();say(text);if(fn)fn()},700);
}

/* --- BOT --- */
function renderBot(){
  $("#app").innerHTML=`
  <div class="row" style="margin-bottom:8px">
    <div><h3 style="font-size:15px">Typing Bot</h3><div class="muted">${lang==='ar'?'اكتب أمراً لبدء التدريب':'Type a command to start'}</div></div>
    <button class="btn-secondary" style="flex:0 0 auto" onclick="resetBot()">${lang==='ar'?'جديد':'New'}</button>
  </div>
  <div id="chatlog" class="chatlog card" style="padding:8px"></div>
  <div class="chat-input-area">
    <input id="botInput" placeholder="${t("typeHere")}" onkeydown="if(event.key==='Enter')sendBot()">
    <button class="send-btn" onclick="sendBot()"><svg viewBox="0 0 24 24"><path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7Z"/></svg></button>
  </div>
  <div id="typingArea"></div>`;
  botReply(lang==='ar'?"مرحباً! اكتب:\n• جمل\n• سوالف\n• جريدة\n• تكرار\n\nأو اكتب الأمرين معاً (مثل: جمل سهل)":"Hi! Type:\n• sentences\n• stories\n• newspaper\n• repeat\n\nOr combine (e.g., sentences easy)");
}

function resetBot(){flow="";typingState=null;renderBot()}

function sendBot(){
  const input=$("#botInput"),v=input.value.trim();if(!v)return;
  input.value="";say(v,"me");
  if(typingState){checkTyping(v);return}
  const cmd=v.toLowerCase();
  
  // Quick combined command
  const modeMatch=cmd.match(/(جمل|سوالف|جريدة|تكرار|sentences|stories|newspaper|repeat)/);
  const diffMatch=cmd.match(/(سهل|متوسط|صعب|easy|medium|hard)/);
  
  if(modeMatch&&diffMatch&&!flow){
    const m=modeMatch[1],d=diffMatch[1];
    const mode=m.includes("جمل")||m==="sentences"?"sentences":m.includes("سوالف")||m==="stories"?"stories":m.includes("جريدة")||m==="newspaper"?"news":"repeat";
    if(mode!=="repeat"){
      flow=mode;
      const level=(d==="سهل"||d==="easy")?"easy":(d==="صعب"||d==="hard")?"hard":"medium";
      const arr=flow==="sentences"?genSentences(level):flow==="stories"?genStories(level):genNews();
      botReply(lang==='ar'?`جاري التجهيز...`:"Preparing...",()=>startCountdown(()=>startTyping(pick(arr))));
      return;
    }
  }
  
  if(["جمل","sentences","سوالف","stories","جريدة","newspaper"].includes(cmd)){
    flow=cmd.includes("جمل")||cmd==="sentences"?"sentences":cmd.includes("سوالف")||cmd==="stories"?"stories":"news";
    botReply(t("difficulty"));return;
  }
  if(["سهل","متوسط","صعب","easy","medium","hard"].includes(cmd)&&flow){
    const level=(cmd==="سهل"||cmd==="easy")?"easy":(cmd==="صعب"||cmd==="hard")?"hard":"medium";
    const arr=flow==="sentences"?genSentences(level):flow==="stories"?genStories(level):genNews();
    botReply(lang==='ar'?"استعد...":"Get ready...",()=>startCountdown(()=>startTyping(pick(arr))));return;
  }
  if(["تكرار","repeat"].includes(cmd)){flow="repeat";botReply(t("repeatCount"));return}
  if(flow==="repeat"&&/^\d+$/.test(cmd)){
    const n=Math.max(1,Math.min(10,Number(cmd))),vocab=words[lang],items=[];
    for(let i=0;i<n;i++){const w=pick(vocab),times=1+Math.floor(Math.random()*4);items.push(`${w} (${times})`)}
    const target=items.map(x=>{const m=x.match(/^(.*) \((\d)\)$/);return Array(Number(m[2])).fill(m[1]).join(" ")}).join(" ");
    botReply(items.join("   •   "),()=>startCountdown(()=>startTyping(target)));flow="";return;
  }
  botReply(lang==='ar'?"لم أفهم الأمر. جرّب: جمل، سوالف، جريدة، أو تكرار.":"Unknown command. Try: sentences, stories, newspaper, or repeat.");
}

function startCountdown(done){
  let n=3;const tick=()=>{
    if(n>0){say(String(n));setTimeout(tick,650)}
    else{say(lang==='ar'?"انطلق!":"Go!");done()}
  };tick();
}

function startTyping(text){
  typingState={text,started:Date.now(),typed:"",correct:0,errors:0};
  $("#typingArea").innerHTML=`
  <div class="typing-card">
    <div class="typing-target" id="typingTarget"></div>
    <div class="progress-bar"><div class="progress-fill" id="typeProgress"></div></div>
    <input id="typeInput" class="input-field" autocomplete="off" placeholder="${t("typeHere")}" oninput="typingInput()">
    <div class="live-stats">
      <div class="stat-item"><div class="stat-value" id="liveWpm">0</div><div class="stat-label">WPM</div></div>
      <div class="stat-item"><div class="stat-value" id="liveAcc">100%</div><div class="stat-label">${t("accuracy")}</div></div>
      <div class="stat-item"><div class="stat-value" id="liveChars">0</div><div class="stat-label">Chars</div></div>
    </div>
  </div>`;
  paintTarget();
  $("#typeInput").focus();
}

function paintTarget(){
  if(!typingState)return;
  const {text,typed}=typingState;
  $("#typingTarget").innerHTML=[...text].map((c,i)=>{
    const cls=i<typed.length?(typed[i]===c?"correct":"wrong"):i===typed.length?"current":"";
    return `<span class="${cls}">${c===" "?"&nbsp;":esc(c)}</span>`;
  }).join("");
  $("#typeProgress").style.width=Math.min(100,typed.length/text.length*100)+"%";
}

function typingInput(){
  if(!typingState)return;
  const val=$("#typeInput").value;typingState.typed=val;
  typingState.correct=0;typingState.errors=0;
  for(let i=0;i<val.length;i++){if(val[i]===typingState.text[i])typingState.correct++;else typingState.errors++}
  const elapsed=(Date.now()-typingState.started)/60000;
  const wpm=Math.round((typingState.correct/5)/Math.max(elapsed,.01));
  const acc=val.length?Math.round(typingState.correct/val.length*100):100;
  $("#liveWpm").textContent=wpm;
  $("#liveAcc").textContent=acc+"%";
  $("#liveChars").textContent=val.length;
  paintTarget();
  if(val.length>=typingState.text.length)finishTyping();
}

function checkTyping(v){if(typingState){$("#typeInput").value=v;typingInput()}}

function finishTyping(){
  const s=typingState;if(!s)return;
  const minutes=Math.max((Date.now()-s.started)/60000,.01);
  const wpm=Math.round((s.text.length/5)/minutes);
  const accuracy=Math.round(s.correct/Math.max(s.typed.length,1)*100);
  const points=Math.max(0,s.correct*10-s.errors*2);
  
  current.score=(current.score||0)+points;
  current.totalTests=(current.totalTests||0)+1;
  current.best=Math.max(current.best||0,wpm);
  users=users.map(u=>u.id===current.id?current:u);
  persist();
  
  typingState=null;
  const rating=accuracy>=95&&wpm>=40?'perfect':accuracy>=85?'great':accuracy>=70?'good':'keepGoing';
  const ratingMsg=t(rating);
  
  $("#typingArea").innerHTML=`
  <div class="typing-card" style="text-align:center">
    <div style="font-size:32px;font-weight:800;background:var(--grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:4px">${wpm}</div>
    <div class="muted" style="margin-bottom:16px">WPM · ${ratingMsg}</div>
    <div class="row" style="margin-bottom:14px">
      <div><div class="stat-value">${accuracy}%</div><div class="stat-label">${t("accuracy")}</div></div>
      <div><div class="stat-value">+${points}</div><div class="stat-label">${t("score")}</div></div>
      <div><div class="stat-value">${s.errors}</div><div class="stat-label">Errors</div></div>
    </div>
    <button class="btn-primary" style="width:100%" onclick="startTyping('${s.text.replace(/'/g,"\\'")}');typingState.started=Date.now();">${t("retry")}</button>
  </div>`;
  toast(`+${points} ${t("score")} · ${wpm} WPM`,'success');
}

/* --- LEADERBOARD --- */
function renderLeaderboard(){
  const sorted=[...users].filter(u=>u.role!=='admin').sort((a,b)=>(b.score||0)-(a.score||0));
  $("#app").innerHTML=`<h3 style="font-size:16px;margin-bottom:12px">${t("leaderboard")}</h3>
  ${sorted.length?sorted.map((u,i)=>{
    const rank=i+1,cls=rank<=3?`top-${rank}`:'';
    return `<div class="rank-item ${cls}" onclick="viewProfile('${u.id}')">
      <div class="rank-num">${rank<=3?['★','★','★'][rank-1]:rank}</div>
      ${avatar(u)}
      <div style="flex:1;min-width:0">
        <div style="font-weight:700;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(u.nickname||u.name)} ${badge(u)}</div>
        <div class="muted">${u.best||0} WPM · ${u.totalTests||0} tests</div>
      </div>
      <div style="font-weight:800;font-size:14px;background:var(--grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent">${u.score||0}</div>
    </div>`;
  }).join(""):`<p class="muted center" style="padding:40px 0">${t("noUsers")}</p>`}`;
}

/* --- COMMUNITY --- */
function renderCommunity(){
  $("#app").innerHTML=`<h3 style="font-size:16px;margin-bottom:12px">${t("community")}</h3>
  <div class="search-bar"><input id="userSearch" placeholder="${t("search")}" oninput="filterUsers()"></div>
  <div id="userList"></div>`;
  filterUsers();
}

function filterUsers(){
  const q=($("#userSearch")?.value||"").toLowerCase();
  const list=users.filter(u=>u.id!==current.id&&u.role!=='admin'&&(u.name.toLowerCase().includes(q)||(u.nickname||'').toLowerCase().includes(q)));
  $("#userList").innerHTML=list.length?list.map(u=>`
    <div class="list-item">
      <div class="person" onclick="viewProfile('${u.id}')">
        ${avatar(u)}
        <div class="person-info">
          <div class="person-name">${esc(u.nickname||u.name)} ${badge(u)}</div>
          <div class="person-handle">@${esc(u.name)} · ${u.score||0} pts</div>
        </div>
      </div>
      <button class="btn-secondary" style="flex:0 0 auto" onclick="event.stopPropagation();openPrivate('${u.id}')">${t("message")}</button>
    </div>
  `).join(""):`<p class="muted center" style="padding:40px 0">${lang==='ar'?'لا نتائج':'No results'}</p>`;
}

/* --- SETTINGS --- */
function renderSettings(){
  const themes=["Dark","Light","Midnight","Ocean","Sunset","Forest","Cyberpunk"];
  $("#app").innerHTML=`
  <h3 style="font-size:16px;margin-bottom:12px">${t("settings")}</h3>
  <div class="card">
    <label>${t("theme")}</label>
    <select class="input-field" onchange="changeTheme(this.value)">${themes.map(x=>`<option ${document.documentElement.dataset.theme===x?"selected":""}>${x}</option>`).join("")}</select>
    <label>${t("language")}</label>
    <button class="btn-secondary" style="width:100%" onclick="toggleLang()">${lang==='ar'?'English':'العربية'}</button>
  </div>
  <div class="card">
    <div class="row" style="margin-bottom:12px">
      <div style="text-align:center"><div class="stat-value">${current.best||0}</div><div class="stat-label">${t("best")}</div></div>
      <div style="text-align:center"><div class="stat-value">${current.score||0}</div><div class="stat-label">${t("score")}</div></div>
      <div style="text-align:center"><div class="stat-value">${current.totalTests||0}</div><div class="stat-label">${t("tests")}</div></div>
    </div>
  </div>
  <div class="stack">
    <button class="btn-secondary" onclick="editProfile()">${t("edit")}</button>
    <button class="btn-secondary" onclick="openSupport()">${t("support")}</button>
    ${!current.vip&&current.role!=='admin'?`<button class="btn-primary" onclick="vipModal()">${t("vip")}</button>`:''}
    ${current.role==='admin'?`<button class="btn-secondary" onclick="adminPanel()">${t("admin")}</button>`:''}
    <button class="btn-danger" onclick="logout()">${t("logout")}</button>
  </div>`;
}

function changeTheme(v){localStorage.setItem("typing_theme",v);render();toast(lang==='ar'?"تم تغيير الثيم":"Theme changed",'success')}
function toggleLang(){lang=lang==="ar"?"en":"ar";localStorage.setItem("typing_lang",lang);render()}
function logout(){current=null;localStorage.removeItem("typing_user");page="bot";render();toast(lang==='ar'?"تم تسجيل الخروج":"Logged out",'info')}

/* --- MODALS --- */
function modal(title,content){
  $("#modalRoot").innerHTML=`<div class="modal-backdrop" onclick="if(event.target===this)closeModal()"><div class="modal"><div class="modal-head"><h3>${title}</h3><button onclick="closeModal()">×</button></div>${content}</div></div>`;
}
function closeModal(){$("#modalRoot").innerHTML=""}

function editProfile(){
  modal(t("edit"),`
  <div class="center" style="margin-bottom:12px">${avatar(current)}</div>
  <label>${lang==='ar'?'صورة جديدة':'New Photo'}</label>
  <input id="editPhoto" type="file" accept="image/*" class="input-field">
  <label>${t("nickname")}</label>
  <input id="editNick" class="input-field" value="${esc(current.nickname||"")}">
  <label>${t("bio")}</label>
  <textarea id="editBio" class="input-field">${esc(current.bio||"")}</textarea>
  <label>Instagram</label>
  <input id="editInstagram" class="input-field" value="${esc(current.instagram||"")}" placeholder="@username">
  <label>Snapchat</label>
  <input id="editSnapchat" class="input-field" value="${esc(current.snapchat||"")}" placeholder="@username">
  <div class="stack" style="margin-top:16px">
    <button class="btn-primary" onclick="saveProfile()">${t("save")}</button>
    <button class="btn-secondary" onclick="closeModal()">${t("cancel")}</button>
  </div>`);
}

function saveProfile(){
  const file=$("#editPhoto").files[0];
  const apply=photo=>{
    current.nickname=$("#editNick").value.trim()||current.name;
    current.bio=$("#editBio").value;
    current.instagram=$("#editInstagram").value.trim();
    current.snapchat=$("#editSnapchat").value.trim();
    if(photo)current.photo=photo;
    users=users.map(u=>u.id===current.id?current:u);
    persist();closeModal();render();
    toast(lang==='ar'?"تم حفظ التعديلات":"Profile saved",'success');
  };
  if(file){const r=new FileReader();r.onload=()=>apply(r.result);r.readAsDataURL(file)}
  else apply(null);
}

function socialLinks(u){
  let h="";
  if(u.instagram)h+=`<a class="social instagram" target="_blank" href="https://instagram.com/${encodeURIComponent(u.instagram.replace(/^@/,""))}"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><path d="M17.5 6.5h.01"/></svg>Instagram</a>`;
  if(u.snapchat)h+=`<a class="social snapchat" target="_blank" href="https://www.snapchat.com/add/${encodeURIComponent(u.snapchat.replace(/^@/,""))}"><svg viewBox="0 0 24 24"><path d="M12 3c-3 0-4 2-4 5v4c0 1-2 2-4 2 1 2 2 3 4 3s3-1 4-3c1 0 3 0 4-2-2 0-4-1-4-2V8c0-3-1-5-4-5Z"/></svg>Snapchat</a>`;
  return h;
}

function viewProfile(id){
  const u=users.find(x=>x.id===id);if(!u)return;
  const isMe=u.id===current.id;
  modal(t("profile"),`
    <div class="center" style="margin-bottom:12px">${avatar(u)}<h3 style="margin-top:8px">${esc(u.nickname||u.name)} ${badge(u)}</h3><div class="muted">@${esc(u.name)}</div></div>
    ${u.bio?`<p class="center" style="font-size:12px;margin-bottom:12px">${esc(u.bio)}</p>`:''}
    <div class="center">${socialLinks(u)}</div>
    <div class="row" style="margin:16px 0">
      <div class="center"><div class="stat-value">${u.score||0}</div><div class="stat-label">${t("score")}</div></div>
      <div class="center"><div class="stat-value">${u.best||0}</div><div class="stat-label">WPM</div></div>
    </div>
    ${!isMe?`<div class="stack"><button class="btn-primary" onclick="addFriend('${u.id}')">${t("friends")}</button><button class="btn-secondary" onclick="closeModal();openPrivate('${u.id}')">${t("message")}</button></div>`:`<button class="btn-secondary" onclick="closeModal();editProfile()">${t("edit")}</button>`}
  `);
}

function addFriend(id){
  const u=users.find(x=>x.id===id);if(!u)return;
  current.friends=current.friends||[];
  if(!current.friends.includes(id))current.friends.push(id);
  persist();closeModal();toast(lang==='ar'?"تمت الإضافة":"Added",'success');
}

/* --- PRIVATE CHAT --- */
function openPrivate(id){
  activeTarget=users.find(x=>x.id===id);if(!activeTarget)return;
  const key=[current.id,id].sort().join(":"),arr=chats[key]||[];
  modal(`<svg viewBox="0 0 24 24" style="width:16px;height:16px;vertical-align:middle"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg> ${esc(activeTarget.nickname||activeTarget.name)}`,
    `<div class="chatlog" id="privateLog" style="height:320px"></div>
    <div class="chat-input-area">
      <input id="privateInput" placeholder="${t("typeHere")}" onkeydown="if(event.key==='Enter')sendPrivate()">
      <button class="send-btn" onclick="sendPrivate()"><svg viewBox="0 0 24 24"><path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7Z"/></svg></button>
    </div>`);
  arr.forEach(m=>privateBubble(m.text,m.from===current.id));
  $("#privateLog").scrollTop=$("#privateLog").scrollHeight;
}

function privateBubble(text,mine){
  const log=$("#privateLog");if(!log)return;
  log.insertAdjacentHTML('beforeend',`<div class="bubble-wrap ${mine?'me':'bot'}"><div class="bubble-avatar">${mine?esc(current.avatar||'?'):esc(activeTarget.avatar||'?')}</div><div><div class="bubble">${esc(text)}</div><div class="bubble-time">${nowTime()}</div></div></div>`);
  log.scrollTop=log.scrollHeight;
}

function sendPrivate(){
  const input=$("#privateInput"),text=input.value.trim();if(!text||!activeTarget)return;
  input.value="";
  const key=[current.id,activeTarget.id].sort().join(":");
  chats[key]=chats[key]||[];
  chats[key].push({from:current.id,text,at:Date.now()});
  persist();privateBubble(text,true);
  setTimeout(()=>{
    if(!$("#privateLog"))return;
    const replies=lang==='ar'?["شكراً على رسالتك!","سعيد بالتحدث معك","سأرد قريباً","فكرة رائعة!"]:["Thanks!","Nice talking to you","I'll reply soon","Great idea!"];
    const reply=pick(replies);
    chats[key].push({from:activeTarget.id,text:reply,at:Date.now()});
    persist();privateBubble(reply,false);
  },1400);
}

/* --- SUPPORT --- */
function openSupport(){
  modal(t("support"),`
    <div class="chatlog" id="supportLog" style="height:320px"></div>
    <div class="chat-input-area">
      <input id="supportInput" placeholder="${t("typeHere")}" onkeydown="if(event.key==='Enter')sendSupport()">
      <button class="send-btn" onclick="sendSupport()"><svg viewBox="0 0 24 24"><path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7Z"/></svg></button>
    </div>`);
  const log=$("#supportLog");
  support.filter(m=>m.userId===current.id).forEach(m=>{
    const mine=m.from==="user";
    log.insertAdjacentHTML('beforeend',`<div class="bubble-wrap ${mine?'me':'bot'}"><div class="bubble-avatar">${mine?esc(current.avatar||'?'):'S'}</div><div><div class="bubble">${esc(m.text)}</div></div></div>`);
  });
  log.scrollTop=log.scrollHeight;
}

function sendSupport(){
  const input=$("#supportInput"),text=input.value.trim();if(!text)return;
  input.value="";
  support.push({userId:current.id,userName:current.name,from:"user",text,at:Date.now()});
  support.push({userId:current.id,userName:current.name,from:"system",text:lang==='ar'?"تم استلام رسالتك، سيتم الرد قريباً.":"Your message was received. We'll reply soon.",at:Date.now()});
  persist();openSupport();
}

/* --- ADMIN --- */
function adminPanel(){
  const blocked=users.filter(u=>u.banned);
  const supportUsers=[...new Map(support.map(m=>[m.userId,m])).values()];
  modal(t("admin"),`
    <h4 style="font-size:13px;margin-bottom:8px">${lang==='ar'?'المستخدمون المحظورون':'Banned Users'}</h4>
    <div>${blocked.length?blocked.map(u=>`<div class="list-item"><span>${esc(u.name)}</span><button class="btn-secondary" onclick="unban('${u.id}')">Unban</button></div>`).join(""):`<p class="muted">${lang==='ar'?'لا يوجد':'None'}</p>`}</div>
    <hr>
    <h4 style="font-size:13px;margin-bottom:8px">${lang==='ar'?'صندوق الدعم':'Support Inbox'}</h4>
    <div>${supportUsers.length?supportUsers.map(m=>`<div class="list-item"><span>${esc(m.userName)}</span><button class="btn-secondary" onclick="closeModal();adminReply('${m.userId}')">Open</button></div>`).join(""):`<p class="muted">${lang==='ar'?'لا رسائل':'No messages'}</p>`}</div>
  `);
}
function unban(id){const u=users.find(x=>x.id===id);if(u)u.banned=false;persist();adminPanel();toast("Unbanned",'success')}
function adminReply(id){
  const u=users.find(x=>x.id===id);if(!u)return;
  modal(`Support: ${esc(u.name)}`,`
    <div class="chatlog" id="adminSupportLog" style="height:320px"></div>
    <div class="chat-input-area">
      <input id="adminSupportInput" placeholder="${t("typeHere")}" onkeydown="if(event.key==='Enter')adminSend('${id}')">
      <button class="send-btn" onclick="adminSend('${id}')"><svg viewBox="0 0 24 24"><path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7Z"/></svg></button>
    </div>`);
  support.filter(m=>m.userId===id).forEach(m=>{
    const mine=m.from==="admin";
    $("#adminSupportLog").insertAdjacentHTML('beforeend',`<div class="bubble-wrap ${mine?'me':'bot'}"><div class="bubble-avatar">${mine?'A':'U'}</div><div><div class="bubble">${esc(m.text)}</div></div></div>`);
  });
}
function adminSend(id){
  const input=$("#adminSupportInput"),text=input.value.trim();if(!text)return;
  input.value="";
  support.push({userId:id,userName:users.find(u=>u.id===id)?.name||"",from:"admin",text,at:Date.now()});
  persist();adminReply(id);
}

/* --- VIP --- */
function vipModal(){
  modal(t("vip"),`
    <p class="muted center" style="margin-bottom:16px">${lang==='ar'?'افتح المزايا الحصرية':'Unlock exclusive features'}</p>
    <div class="vip-card">
      <div style="font-weight:800;margin-bottom:8px">${lang==='ar'?'مزايا VIP':'VIP Benefits'}</div>
      <div class="small" style="line-height:2">
        ✓ ${lang==='ar'?'شارة VIP مميزة':'Premium VIP badge'}<br>
        ✓ ${lang==='ar'?'ثيمات حصرية':'Exclusive themes'}<br>
        ✓ ${lang==='ar'?'إحصائيات متقدمة':'Advanced statistics'}<br>
        ✓ ${lang==='ar'?'أولوية في الدعم':'Priority support'}
      </div>
    </div>
    <div class="vip-plan" onclick="payment('monthly')">
      <div><div style="font-weight:700">${t("monthly")}</div><div class="small">$2.99/mo</div></div>
      <div style="font-weight:800;color:var(--accent)">$2.99</div>
    </div>
    <div class="vip-plan featured" onclick="payment('yearly')">
      <div><div style="font-weight:700">${t("yearly")} ★</div><div class="small">$26.99/yr · Save 25%</div></div>
      <div style="font-weight:800;color:var(--accent)">$26.99</div>
    </div>
    <div class="vip-plan" onclick="payment('lifetime')">
      <div><div style="font-weight:700">${t("lifetime")}</div><div class="small">One-time</div></div>
      <div style="font-weight:800;color:var(--accent)">$79.99</div>
    </div>
  `);
}

function payment(plan){
  modal(lang==='ar'?"الدفع":"Payment",`
    <div class="tabs">
      <button class="active" onclick="$$('.tabs button').forEach(b=>b.classList.remove('active'));this.classList.add('active')">Apple Pay</button>
      <button onclick="$$('.tabs button').forEach(b=>b.classList.remove('active'));this.classList.add('active')">${lang==='ar'?'بطاقة':'Card'}</button>
    </div>
    <label>${lang==='ar'?'رقم البطاقة':'Card Number'}</label>
    <input class="input-field" placeholder="4242 4242 4242 4242" inputmode="numeric">
    <div class="row">
      <div><label>MM/YY</label><input class="input-field" placeholder="12/25"></div>
      <div><label>CVC</label><input class="input-field" placeholder="123" maxlength="4"></div>
    </div>
    <button class="btn-primary" style="width:100%;margin-top:16px" onclick="payNow('${plan}')">${t("pay")}</button>
  `);
}

function payNow(plan){
  modal(lang==='ar'?"معالجة الدفع":"Processing",`<div class="spinner"></div><p class="center muted">${lang==='ar'?'يرجى الانتظار...':'Please wait...'}</p>`);
  setTimeout(()=>{
    current.vip=true;current.vipPlan=plan;
    users=users.map(u=>u.id===current.id?current:u);
    persist();
    modal(lang==='ar'?"تمت الترقية":"Upgraded",`<div class="center" style="padding:16px 0"><div style="font-size:48px;margin-bottom:12px">✓</div><h3 style="background:var(--grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent">${lang==='ar'?'مرحباً بك في VIP!':'Welcome to VIP!'}</h3></div><button class="btn-primary" style="width:100%" onclick="closeModal();render()">${lang==='ar'?'ابدأ':'Continue'}</button>`);
    toast(lang==='ar'?"تمت الترقية بنجاح":"Upgraded successfully",'success');
  },2000);
}

/* --- NAV --- */
$("#nav").addEventListener("click",e=>{
  const b=e.target.closest("button[data-page]");
  if(b){page=b.dataset.page;render()}
});

render();
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def serve_app():
    return HTML_PAGE

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)