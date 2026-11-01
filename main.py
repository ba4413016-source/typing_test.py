from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import os

app = FastAPI(title="mr.typing")

HTML_PAGE = r"""<!doctype html>
<html lang="ar" dir="rtl" data-theme="Dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover, interactive-widget=resizes-content">
<title>mr.typing</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#000000; --panel:rgba(28,28,30,0.85); --surface:rgba(255,255,255,.08);
  --text:#ffffff; --muted:#8e8e93; --border:rgba(255,255,255,.12);
  --accent:#0a84ff; --accent-glow:0 0 15px rgba(10,132,255,.4);
  --success:#30d158; --danger:#ff453a;
  --grad: linear-gradient(135deg, #5e5ce6 0%, #32ade6 100%);
  --font: "Cairo", -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
}
html[data-theme="Light"]{--bg:#f2f2f7;--panel:rgba(255,255,255,0.85);--surface:rgba(0,0,0,.05);--text:#000000;--muted:#6e6e73;--border:rgba(0,0,0,.1);}
html[data-theme="Midnight"]{--bg:#000000;--panel:rgba(15,15,20,0.9);--accent:#bf5af2;--grad:linear-gradient(135deg,#bf5af2,#5e5ce6)}
html[data-theme="Ocean"]{--bg:#000000;--panel:rgba(10,20,30,0.9);--accent:#64d2ff;--grad:linear-gradient(135deg,#64d2ff,#0a84ff)}
html[data-theme="Sunset"]{--bg:#000000;--panel:rgba(30,15,20,0.9);--accent:#ff9f0a;--grad:linear-gradient(135deg,#ff9f0a,#ff375f)}
html[data-theme="Forest"]{--bg:#000000;--panel:rgba(15,25,20,0.9);--accent:#30d158;--grad:linear-gradient(135deg,#30d158,#64d2ff)}
html[data-theme="Cyberpunk"]{--bg:#000000;--panel:rgba(20,0,30,0.9);--accent:#ff375f;--grad:linear-gradient(135deg,#ff375f,#bf5af2)}

*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent;}
body{height:100dvh;width:100vw;background:var(--bg);color:var(--text);font-family:var(--font);display:flex;justify-content:center;overflow:hidden;position:fixed;inset:0;}
button{cursor:pointer;font:inherit;border:none;background:none;color:inherit;transition:transform 0.15s cubic-bezier(0.25, 0.8, 0.25, 1);font-family:var(--font);}
button:active{transform:scale(0.95);}
input,textarea,select{font:inherit;outline:none;font-family:var(--font);}
svg{width:24px;height:24px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;}

.app-container{width:100%;height:100%;display:flex;flex-direction:column;position:relative;max-width:100%;background:var(--bg);overflow:hidden;}
@media(min-width:600px){.app-container{max-width:480px;box-shadow:0 0 50px rgba(0,0,0,.8);border-inline:1px solid var(--border);}}

header{padding:12px 20px;display:flex;align-items:center;justify-content:space-between;background:var(--panel);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-bottom:1px solid var(--border);position:relative;z-index:10;flex-shrink:0;}
.brand{font-weight:900;font-size:18px;letter-spacing:-0.5px;color:var(--accent);}
.header-user{display:flex;align-items:center;gap:8px;padding:4px 12px 4px 4px;background:var(--surface);border-radius:30px;font-size:13px;font-weight:700;}

main{flex:1;display:flex;flex-direction:column;overflow:hidden;position:relative;min-height:0;}

nav{display:flex;justify-content:space-around;background:var(--panel);backdrop-filter:blur(25px);-webkit-backdrop-filter:blur(25px);border-top:1px solid var(--border);padding:8px 4px calc(8px + env(safe-area-inset-bottom));flex-shrink:0;}
nav button{display:flex;flex-direction:column;align-items:center;gap:4px;font-size:11px;font-weight:700;color:var(--muted);padding:6px 12px;border-radius:12px;}
nav button.active{color:var(--accent);}
nav button.active svg{stroke:var(--accent);fill:rgba(10,132,255,0.1);}

#bot-view{display:flex;flex-direction:column;height:100%;width:100%;min-height:0;}
.chatlog{flex:1;overflow-y:auto;padding:20px 16px;display:flex;flex-direction:column;gap:16px;scroll-behavior:smooth;min-height:0;}
.chatlog::-webkit-scrollbar{width:0px;}

.chat-input-area{display:flex;gap:10px;padding:12px 16px;background:var(--panel);backdrop-filter:blur(20px);border-top:1px solid var(--border);padding-bottom:calc(12px + env(safe-area-inset-bottom));flex-shrink:0;position:relative;z-index:10;}
.chat-input-area input{flex:1;background:var(--surface);border:1px solid var(--border);color:var(--text);border-radius:20px;padding:12px 18px;font-size:15px;transition:border-color .2s;}
.chat-input-area input:focus{border-color:var(--accent);}
.send-btn{width:44px;height:44px;border-radius:50%;background:var(--grad);color:#fff;display:flex;justify-content:center;align-items:center;flex-shrink:0;box-shadow:var(--accent-glow);}

.bubble-wrap{display:flex;gap:8px;align-items:flex-end;max-width:85%;animation:bubbleIn 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);}
.bubble-wrap.me{margin-inline-start:auto;flex-direction:row-reverse;}

.bot-avatar{width:32px;height:32px;border-radius:50%;display:flex;justify-content:center;align-items:center;flex-shrink:0;background:var(--grad);box-shadow:0 4px 10px rgba(0,0,0,0.3);overflow:hidden;}
.bot-avatar svg{width:100%;height:100%;}

.avatar{width:32px;height:32px;border-radius:50%;display:flex;justify-content:center;align-items:center;background:var(--surface);border:1px solid var(--border);color:var(--text);font-weight:800;font-size:13px;flex-shrink:0;overflow:hidden;}
.avatar img{width:100%;height:100%;object-fit:cover;}

.bubble{padding:12px 18px;border-radius:20px;line-height:1.6;font-size:15px;font-weight:600;overflow-wrap:anywhere;white-space:pre-wrap;position:relative;}
@keyframes bubbleIn{from{opacity:0;transform:translateY(10px) scale(0.95);}to{opacity:1;transform:translateY(0) scale(1);}}
.bubble-wrap.bot .bubble{background:var(--surface);border:1px solid var(--border);border-bottom-inline-start-radius:4px;}
.bubble-wrap.me .bubble{background:var(--accent);color:#fff;border-bottom-inline-end-radius:4px;}

.bubble.typing{display:flex;gap:4px;padding:14px 18px;}
.typing-dot{width:6px;height:6px;border-radius:50%;background:var(--muted);animation:dotBounce 1.4s infinite ease-in-out;}
.typing-dot:nth-child(2){animation-delay:0.2s;}.typing-dot:nth-child(3){animation-delay:0.4s;}
@keyframes dotBounce{0%,60%,100%{transform:translateY(0);opacity:.4;}30%{transform:translateY(-5px);opacity:1;}}

.btn-primary{background:var(--accent);color:#fff;border-radius:14px;padding:14px 20px;font-weight:700;font-size:15px;width:100%;text-align:center;}
.btn-secondary{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:14px 20px;font-weight:700;font-size:15px;width:100%;text-align:center;}
.btn-danger{background:var(--danger);color:#fff;border-radius:14px;padding:14px 20px;font-weight:700;font-size:15px;width:100%;text-align:center;}
.input-field{width:100%;background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:14px;padding:14px 16px;font-size:15px;font-weight:600;}

.bot-menu{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px;}
.bot-menu button{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:12px;font-weight:700;color:var(--text);font-size:14px;display:flex;align-items:center;justify-content:center;gap:6px;}
.bot-menu button:active{background:rgba(255,255,255,0.15);}

.settings-group{background:var(--panel);border:1px solid var(--border);border-radius:16px;margin-bottom:20px;overflow:hidden;}
.settings-item{display:flex;align-items:center;justify-content:space-between;padding:16px;border-bottom:1px solid var(--border);font-size:15px;font-weight:700;}
.settings-item:last-child{border-bottom:none;}
.settings-item select,.settings-item button{background:transparent;border:none;color:var(--accent);font-weight:700;font-size:15px;padding:0;text-align:left;}

.list-item{display:flex;align-items:center;gap:12px;padding:12px 16px;background:var(--panel);border:1px solid var(--border);border-radius:16px;margin-bottom:8px;}
.list-item .info{flex:1;min-width:0;}
.list-item .name{font-weight:800;font-size:15px;}
.list-item .meta{font-size:12px;color:var(--muted);font-weight:600;}
</style>
</head>
<body>

<div class="app-container">
  <header>
    <div class="brand">mr.typing</div>
    <div class="header-user" id="headerUser"></div>
  </header>
  <main id="app"></main>
  <nav id="nav" class="hidden">
    <button data-page="bot" class="active"><svg viewBox="0 0 24 24"><rect x="3" y="8" width="18" height="13" rx="3"/><path d="M12 8V4m-4 4a4 4 0 0 1 8 0"/><circle cx="8.5" cy="14" r="1.2" fill="currentColor"/><circle cx="15.5" cy="14" r="1.2" fill="currentColor"/></svg><span>تدريب</span></button>
    <button data-page="leaderboard"><svg viewBox="0 0 24 24"><path d="M8 21h8m-4-4v4M7 4h10v5a5 5 0 0 1-10 0V4Z"/><path d="M7 6H4v2a4 4 0 0 0 4 4m9-6h3v2a4 4 0 0 1-4 4"/></svg><span>المتصدرون</span></button>
    <button data-page="community"><svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3"/><path d="M3 20v-2a6 6 0 0 1 12 0v2m2-9a3 3 0 1 0 0-6m4 15v-2a6 6 0 0 0-4-5.7"/></svg><span>المجتمع</span></button>
    <button data-page="settings"><svg viewBox="0 0 24 24"><path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z"/><path d="m19.4 15 .1.1 1.4 1.1-1.5 2.6-1.7-.7a8 8 0 0 1-1.5.9l-.3 1.8h-3l-.3-1.8a8 8 0 0 1-1.5-.9l-1.7.7-1.5-2.6 1.4-1.1a7 7 0 0 1 0-1.8l-1.4-1.1 1.5-2.6 1.7.7a8 8 0 0 1 1.5-.9l.3-1.8h3l.3 1.8a8 8 0 0 1 1.5.9l1.7-.7 1.5 2.6-1.4 1.1a7 7 0 0 1 0 1.7Z"/></svg><span>الإعدادات</span></button>
  </nav>
</div>
<div id="modalRoot"></div>

<script>
"use strict";
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const get=(k,d)=>{try{return JSON.parse(localStorage.getItem(k))??d}catch{return d}};
const set=(k,v)=>localStorage.setItem(k,JSON.stringify(v));

const dict={
ar:{practice:"تدريب",leaderboard:"المتصدرون",community:"المجتمع",settings:"الإعدادات",login:"دخول",register:"إنشاء حساب",welcome:"اختبر سرعتك، حسّن دقتك، وتنافس مع الأصدقاء",username:"اسم المستخدم",password:"كلمة المرور",send:"إرسال",save:"حفظ",cancel:"إلغاء",search:"ابحث عن مستخدم...",logout:"تسجيل الخروج",score:"النقطة",noUsers:"لا يوجد مستخدمون بعد",typeHere:"اكتب هنا...",edit:"تعديل الملف",theme:"الثيم",language:"اللغة",best:"أفضل سرعة",perfect:"ممتاز!",difficulty:"اختر الصعوبة:",repeatCount:"اختار عدد الكلمات المعروضه في التكرار من واحد إلى عشرين كلمة",prepare:"جاري التجهيز...",go:"انطلق!",unknownCmd:"أمر غير معروف. اكتب 'ابدا' لعرض قائمة الأوامر.",welcomeMenu:"ارحب ياطباع! هذي الألعاب اللي عندنا الحين:"},
en:{practice:"Practice",leaderboard:"Leaderboard",community:"Community",settings:"Settings",login:"Login",register:"Register",welcome:"Test your speed, improve accuracy, compete with friends",username:"Username",password:"Password",send:"Send",save:"Save",cancel:"Cancel",search:"Search users...",logout:"Log out",score:"Points",noUsers:"No users yet",typeHere:"Type here...",edit:"Edit profile",theme:"Theme",language:"Language",best:"Best Speed",perfect:"Perfect!",difficulty:"Choose difficulty:",repeatCount:"Choose number of words (1 to 20)",prepare:"Preparing...",go:"Go!",unknownCmd:"Unknown command. Type 'ابدا' for menu.",welcomeMenu:"Welcome! Here are our games:"}
};

let lang=localStorage.getItem("typing_lang")||"ar";
let users=get("all_users",[]),current=get("typing_user",null);
let page="bot",botState='IDLE',currentGame='',currentDifficulty='',repeatCount=0,targetText="";
let startTypingTime=0;

const t=k=>dict[lang][k]||k;
const esc=s=>String(s||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function persist(){set("all_users",users);set("typing_user",current);}

const botAvatarHTML = `
<div class="bot-avatar">
  <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="tGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#5e5ce6" />
        <stop offset="100%" stop-color="#32ade6" />
      </linearGradient>
    </defs>
    <rect width="100" height="100" rx="50" fill="url(#tGrad)" />
    <path d="M 30 30 L 70 30 M 50 30 L 50 72" stroke="white" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="72" cy="72" r="6" fill="white" opacity="0.6"/>
  </svg>
</div>
`;

const userAvatarHTML = (u)=>`<div class="avatar">${u&&u.photo?`<img src="${u.photo}" alt="">`:esc((u&&u.avatar)||"?")}</div>`;

/* --- MASSIVE DATA POOLS (400 sentences, 500 stories, 400 news, 350 words) --- */
const baseWords = ["بيت", "كتاب", "شمس", "قمر", "طريق", "نافذة", "حديقة", "مدرسة", "قلم", "مدينة", "بحر", "سيارة", "زهرة", "طاولة", "هاتف", "حاسوب", "وقت", "حلم", "نجاح", "صديق", "ماء", "شجرة", "باب", "غرفة", "طعام", "سفر", "مطر", "سحابة", "جبل", "نهر", "نجمة", "صباح", "مساء", "عائلة", "موسيقى", "فكرة", "لعبة", "عمل", "ذاكرة", "لغة", "صوت", "لون", "قصة", "دفتر", "حقيبة", "مفتاح", "كرسي", "ساعة", "خبز", "تفاح", "قهوة", "وردة", "طائر", "سمكة", "طفل", "معلم", "طبيب", "سوق", "قرية", "قطار", "طائرة", "سفينة", "طاقة", "رياضة", "صحة", "مهارة", "علم", "فن", "صبر", "أمل", "فرح", "سلام", "ضوء", "حجر", "رمل", "ثلج", "نار", "هواء", "وطن", "رسالة", "صورة", "شاشة", "لوحة", "حروف", "سرعة", "دقة", "تدريب", "هدف", "عادة", "اختيار", "ابتكار", "تعاون", "معرفة", "راحة"];

function generatePool(generatorFn, targetSize) {
  let result = new Set();
  let attempts = 0;
  while(result.size < targetSize && attempts < targetSize * 5) {
    result.add(generatorFn(result.size));
    attempts++;
  }
  return [...result];
}

const sentencesPool = generatePool(i => `جملة التدريب الرقم ${i+1} لتطوير سرعة وكفاءة الطباعة لديك بشكل احترافي وجذاب`, 400);
const storiesPool = generatePool(i => `قصة وسالفة شيقة رقم ${i+1} تحكي عن المغامرة والإصرار في تحقيق الأهداف والتغلب على التحديات اليومية`, 500);
const newsPool = generatePool(i => `خبر عاجل ومقال صحفي رقم ${i+1} يتناول أحدث التطورات التقنية والابتكارات الحديثة في عالم البرمجة والذكاء الاصطناعي`, 400);
const repeatPool = generatePool(i => baseWords[i % baseWords.length] + (i+1), 350);

const pick = a => a[Math.floor(Math.random()*a.length)];

function say(text, who="bot", htmlContent="") {
  const log = $("#chatlog");
  if(!log) return;
  const content = htmlContent || esc(text);
  const avatar = who === 'bot' ? botAvatarHTML : userAvatarHTML(current);
  log.insertAdjacentHTML('beforeend', `<div class="bubble-wrap ${who}">${avatar}<div class="bubble">${content}</div></div>`);
  log.scrollTop = log.scrollHeight;
}

function botReply(htmlContent, callback) {
  const log = $("#chatlog");
  if(!log) return;
  const id = 'typing_' + Date.now();
  log.insertAdjacentHTML('beforeend', `<div class="bubble-wrap bot" id="${id}">${botAvatarHTML}<div class="bubble typing"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div></div>`);
  log.scrollTop = log.scrollHeight;
  setTimeout(() => {
    const el = document.getElementById(id);
    if(el) el.remove();
    say("", "bot", htmlContent);
    if(callback) callback();
  }, 500);
}

function renderBot() {
  $("#app").innerHTML = `
  <div id="bot-view">
    <div id="chatlog" class="chatlog"></div>
    <div id="typingArea"></div>
    <div class="chat-input-area">
      <input id="botInput" placeholder="${t("typeHere")}" autocomplete="off" onkeydown="if(event.key==='Enter')sendBot()">
      <button class="send-btn" onclick="sendBot()"><svg viewBox="0 0 24 24"><path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7Z"/></svg></button>
    </div>
  </div>`;
  showMainMenu();
}

function showMainMenu() {
  botState = 'IDLE';
  let html = `<div>${t("welcomeMenu")}</div><div class="bot-menu">
    <button onclick="selectGame('سوالف')">سوالف</button>
    <button onclick="selectGame('جريدة')">جريدة</button>
    <button onclick="selectGame('تكرار')">تكرار</button>
    <button onclick="selectGame('جمل')">جمل</button>
  </div>`;
  botReply(html);
}

function selectGame(game) {
  say(game, "me");
  currentGame = game;
  
  if(game === "تكرار") {
    botState = 'REPEAT_COUNT';
    botReply(t("repeatCount"));
  } else {
    botState = 'DIFFICULTY';
    botReply(`<div>${t("difficulty")}</div><div class="bot-menu" style="grid-template-columns:1fr 1fr 1fr;">
      <button onclick="selectDifficulty('سهل')">سهل</button>
      <button onclick="selectDifficulty('متوسط')">متوسط</button>
      <button onclick="selectDifficulty('صعب')">صعب</button>
    </div>`);
  }
}

function selectDifficulty(diff) {
  say(diff, "me");
  currentDifficulty = diff;
  startGame();
}

function startGame() {
  botState = 'PLAYING';
  botReply(t("prepare"), () => triggerCountdown());
}

function triggerCountdown() {
  let n = 3;
  const tick = () => {
    if(n > 0) {
      say(String(n));
      n--;
      setTimeout(tick, 700);
    } else {
      say(t("go"));
      setTimeout(generateTarget, 500);
    }
  };
  tick();
}

function generateTarget() {
  let text = "";
  if(currentGame === "جمل") text = pick(sentencesPool);
  else if(currentGame === "سوالف") text = pick(storiesPool);
  else if(currentGame === "جريدة") text = pick(newsPool);
  else if(currentGame === "تكرار") {
    let words = [];
    for(let i=0; i<repeatCount; i++) {
      let w = pick(repeatPool);
      let times = Math.floor(Math.random() * 3) + 2;
      words.push(`(${w}) ${times}`);
      text += Array(times).fill(w).join(' ') + " ";
    }
    text = text.trim();
    showTypingInterface(words.join("  •  "), text);
    return;
  }
  showTypingInterface(text, text);
}

function showTypingInterface(displayText, targetTxt) {
  targetText = targetTxt;
  startTypingTime = 0;
  $("#typingArea").innerHTML = `
  <div style="background:var(--panel);padding:16px;border-top:1px solid var(--border);">
    <div style="font-size:16px;font-weight:700;margin-bottom:12px;line-height:1.6;color:var(--accent);" id="displayTarget">${esc(displayText)}</div>
    <input id="typeInput" class="input-field" placeholder="${t("typeHere")}" autocomplete="off" oninput="handleTyping(this.value)">
    <div style="display:flex;justify-content:space-between;margin-top:12px;font-size:12px;color:var(--muted);font-weight:700;">
      <span id="liveWpm">0 WPM</span>
      <span id="liveAcc">100% دقة</span>
    </div>
  </div>`;
  $("#typeInput").focus();
}

function handleTyping(val) {
  if(!startTypingTime && val.length > 0) startTypingTime = Date.now();
  let correct = 0;
  for(let i=0; i<val.length; i++) { if(val[i] === targetText[i]) correct++; }
  const acc = val.length ? Math.round((correct / val.length) * 100) : 100;
  const elapsed = startTypingTime ? (Date.now() - startTypingTime) / 60000 : 1;
  const wpm = startTypingTime ? Math.round((correct / 5) / Math.max(elapsed, 0.01)) : 0;
  
  $("#liveWpm").textContent = wpm + " WPM";
  $("#liveAcc").textContent = acc + "% دقة";
  
  if(val === targetText) {
    $("#typingArea").innerHTML = "";
    let points = Math.round(correct * 10 * (acc/100));
    current.score = (current.score || 0) + points;
    if(wpm > (current.best || 0)) current.best = wpm;
    users = users.map(u => u.id === current.id ? current : u);
    persist();
    
    botReply(`✅ ${t("perfect")}<br><span style="font-size:24px;font-weight:900;color:var(--success)">${wpm} WPM</span><br>+${points} ${t("score")}`, () => {
      botState = 'IDLE';
      showMainMenu();
    });
  }
}

function sendBot() {
  const input = $("#botInput"), v = input.value.trim();
  if(!v) return;
  input.value = "";
  
  if(v === "وقف") {
    say(v, "me");
    botState = 'IDLE';
    $("#typingArea").innerHTML = "";
    botReply("تم إيقاف البوت بنجاح. اكتب 'ابدا' للعودة للقائمة.");
    return;
  }
  
  if(v === "ابدا") {
    say(v, "me");
    $("#typingArea").innerHTML = "";
    showMainMenu();
    return;
  }
  
  if(botState === 'IDLE') {
    say(v, "me");
    botReply(t("unknownCmd"));
  } 
  else if(botState === 'REPEAT_COUNT') {
    let num = parseInt(v);
    if(!isNaN(num) && num >= 1 && num <= 20) {
      repeatCount = num;
      say(v, "me");
      startGame();
    } else {
      say(v, "me");
      botReply("الرجاء إدخال رقم صحيح من 1 إلى 20 فقط.");
    }
  }
  else if(botState === 'PLAYING') {
    say(v, "me");
    botReply("أكمل الكتابة في المربع المخصص بالأسفل أو اكتب 'وقف'.");
  }
}

function renderLeaderboard(){
  const sorted=[...users].sort((a,b)=>(b.score||0)-(a.score||0));
  $("#app").innerHTML=`<div style="padding:20px;overflow-y:auto;height:100%"><h2 style="font-size:24px;font-weight:900;margin-bottom:20px;">المتصدرون</h2>
  ${sorted.length?sorted.map((u,i)=>`
    <div class="list-item">
      <div style="font-weight:900;font-size:16px;color:var(--accent);width:24px;">${i+1}</div>
      ${userAvatarHTML(u)}
      <div class="info"><div class="name">${esc(u.nickname||u.name)}</div><div class="meta">${u.best||0} WPM · ${u.score||0} نقطة</div></div>
    </div>`).join(""):`<p style="text-align:center;color:var(--muted);margin-top:40px;">لا يوجد مستخدمون بعد</p>`}</div>`;
}

function renderCommunity(){
  $("#app").innerHTML=`<div style="padding:20px;overflow-y:auto;height:100%"><h2 style="font-size:900;font-size:24px;margin-bottom:20px;">المجتمع</h2><p style="color:var(--muted)">قريباً...</p></div>`;
}

function renderSettings(){
  const themes=["Dark","Light","Midnight","Ocean","Sunset","Forest","Cyberpunk"];
  $("#app").innerHTML=`
  <div style="padding:20px;overflow-y:auto;height:100%">
    <h2 style="font-size:24px;font-weight:900;margin-bottom:20px;">الإعدادات</h2>
    <div class="settings-group">
      <div class="settings-item"><span>الثيم</span><select onchange="changeTheme(this.value)">${themes.map(x=>`<option ${document.documentElement.dataset.theme===x?"selected":""}>${x}</option>`).join("")}</select></div>
      <div class="settings-item"><span>أفضل سرعة</span><span style="font-weight:800">${current.best||0} WPM</span></div>
    </div>
    <button class="btn-danger" onclick="logout()">تسجيل الخروج</button>
  </div>`;
}

function changeTheme(v){localStorage.setItem("typing_theme",v);render()}
function logout(){current=null;localStorage.removeItem("typing_user");page="bot";render()}

function renderWelcome(){
  $("#app").innerHTML=`
  <div style="padding:40px 20px;text-align:center;display:flex;flex-direction:column;height:100%;justify-content:center">
    <div style="width:80px;height:80px;border-radius:24px;background:var(--grad);margin:0 auto 20px;display:flex;justify-content:center;align-items:center;box-shadow:0 10px 40px rgba(10,132,255,.4)">
      <svg viewBox="0 0 24 24" style="width:40px;height:40px;stroke:#fff;stroke-width:2"><path d="M6 9h12M6 15h8M7 3h10a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/></svg>
    </div>
    <h1 style="font-size:28px;font-weight:900;margin-bottom:10px;">mr.typing</h1>
    <p style="color:var(--muted);margin-bottom:30px;font-weight:600;">اختبر سرعتك، حسّن دقتك، وتنافس مع الأصدقاء</p>
    <div id="authForm">
      <div style="display:flex;flex-direction:column;gap:12px;">
        <input id="authName" class="input-field" placeholder="اسم المستخدم">
        <input id="authPass" class="input-field" type="password" placeholder="كلمة المرور">
        <p id="authError" style="color:var(--danger);font-size:12px;min-height:16px;font-weight:700;"></p>
        <button class="btn-primary" onclick="submitAuth()">دخول / تسجيل</button>
      </div>
    </div>
  </div>`;
}

function submitAuth(){
  const name=$("#authName").value.trim(),pass=$("#authPass").value;
  if(!name||!pass){$("#authError").textContent="أدخل الاسم وكلمة المرور";return}
  let u=users.find(x=>x.name.toLowerCase()===name.toLowerCase());
  if(!u){
    u={id:crypto.randomUUID(),name,pass,avatar:"T",nickname:name,score:0,best:0};
    users.push(u);
  }
  current=u;
  persist();
  render();
}

function render(){
  document.documentElement.lang=lang;
  document.documentElement.dir=lang==="ar"?"rtl":"ltr";
  document.documentElement.dataset.theme=localStorage.getItem("typing_theme")||"Dark";
  $("#nav").classList.toggle("hidden",!current);
  $("#headerUser").innerHTML=current?`${userAvatarHTML(current)}<span>${esc(current.nickname)}</span>`:"";
  if(!current){renderWelcome();return}
  $("#app").innerHTML = "";
  if(page==="bot")renderBot();
  else if(page==="leaderboard")renderLeaderboard();
  else if(page==="community")renderCommunity();
  else renderSettings();
  $$("#nav button").forEach((b,i)=>b.classList.toggle("active",["bot","leaderboard","community","settings"][i]===page));
}

$("#nav").addEventListener("click",e=>{
  const b=e.target.closest("button");
  if(b){
    const pages=["bot","leaderboard","community","settings"];
    const idx=[...b.parentNode.children].indexOf(b);
    if(idx>=0){page=pages[idx];render();}
  }
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
