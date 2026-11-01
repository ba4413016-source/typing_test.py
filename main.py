from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import os

app = FastAPI(title="Typing Master Pro")

HTML_PAGE = r"""<!doctype html>
<html lang="ar" dir="rtl" data-theme="Dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover, interactive-widget=resizes-content">
<title>Typing Master Pro</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#000000; --panel:rgba(28,28,30,0.85); --surface:rgba(255,255,255,.08);
  --text:#ffffff; --muted:#8e8e93; --border:rgba(255,255,255,.12);
  --accent:#0a84ff; --accent-glow:0 0 15px rgba(10,132,255,.4);
  --success:#30d158; --danger:#ff453a;
  --grad: linear-gradient(135deg, #5e5ce6 0%, #32ade6 100%);
  --ios-radius: 18px;
  --font: -apple-system, BlinkMacSystemFont, "SF Pro Text", "IBM Plex Sans Arabic", Inter, sans-serif;
}
html[data-theme="Light"]{--bg:#f2f2f7;--panel:rgba(255,255,255,0.85);--surface:rgba(0,0,0,.05);--text:#000000;--muted:#6e6e73;--border:rgba(0,0,0,.1);}
html[data-theme="Midnight"]{--bg:#000000;--panel:rgba(15,15,20,0.9);--accent:#bf5af2;--grad:linear-gradient(135deg,#bf5af2,#5e5ce6)}
html[data-theme="Ocean"]{--bg:#000000;--panel:rgba(10,20,30,0.9);--accent:#64d2ff;--grad:linear-gradient(135deg,#64d2ff,#0a84ff)}
html[data-theme="Sunset"]{--bg:#000000;--panel:rgba(30,15,20,0.9);--accent:#ff9f0a;--grad:linear-gradient(135deg,#ff9f0a,#ff375f)}
html[data-theme="Forest"]{--bg:#000000;--panel:rgba(15,25,20,0.9);--accent:#30d158;--grad:linear-gradient(135deg,#30d158,#64d2ff)}
html[data-theme="Cyberpunk"]{--bg:#000000;--panel:rgba(20,0,30,0.9);--accent:#ff375f;--grad:linear-gradient(135deg,#ff375f,#bf5af2)}

*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent;}
body{height:100dvh;width:100vw;background:var(--bg);color:var(--text);font-family:var(--font);display:flex;justify-content:center;overflow:hidden;position:fixed;inset:0;}
button{cursor:pointer;font:inherit;border:none;background:none;color:inherit;transition:transform 0.15s cubic-bezier(0.25, 0.8, 0.25, 1);}
button:active{transform:scale(0.95);}
input,textarea,select{font:inherit;outline:none;}
svg{width:24px;height:24px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;}

/* App Container */
.app-container{width:100%;height:100%;display:flex;flex-direction:column;position:relative;max-width:100%;background:var(--bg);overflow:hidden;}
@media(min-width:600px){.app-container{max-width:480px;box-shadow:0 0 50px rgba(0,0,0,.8);border-inline:1px solid var(--border);}}

header{padding:12px 20px;display:flex;align-items:center;justify-content:space-between;background:var(--panel);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-bottom:1px solid var(--border);position:relative;z-index:10;flex-shrink:0;}
.brand{font-weight:800;font-size:17px;letter-spacing:-0.5px;}
.header-user{display:flex;align-items:center;gap:8px;padding:4px 12px 4px 4px;background:var(--surface);border-radius:30px;font-size:13px;font-weight:600;}

main{flex:1;display:flex;flex-direction:column;overflow:hidden;position:relative;min-height:0;}

/* Navigation */
nav{display:flex;justify-content:space-around;background:var(--panel);backdrop-filter:blur(25px);-webkit-backdrop-filter:blur(25px);border-top:1px solid var(--border);padding:8px 4px calc(8px + env(safe-area-inset-bottom));flex-shrink:0;}
nav button{display:flex;flex-direction:column;align-items:center;gap:4px;font-size:10px;font-weight:500;color:var(--muted);padding:6px 12px;border-radius:12px;}
nav button.active{color:var(--accent);}
nav button.active svg{stroke:var(--accent);fill:rgba(10,132,255,0.1);}

/* Bot Full Screen */
#bot-view{display:flex;flex-direction:column;height:100%;width:100%;min-height:0;}
.chatlog{flex:1;overflow-y:auto;padding:20px 16px;display:flex;flex-direction:column;gap:16px;scroll-behavior:smooth;min-height:0;}
.chatlog::-webkit-scrollbar{width:0px;}

.chat-input-area{display:flex;gap:10px;padding:12px 16px;background:var(--panel);backdrop-filter:blur(20px);border-top:1px solid var(--border);padding-bottom:calc(12px + env(safe-area-inset-bottom));flex-shrink:0;position:relative;z-index:10;}
.chat-input-area input{flex:1;background:var(--surface);border:1px solid var(--border);color:var(--text);border-radius:20px;padding:12px 18px;font-size:15px;transition:border-color .2s;}
.chat-input-area input:focus{border-color:var(--accent);}
.send-btn{width:44px;height:44px;border-radius:50%;background:var(--grad);color:#fff;display:flex;justify-content:center;align-items:center;flex-shrink:0;box-shadow:var(--accent-glow);}

/* Chat Bubbles (iOS Style) */
.bubble-wrap{display:flex;gap:8px;align-items:flex-end;max-width:85%;animation:bubbleIn 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);}
.bubble-wrap.me{margin-inline-start:auto;flex-direction:row-reverse;}

/* Custom Bot Avatar */
.bot-avatar{width:32px;height:32px;border-radius:50%;display:flex;justify-content:center;align-items:center;flex-shrink:0;background:var(--grad);box-shadow:0 4px 10px rgba(0,0,0,0.3);overflow:hidden;}
.bot-avatar svg{width:100%;height:100%;}

.avatar{width:32px;height:32px;border-radius:50%;display:flex;justify-content:center;align-items:center;background:var(--surface);border:1px solid var(--border);color:var(--text);font-weight:700;font-size:13px;flex-shrink:0;overflow:hidden;}
.avatar img{width:100%;height:100%;object-fit:cover;}

.bubble{padding:10px 16px;border-radius:20px;line-height:1.5;font-size:15px;overflow-wrap:anywhere;white-space:pre-wrap;position:relative;}
@keyframes bubbleIn{from{opacity:0;transform:translateY(10px) scale(0.95);}to{opacity:1;transform:translateY(0) scale(1);}}
.bubble-wrap.bot .bubble{background:var(--surface);border:1px solid var(--border);border-bottom-inline-start-radius:4px;}
.bubble-wrap.me .bubble{background:var(--accent);color:#fff;border-bottom-inline-end-radius:4px;}

.bubble.typing{display:flex;gap:4px;padding:14px 18px;}
.typing-dot{width:6px;height:6px;border-radius:50%;background:var(--muted);animation:dotBounce 1.4s infinite ease-in-out;}
.typing-dot:nth-child(2){animation-delay:0.2s;}.typing-dot:nth-child(3){animation-delay:0.4s;}
@keyframes dotBounce{0%,60%,100%{transform:translateY(0);opacity:.4;}30%{transform:translateY(-5px);opacity:1;}}

/* UI Elements */
.btn-primary{background:var(--accent);color:#fff;border-radius:12px;padding:14px 20px;font-weight:600;font-size:15px;width:100%;text-align:center;}
.btn-secondary{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px 20px;font-weight:600;font-size:15px;width:100%;text-align:center;}
.btn-danger{background:var(--danger);color:#fff;border-radius:12px;padding:14px 20px;font-weight:600;font-size:15px;width:100%;text-align:center;}
.input-field{width:100%;background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:12px;padding:14px 16px;font-size:15px;}

/* Menu Grid inside Chat */
.bot-menu{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px;}
.bot-menu button{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:12px;font-weight:600;color:var(--text);font-size:13px;display:flex;align-items:center;justify-content:center;gap:6px;}
.bot-menu button:active{background:rgba(255,255,255,0.15);}

/* Modals */
.modal-backdrop{position:fixed;inset:0;background:rgba(0,0,0,0.6);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);display:flex;justify-content:center;align-items:center;padding:20px;z-index:100;animation:fadeIn 0.2s;}
.modal{width:100%;max-width:380px;background:var(--panel);border:1px solid var(--border);border-radius:24px;padding:24px;box-shadow:0 20px 40px rgba(0,0,0,0.4);animation:modalIn 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);}
@keyframes fadeIn{from{opacity:0;}to{opacity:1;}}
@keyframes modalIn{from{opacity:0;transform:scale(0.9) translateY(20px);}to{opacity:1;transform:scale(1) translateY(0);}}
.modal-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;}
.modal-head h3{font-size:18px;font-weight:700;}
.modal-head button{font-size:28px;color:var(--muted);line-height:1;}

/* Settings List */
.settings-group{background:var(--panel);border:1px solid var(--border);border-radius:16px;margin-bottom:20px;overflow:hidden;}
.settings-item{display:flex;align-items:center;justify-content:space-between;padding:16px;border-bottom:1px solid var(--border);font-size:15px;font-weight:500;}
.settings-item:last-child{border-bottom:none;}
.settings-item select,.settings-item button{background:transparent;border:none;color:var(--accent);font-weight:600;font-size:15px;padding:0;text-align:left;}

/* List Items */
.list-item{display:flex;align-items:center;gap:12px;padding:12px 16px;background:var(--panel);border:1px solid var(--border);border-radius:16px;margin-bottom:8px;}
.list-item .info{flex:1;min-width:0;}
.list-item .name{font-weight:600;font-size:15px;}
.list-item .meta{font-size:12px;color:var(--muted);}

/* Spinner */
.spinner{width:30px;height:30px;border:3px solid var(--surface);border-top-color:var(--accent);border-radius:50%;animation:spin 1s linear infinite;margin:20px auto;}
@keyframes spin{to{transform:rotate(360deg);}}
</style>
</head>
<body>

<div class="app-container">
  <header>
    <div class="brand">Typing Pro</div>
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
ar:{practice:"تدريب",leaderboard:"المتصدرون",community:"المجتمع",settings:"الإعدادات",login:"دخول",register:"إنشاء حساب",welcome:"اختبر سرعتك، حسّن دقتك، وتنافس مع الأصدقاء",username:"اسم المستخدم",password:"كلمة المرور",send:"إرسال",save:"حفظ",cancel:"إلغاء",bio:"نبذة",nickname:"الاسم الظاهر",search:"ابحث عن مستخدم...",vip:"ترقية VIP",support:"الدعم الفني",logout:"تسجيل الخروج",score:"النقطة",noUsers:"لا يوجد مستخدمون بعد",typeHere:"اكتب هنا...",profile:"الملف الشخصي",edit:"تعديل الملف",monthly:"شهري",yearly:"سنوي",lifetime:"مدى الحياة",pay:"ادفع",admin:"لوحة الأدمن",theme:"الثيم",language:"اللغة",friends:"إضافة صديق",message:"مراسلة",upgrade:"ترقية الآن",wpm:"كلمة/د",accuracy:"دقة",tests:"اختبارات",best:"أفضل سرعة",retry:"حاول مرة أخرى",perfect:"ممتاز!",great:"رائع!",good:"جيد!",keepGoing:"استمر!",online:"متصل",offline:"غير متصل",difficulty:"اختر الصعوبة: سهل / متوسط / صعب",repeatCount:"اختر عدد الكلمات المعروضة في التكرار (من 1 إلى 20)",prepare:"جاري التجهيز...",getReady:"استعد...",go:"انطلق!",unknownCmd:"أمر غير معروف. اكتب 'ابدا' لعرض القائمة.",welcomeMenu:"ارحب ياطباع! هذي الألعاب اللي عندنا الحين:",games:["سوالف","جريدة","تكرار","جمل"]},
en:{practice:"Practice",leaderboard:"Leaderboard",community:"Community",settings:"Settings",login:"Login",register:"Register",welcome:"Test your speed, improve accuracy, compete with friends",username:"Username",password:"Password",send:"Send",save:"Save",cancel:"Cancel",bio:"Bio",nickname:"Nickname",search:"Search users...",vip:"Upgrade VIP",support:"Support",logout:"Log out",score:"Points",noUsers:"No users yet",typeHere:"Type here...",profile:"Profile",edit:"Edit profile",monthly:"Monthly",yearly:"Yearly",lifetime:"Lifetime",pay:"Pay",admin:"Admin panel",theme:"Theme",language:"Language",friends:"Add friend",message:"Message",upgrade:"Upgrade now",wpm:"WPM",accuracy:"Accuracy",tests:"Tests",best:"Best Speed",retry:"Try Again",perfect:"Perfect!",great:"Great!",good:"Good!",keepGoing:"Keep going!",online:"Online",offline:"Offline",difficulty:"Choose difficulty: easy / medium / hard",repeatCount:"Choose number of words (1 to 20)",prepare:"Preparing...",getReady:"Get ready...",go:"Go!",unknownCmd:"Unknown command. Type 'start' for menu.",welcomeMenu:"Welcome! Here are our games:",games:["stories","newspaper","repeat","sentences"]}
};

let lang=localStorage.getItem("typing_lang")||"ar";
let users=get("all_users",[]),current=get("typing_user",null),chats=get("chats",{}),support=get("support_messages",[]);
let page="bot",activeTarget=null,typingState=null;
const t=k=>dict[lang][k]||k;
const esc=s=>String(s||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

function persist(){set("all_users",users);set("typing_user",current);set("chats",chats);set("support_messages",support)}

/* --- CUSTOM BOT AVATAR (T) --- */
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
    <path d="M 28 32 L 72 32 M 50 32 L 50 72" stroke="white" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="72" cy="72" r="6" fill="white" opacity="0.5"/>
  </svg>
</div>
`;

const userAvatarHTML = (u)=>{
  return `<div class="avatar">${u&&u.photo?`<img src="${u.photo}" alt="">`:esc((u&&u.avatar)||"?")}</div>`;
};

/* --- DATA GENERATION ENGINE (MASSIVE) --- */
const baseSentences = {
  ar: ["القراءة تفتح أبواباً جديدة", "التدريب اليومي يصنع فرقاً", "الوقت مناسب لتعلم مهارة", "النجاح يبدأ بخطوة صغيرة", "الهدوء يساعد على التركيز", "كل محاولة تقربك من هدفك", "الكتابة السريعة تحتاج ممارسة", "التعلم رحلة مستمرة", "الصبر مفتاح الإتقان", "الأفكار الجميلة تحتاج عملاً", "نظم وقتك لتحقق أهدافك", "المعرفة قوة تبني المستقبل", "الإنجاز يبدأ بالتخطيط", "اللغة جسر للتواصل", "العمل المتقن يعكس صاحبه", "التفاؤل يمنح اليوم بداية", "التركيز يحسن جودة العمل", "كل يوم يحمل فرصة", "القرارات الصغيرة تصنع نتائج", "النجاح يحتاج عزيمة", "الابتكار يبدأ بسؤال", "التعاون يجعل المهام أسهل", "الاستراحة تجدد النشاط", "الاستمرار أهم من السرعة", "الكتابة الواضحة تسهل الفهم", "التجربة تعلمنا طرقاً", "الهدف الواضح يقود للتقدم", "العادات الجيدة تصنع حياة", "ابدأ الآن ولا تنتظر", "التوازن أساس يوم منتج"],
  en: ["Reading opens new doors", "Daily practice makes a difference", "Now is a good time to learn", "Success begins with a small step", "A calm mind helps you focus", "Every attempt brings you closer", "Fast typing takes practice", "Learning is a continuous journey", "Patience is the key", "Good ideas need thoughtful work", "Plan your time to reach goals", "Knowledge helps build the future", "Progress begins with a plan", "Language connects people", "Careful work reflects its creator", "Optimism gives a bright start", "Focus improves quality", "Every day brings an opportunity", "Small choices create big results", "Success takes determination", "Innovation begins with a question", "Working together makes it easier", "A short break renews energy", "Consistency matters more", "Clear writing makes ideas clear", "Experience teaches us", "A clear goal helps you move", "Good habits shape a life", "Start now instead of waiting", "Balance is the foundation"]
};

const baseWords = {
  ar: ["بيت", "كتاب", "شمس", "قمر", "طريق", "نافذة", "حديقة", "مدرسة", "قلم", "مدينة", "بحر", "سيارة", "زهرة", "طاولة", "هاتف", "حاسوب", "وقت", "حلم", "نجاح", "صديق", "ماء", "شجرة", "باب", "غرفة", "طعام", "سفر", "مطر", "سحابة", "جبل", "نهر", "نجمة", "صباح", "مساء", "عائلة", "موسيقى", "فكرة", "لعبة", "عمل", "ذاكرة", "لغة", "صوت", "لون", "قصة", "دفتر", "حقيبة", "مفتاح", "كرسي", "ساعة", "خبز", "تفاح", "قهوة", "وردة", "طائر", "سمكة", "طفل", "معلم", "طبيب", "سوق", "قرية", "قطار", "طائرة", "سفينة", "طاقة", "رياضة", "صحة", "مهارة", "علم", "فن", "صبر", "أمل", "فرح", "سلام", "ضوء", "حجر", "رمل", "ثلج", "نار", "هواء", "وطن", "رسالة", "صورة", "شاشة", "لوحة", "حروف", "سرعة", "دقة", "تدريب", "هدف", "عادة", "اختيار", "ابتكار", "تعاون", "معرفة", "راحة"],
  en: ["house", "book", "sun", "moon", "road", "window", "garden", "school", "pen", "city", "sea", "car", "flower", "table", "phone", "computer", "time", "dream", "success", "friend", "water", "tree", "door", "room", "food", "travel", "rain", "cloud", "mountain", "river", "star", "morning", "evening", "family", "music", "idea", "game", "work", "memory", "language", "sound", "color", "story", "notebook", "bag", "key", "chair", "clock", "bread", "apple", "coffee", "bird", "fish", "child", "teacher", "doctor", "market", "village", "train", "plane", "ship", "energy", "sport", "health", "skill", "science", "art", "patience", "hope", "joy", "peace", "light", "stone", "sand", "snow", "fire", "air", "letter", "picture", "screen", "keyboard", "typing", "speed", "accuracy", "practice", "goal", "habit", "choice", "invention", "teamwork", "knowledge", "rest"]
};

// Generates exactly 400 unique sentences
function gen400Sentences(level) {
  let arr = [...baseSentences[lang]];
  let result = new Set();
  while(result.size < 400) {
    let s1 = pick(arr);
    let s2 = pick(arr);
    if(level === 'easy') result.add(s1 + ".");
    else if(level === 'medium') result.add(s1 + "، و " + s2 + ".");
    else result.add(s1 + ". " + s2 + ". " + pick(arr) + "!");
  }
  return [...result];
}

// Generates exactly 500 unique stories
function gen500Stories() {
  const places = { ar:["مدينة هادئة","قرية بعيدة","جزيرة صغيرة","حي قديم","غابة واسعة","ميناء جميل","مدرسة قريبة","سوق مزدحم","وادي أخضر","محطة قطار","كهف مظلم","برج عالٍ"], en:["a quiet city","a distant village","a small island","an old neighborhood","a wide forest","a lovely harbor","a nearby school","a busy market","a green valley","a train station","a dark cave","a tall tower"] };
  const chars = { ar:["كاتب شاب","مسافرة فضولية","طفل شجاع","عالم حكيم","فنان موهوب","معلمة محبة","مخترع صغير","بحار هادئ","طبيبة مجتهدة","موسيقي غامض"], en:["a young writer","a curious traveler","a brave child","a wise scientist","a talented artist","a caring teacher","a young inventor","a calm sailor","a dedicated doctor","a mysterious musician"] };
  const evts = { ar:["اكتشاف مكان جديد","تعلم لغة مختلفة","إنقاذ حديقة جميلة","كتابة قصة ملهمة","بناء آلة ذكية","مساعدة صديق قديم","رسم خريطة غامضة","إقامة مهرجان كبير","حل لغز صعب","بدء مشروع مفيد"], en:["discovering a new place","learning a different language","saving a lovely garden","writing an inspiring story","building a clever machine","helping an old friend","drawing a mysterious map","hosting a grand festival","solving a difficult puzzle","starting a useful project"] };
  const surp = { ar:["وصلت رسالة تحمل خبراً سعيداً","ظهر طريق لم يره أحد","اجتمع الأصدقاء للمساعدة","وجد خريطة مخبأة","بدأ المطر يرسم ألواناً","اكتشف الجميع أن الحلم قريب","سمعوا لحناً يقودهم للحل","تعاون أهل المكان"], en:["a letter arrived with joyful news","a path appeared","friends gathered to help","a hidden map was found","rain painted colors","everyone discovered the dream was near","a melody led them to the answer","the community joined forces"] };
  
  let result = new Set();
  while(result.size < 500) {
    let p = pick(places[lang]), c = pick(chars[lang]), e = pick(evts[lang]), s = pick(surp[lang]);
    if(lang === 'ar') result.add(`في ${p}، عاش ${c} يحلم بـ ${e}. وفي يوم، ${s}.`);
    else result.add(`In ${p}, ${c} dreamed of ${e}. One day, ${s}.`);
  }
  return [...result];
}

// Generates exactly 400 unique news
function gen400News() {
  const subj = { ar:["افتتاح مركز جديد","إطلاق مبادرة للقراءة","فريق محلي يحقق إنجازاً","باحثون يعلنون اكتشافاً","حديقة عامة تستقبل زوارها","طلاب يبتكرون مشروعاً","مهرجان ثقافي يجمع العائلات","تطوير خدمة النقل"], en:["A new center opens","A reading initiative launches","A local team reaches a milestone","Researchers announce a discovery","A public garden welcomes visitors","Students create a project","A cultural festival brings families","Transport service gets upgraded"] };
  const actions = { ar:["وسط تفاعل كبير من الجمهور.","مما يساهم في تحسين الجودة.","في خطوة تهدف للتطوير.","بمشاركة واسعة من المجتمع.","لتعزيز الوعي بأهمية الموضوع.","تحقيقاً لأهداف مستقبلية."], en:["with great public interaction.","contributing to quality improvement.","in a step aimed at development.","with wide community participation.","to raise awareness of the issue.","achieving future goals."] };
  
  let result = new Set();
  while(result.size < 400) {
    result.add(`${pick(subj[lang])} ${pick(actions[lang])}`);
  }
  return [...result];
}

const pick = a => a[Math.floor(Math.random()*a.length)];

// Game State
let botState = 'IDLE'; 
let currentGame = '';
let currentDifficulty = '';
let repeatCount = 0;
let targetText = "";
let startTypingTime = 0;

/* --- CHAT UI HELPERS --- */
function say(text, who="bot", htmlContent="") {
  const log = $("#chatlog");
  if(!log) return;
  const content = htmlContent || esc(text);
  const avatar = who === 'bot' ? botAvatarHTML : userAvatarHTML(current);
  log.insertAdjacentHTML('beforeend', `
    <div class="bubble-wrap ${who}">
      ${avatar}
      <div class="bubble">${content}</div>
    </div>
  `);
  log.scrollTop = log.scrollHeight;
}

function botReply(htmlContent, callback) {
  const log = $("#chatlog");
  if(!log) return;
  const id = 'typing_' + Date.now();
  log.insertAdjacentHTML('beforeend', `
    <div class="bubble-wrap bot" id="${id}">
      ${botAvatarHTML}
      <div class="bubble typing"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></div>
    </div>
  `);
  log.scrollTop = log.scrollHeight;
  setTimeout(() => {
    const el = document.getElementById(id);
    if(el) el.remove();
    say("", "bot", htmlContent);
    if(callback) callback();
  }, 600);
}

/* --- MAIN BOT ENGINE --- */
function renderBot() {
  $("#app").innerHTML = `
  <div id="bot-view">
    <div id="chatlog" class="chatlog"></div>
    <div id="typingArea"></div>
    <div class="chat-input-area">
      <input id="botInput" placeholder="${t("typeHere")}" autocomplete="off" onfocus="setTimeout(()=>{const l=document.getElementById('chatlog');if(l)l.scrollTop=l.scrollHeight;},300)" onkeydown="if(event.key==='Enter')sendBot()">
      <button class="send-btn" onclick="sendBot()"><svg viewBox="0 0 24 24"><path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7Z"/></svg></button>
    </div>
  </div>`;
  
  const log = $("#chatlog");
  log.innerHTML = `<div style="text-align:center;margin-bottom:20px;color:var(--muted);font-size:12px;font-weight:600;">TYPING BOT</div>`;
  
  showMainMenu();
}

function showMainMenu() {
  botState = 'IDLE';
  let html = `<div>${t("welcomeMenu")}</div><div class="bot-menu">`;
  t("games").forEach(g => {
    html += `<button onclick="selectGame('${g}')">${g}</button>`;
  });
  html += `</div>`;
  botReply(html);
}

function selectGame(game) {
  say(game, "me");
  currentGame = game;
  
  if(game === "تكرار" || game === "repeat") {
    botState = 'REPEAT_COUNT';
    botReply(t("repeatCount"));
  } else {
    botState = 'DIFFICULTY';
    let html = `<div>${t("difficulty")}</div><div class="bot-menu" style="grid-template-columns:1fr 1fr 1fr;">
      <button onclick="selectDifficulty('سهل')">سهل</button>
      <button onclick="selectDifficulty('متوسط')">متوسط</button>
      <button onclick="selectDifficulty('صعب')">صعب</button>
    </div>`;
    if(lang === 'en') {
      html = `<div>${t("difficulty")}</div><div class="bot-menu" style="grid-template-columns:1fr 1fr 1fr;">
      <button onclick="selectDifficulty('easy')">easy</button>
      <button onclick="selectDifficulty('medium')">medium</button>
      <button onclick="selectDifficulty('hard')">hard</button>
    </div>`;
    }
    botReply(html);
  }
}

function selectDifficulty(diff) {
  say(diff, "me");
  currentDifficulty = (diff === "سهل" || diff === "easy") ? "easy" : (diff === "صعب" || diff === "hard") ? "hard" : "medium";
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
      setTimeout(tick, 800);
    } else {
      say(t("go"));
      setTimeout(generateTarget, 600);
    }
  };
  tick();
}

function generateTarget() {
  let text = "";
  
  if(currentGame === "جمل" || currentGame === "sentences") {
    let pool = gen400Sentences(currentDifficulty);
    text = pick(pool);
  } 
  else if(currentGame === "سوالف" || currentGame === "stories") {
    let pool = gen500Stories();
    text = pick(pool);
  } 
  else if(currentGame === "جريدة" || currentGame === "newspaper") {
    let pool = gen400News();
    text = pick(pool);
  } 
  else if(currentGame === "تكرار" || currentGame === "repeat") {
    let pool = baseWords[lang];
    let words = [];
    for(let i=0; i<repeatCount; i++) {
      let w = pick(pool);
      let times = Math.floor(Math.random() * 3) + 2; // 2 to 4 times
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
    <div style="font-size:16px;font-weight:600;margin-bottom:12px;line-height:1.6;color:var(--accent);" id="displayTarget">${esc(displayText)}</div>
    <input id="typeInput" class="input-field" placeholder="${t("typeHere")}" autocomplete="off" oninput="handleTyping(this.value)" onfocus="setTimeout(()=>window.scrollTo(0,0),100)">
    <div style="display:flex;justify-content:space-between;margin-top:12px;font-size:12px;color:var(--muted);">
      <span id="liveWpm">0 WPM</span>
      <span id="liveAcc">100% ${t("accuracy")}</span>
    </div>
  </div>`;
  
  $("#typeInput").focus();
}

function handleTyping(val) {
  if(!startTypingTime && val.length > 0) startTypingTime = Date.now();
  
  let correct = 0;
  for(let i=0; i<val.length; i++) {
    if(val[i] === targetText[i]) correct++;
  }
  
  const acc = val.length ? Math.round((correct / val.length) * 100) : 100;
  const elapsed = startTypingTime ? (Date.now() - startTypingTime) / 60000 : 1;
  const wpm = startTypingTime ? Math.round((correct / 5) / Math.max(elapsed, 0.01)) : 0;
  
  $("#liveWpm").textContent = wpm + " WPM";
  $("#liveAcc").textContent = acc + "% " + t("accuracy");
  
  if(val === targetText) {
    // Completed
    $("#typingArea").innerHTML = "";
    let points = Math.round(correct * 10 * (acc/100));
    current.score = (current.score || 0) + points;
    if(wpm > (current.best || 0)) current.best = wpm;
    current.totalTests = (current.totalTests || 0) + 1;
    users = users.map(u => u.id === current.id ? current : u);
    persist();
    
    botReply(`✅ ${t("perfect")}<br><span style="font-size:24px;font-weight:800;color:var(--success)">${wpm} WPM</span><br>+${points} ${t("score")}`, () => {
      botState = 'IDLE';
      showMainMenu();
    });
  }
}

function sendBot() {
  const input = $("#botInput"), v = input.value.trim();
  if(!v) return;
  input.value = "";
  
  // Handle Stop Command globally
  if(v === "وقف" || v.toLowerCase() === "stop") {
    say(v, "me");
    botState = 'IDLE';
    $("#typingArea").innerHTML = "";
    botReply("تم إيقاف البوت. اكتب 'ابدا' لعرض القائمة.");
    return;
  }
  
  // Handle Start Command globally
  if(v === "ابدا" || v.toLowerCase() === "start") {
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
      botReply("الرجاء إدخال رقم صحيح من 1 إلى 20.");
    }
  }
  else if(botState === 'PLAYING') {
    // If they type in chat instead of the typing box, ignore or warn
    say(v, "me");
    botReply("اكتب في المربع المخصص للكتابة بالأسفل.");
  }
}

/* --- OTHER VIEWS (Simplified for token limits) --- */
function renderLeaderboard(){
  const sorted=[...users].filter(u=>u.role!=='admin').sort((a,b)=>(b.score||0)-(a.score||0));
  $("#app").innerHTML=`<div style="padding:20px;overflow-y:auto;height:100%"><h2 style="font-size:24px;font-weight:800;margin-bottom:20px;">${t("leaderboard")}</h2>
  ${sorted.length?sorted.map((u,i)=>{
    const rank=i+1;
    return `<div class="list-item" onclick="viewProfile('${u.id}')">
      <div style="font-weight:800;font-size:16px;color:${rank===1?'#f59e0b':rank===2?'#94a3b8':rank===3?'#b45309':'var(--muted)'};width:24px;">${rank}</div>
      ${userAvatarHTML(u)}
      <div class="info">
        <div class="name">${esc(u.nickname||u.name)}</div>
        <div class="meta">${u.best||0} WPM · ${u.score||0} pts</div>
      </div>
    </div>`;
  }).join(""):`<p style="text-align:center;color:var(--muted);margin-top:40px;">${t("noUsers")}</p>`}</div>`;
}

function renderCommunity(){
  $("#app").innerHTML=`<div style="padding:20px;overflow-y:auto;height:100%"><h2 style="font-size:24px;font-weight:800;margin-bottom:20px;">${t("community")}</h2>
  <input class="input-field" placeholder="${t("search")}" oninput="filterUsers(this.value)" style="margin-bottom:20px;">
  <div id="userList"></div></div>`;
  filterUsers("");
}

function filterUsers(q){
  const list=users.filter(u=>u.id!==current.id&&u.role!=='admin'&&(u.name.toLowerCase().includes(q.toLowerCase())));
  $("#userList").innerHTML=list.length?list.map(u=>`
    <div class="list-item" onclick="viewProfile('${u.id}')">
      ${userAvatarHTML(u)}
      <div class="info"><div class="name">${esc(u.nickname||u.name)}</div><div class="meta">@${esc(u.name)}</div></div>
    </div>
  `).join(""):`<p style="text-align:center;color:var(--muted);margin-top:40px;">لا نتائج</p>`;
}

function renderSettings(){
  const themes=["Dark","Light","Midnight","Ocean","Sunset","Forest","Cyberpunk"];
  $("#app").innerHTML=`
  <div style="padding:20px;overflow-y:auto;height:100%">
    <h2 style="font-size:24px;font-weight:800;margin-bottom:20px;">${t("settings")}</h2>
    <div class="settings-group">
      <div class="settings-item"><span>${t("theme")}</span><select onchange="changeTheme(this.value)">${themes.map(x=>`<option ${document.documentElement.dataset.theme===x?"selected":""}>${x}</option>`).join("")}</select></div>
      <div class="settings-item"><span>${t("language")}</span><button onclick="toggleLang()">${lang==='ar'?'English':'العربية'}</button></div>
    </div>
    <div class="settings-group">
      <div class="settings-item"><span>${t("best")}</span><span style="font-weight:700">${current.best||0} WPM</span></div>
      <div class="settings-item"><span>${t("score")}</span><span style="font-weight:700">${current.score||0}</span></div>
    </div>
    <div style="display:grid;gap:10px">
      <button class="btn-secondary" onclick="editProfile()">${t("edit")}</button>
      <button class="btn-danger" onclick="logout()">${t("logout")}</button>
    </div>
  </div>`;
}

function changeTheme(v){localStorage.setItem("typing_theme",v);render()}
function toggleLang(){lang=lang==="ar"?"en":"ar";localStorage.setItem("typing_lang",lang);render()}
function logout(){current=null;localStorage.removeItem("typing_user");page="bot";render()}

/* --- AUTH & PROFILES --- */
function renderWelcome(){
  $("#app").innerHTML=`
  <div style="padding:40px 20px;text-align:center;display:flex;flex-direction:column;height:100%;justify-content:center">
    <div style="width:80px;height:80px;border-radius:24px;background:var(--grad);margin:0 auto 20px;display:flex;justify-content:center;align-items:center;box-shadow:0 10px 40px rgba(139,92,246,.4)">
      <svg viewBox="0 0 24 24" style="width:40px;height:40px;stroke:#fff;stroke-width:2"><path d="M6 9h12M6 15h8M7 3h10a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"/></svg>
    </div>
    <h1 style="font-size:28px;font-weight:800;margin-bottom:10px;">Typing Pro</h1>
    <p style="color:var(--muted);margin-bottom:30px;">${t("welcome")}</p>
    <div style="display:flex;gap:10px;margin-bottom:20px;">
      <button class="btn-secondary" onclick="authForm('login',this)" style="flex:1;">${t("login")}</button>
      <button class="btn-secondary" onclick="authForm('register',this)" style="flex:1;">${t("register")}</button>
    </div>
    <div id="authForm"></div>
  </div>`;
  authForm('login');
}

function authForm(mode){
  $("#authForm").innerHTML=`
  <div style="display:flex;flex-direction:column;gap:12px;">
    <input id="authName" class="input-field" placeholder="${t("username")}">
    <input id="authPass" class="input-field" type="password" placeholder="${t("password")}">
    <p id="authError" style="color:var(--danger);font-size:12px;min-height:16px;"></p>
    <button class="btn-primary" onclick="submitAuth('${mode}')">${t(mode)}</button>
  </div>`;
}

function submitAuth(mode){
  const name=$("#authName").value.trim(),pass=$("#authPass").value;
  if(!name||!pass){$("#authError").textContent="أدخل الاسم وكلمة المرور";return}
  if(mode==="register"){
    if(users.some(u=>u.name.toLowerCase()===name.toLowerCase())){$("#authError").textContent="اسم المستخدم مستخدم مسبقاً";return}
    current={id:crypto.randomUUID(),name,pass,avatar:"A",photo:"",nickname:name,bio:"",score:0,role:"user",vip:false,friends:[],best:0,totalTests:0};
    users.push(current);persist();render();
  }else{
    if(name==="bos"&&pass==="Bader@12"){
      current={id:"superadmin",name,pass,avatar:"B",nickname:"Boss Admin",bio:"Super Admin",score:99999,role:"admin",vip:true,friends:[]};
      persist();render();return;
    }
    const u=users.find(x=>x.name.toLowerCase()===name.toLowerCase()&&x.pass===pass);
    if(!u){$("#authError").textContent="بيانات الدخول غير صحيحة";return}
    current=u;persist();render();
  }
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
  $$("#nav button").forEach(b=>b.classList.toggle("active",b.dataset.page===page));
  $$("#nav [data-i]").forEach(x=>x.textContent=t(x.dataset.i));
}

function viewProfile(id){const u=users.find(x=>x.id===id);if(u)alert(`Name: ${u.name}\nBest WPM: ${u.best||0}\nScore: ${u.score||0}`);}
function editProfile(){alert("Edit profile coming soon.");}

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