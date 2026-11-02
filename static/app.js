const $ = (id) => document.getElementById(id);
const esc = (v = "") =>
  String(v ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const storedLang = localPref("lang", "ar"),
  storedTheme = localPref("theme", "dark"),
  storedAccent = localPref("accent", "violet"),
  storedKeySound = localPref("key-sound", "off");
const state = {
  user: null,
  csrf: null,
  page: "home",
  lang: ["ar", "en"].includes(storedLang) ? storedLang : "ar",
  theme: ["dark", "light"].includes(storedTheme) ? storedTheme : "dark",
  accent: ["violet", "ocean", "mint", "rose"].includes(storedAccent)
    ? storedAccent
    : "violet",
  authMode: "login",
  busy: false,
  round: null,
  roundToken: 0,
  roundAbort: null,
  beginPromise: null,
  started: false,
  elapsedTimer: null,
  nextTimer: null,
  challenge: null,
  challengeToken: null,
  challengeTimer: null,
  challengeAbort: null,
  challengeRoundSubmitted: false,
  challengeSubmittedRound: 0,
  challengeOffset: 0,
  soundEnabled: storedKeySound === "on",
  audioContext: null,
  botMode: "idle",
  stopAfterCurrent: false,
  flow: {},
  threads: [],
  activeThread: null,
  messageAfter: 0,
  messagePoll: null,
  notificationPoll: null,
  toastTimer: null,
  botLiveTimer: null,
  pendingInvite: new URLSearchParams(location.search).get("challenge") || "",
  unreadNotifications: 0,
  unreadMessages: 0,
  communitySort: "points",
  searchTimer: null,
  lastStats: null,
};
function localPref(k, fallback) {
  try {
    const v = localStorage.getItem("typing." + k);
    return v ?? fallback;
  } catch {
    return fallback;
  }
}
function setPref(k, v) {
  try {
    localStorage.setItem("typing." + k, v);
  } catch {}
}
function tr(ar, en) {
  return state.lang === "ar" ? ar : en;
}
const labels = {
  home: ["الرئيسية", "Home"],
  bot: ["البوت", "Bot"],
  community: ["المجتمع", "Community"],
  messages: ["الرسائل", "Messages"],
  settings: ["الإعدادات", "Settings"],
  games: {
    sentences: ["جمل", "Sentences"],
    stories: ["قصص", "Stories"],
    news: ["أخبار", "News"],
    repeat: ["تكرار", "Repeat"],
  },
  levels: {
    easy: ["سهل", "Easy"],
    medium: ["متوسط", "Medium"],
    hard: ["صعب", "Hard"],
  },
  topics: {
    mixed: ["متنوع تلقائيًا", "Auto-mixed"],
    science: ["العلوم", "Science"],
    nature: ["الطبيعة", "Nature"],
    technology: ["التقنية", "Technology"],
    history: ["التاريخ", "History"],
    space: ["الفضاء", "Space"],
    health: ["الصحة", "Health"],
    travel: ["السفر", "Travel"],
    arts: ["الفنون", "Arts"],
    sports: ["الرياضة", "Sports"],
    education: ["التعليم", "Education"],
    culture: ["الثقافة", "Culture"],
    food: ["الطعام", "Food"],
  },
};
function toast(text) {
  const el = $("toast");
  if (!el) return;
  el.textContent = text;
  el.hidden = false;
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => (el.hidden = true), 3200);
}
function setTheme() {
  document.documentElement.dataset.theme = state.theme;
  document.documentElement.dataset.accent = state.accent;
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.content = state.theme === "dark" ? "#0d111b" : "#f7f8fc";
}
function setLanguage() {
  document.documentElement.lang = state.lang;
  document.documentElement.dir = state.lang === "ar" ? "rtl" : "ltr";
  $("authLanguage").textContent = state.lang === "ar" ? "English" : "العربية";
  $("exitBotButton").setAttribute("aria-label", tr("العودة إلى التطبيق", "Back to app"));
  $("exitBotButton").title = tr("العودة إلى التطبيق", "Back to app");
  $("chatChallengeLabel").textContent = tr("تحدٍّ", "Challenge");
  $("directChallengeButton").setAttribute("aria-label", tr("تحدَّ هذا المستخدم", "Challenge this user"));
  $("directChallengeButton").title = tr("تحدَّ هذا المستخدم", "Challenge this user");
  $("messageImageButton").setAttribute("aria-label", tr("إرفاق صورة", "Attach image"));
  $("messageImageButton").title = tr("إرفاق صورة", "Attach image");
  $("speakRoundButton").textContent = tr("استمع للنص", "Listen");
  $("botInput").setAttribute("aria-label", tr("اكتب أمرًا أو إجابة التدريب", "Type a command or practice answer"));
  $("botInput").placeholder = tr("اكتب أمرًا أو إجابة…", "Type a command or answer…");
  $("messageInput").setAttribute("aria-label", tr("رسالة خاصة", "Private message"));
  $("messageInput").placeholder = tr("اكتب رسالة…", "Write a message…");
  updateSoundButton();
  document
    .querySelectorAll("[data-nav]")
    .forEach(
      (x) =>
        (x.textContent = tr(
          labels[x.dataset.nav][0],
          labels[x.dataset.nav][1],
        )),
    );
}
function syncViewport() {
  let scheduled = false;
  const update = () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      const vv = window.visualViewport;
      const unzoomed = !vv || Math.abs(vv.scale - 1) <= 0.01;
      // Keep pinch zoom fully available; do not size the app to the zoomed sub-viewport.
      const h = unzoomed ? vv?.height || window.innerHeight : window.innerHeight;
      document.documentElement.style.setProperty("--app-height", `${h}px`);
      document.documentElement.style.setProperty("--app-top", "0px");
    });
  };
  window.addEventListener("resize", update, { passive: true });
  window.addEventListener("scroll", update, { passive: true });
  window.visualViewport?.addEventListener("resize", update, { passive: true });
  window.visualViewport?.addEventListener("scroll", update, { passive: true });
  update();
}
function errorText(err) {
  const d = err?.data?.detail;
  if (d && typeof d === "object")
    return state.lang === "ar"
      ? d.ar || d.en || d.code
      : d.en || d.ar || d.code;
  return typeof d === "string"
    ? d
    : err?.message || tr("حدث خطأ غير متوقع.", "An unexpected error occurred.");
}
class ApiError extends Error {
  constructor(status, data) {
    super("API " + status);
    this.status = status;
    this.data = data;
  }
}
async function api(
  path,
  { method = "GET", body, form, signal, auth = true } = {},
) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (method !== "GET" && method !== "HEAD" && auth && state.csrf)
    headers["X-CSRF-Token"] = state.csrf;
  let res;
  try {
    res = await fetch(path, {
      method,
      credentials: "same-origin",
      headers,
      body: form ? form : body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  } catch (e) {
    if (e.name === "AbortError") throw e;
    throw new Error(
      tr(
        "تعذر الاتصال بالخادم. تحقق من الاتصال وحاول مجددًا.",
        "Could not reach the server. Check your connection and try again.",
      ),
    );
  }
  let data = {};
  try {
    data = await res.json();
  } catch {}
  if (res.status === 401 && auth) {
    handleUnauthorized();
    throw new ApiError(401, data);
  }
  if (!res.ok) throw new ApiError(res.status, data);
  return data;
}
function handleUnauthorized() {
  state.user = null;
  state.csrf = null;
  clearRuntime();
  $("appScreen").hidden = true;
  $("authScreen").hidden = false;
  $("authError").textContent = tr(
    "انتهت الجلسة. سجّل الدخول مجددًا.",
    "Your session expired. Please sign in again.",
  );
  $("authError").hidden = false;
}
function showError(err, el = null) {
  const msg = errorText(err);
  if (err?.status === 403) {
    if (el) {
      el.textContent = msg;
      el.hidden = false;
    } else toast(tr("غير مسموح: ", "Not allowed: ") + msg);
  } else if (el) {
    el.textContent = msg;
    el.hidden = false;
  } else toast(msg);
}
function avatar(url, name, cls = "avatar") {
  return url
    ? `<img class="${cls}" src="${esc(url)}" alt="">`
    : `<span class="${cls} avatar-placeholder" aria-hidden="true">${esc((name || "?").slice(0, 1))}</span>`;
}
function who(u) {
  return esc(u?.display_name || u?.username || "");
}
function safeSocialUrl(kind, handle) {
  const h = String(handle || "")
    .replace(/^@/, "")
    .trim();
  if (!h) return "";
  const base = {
    instagram: "https://www.instagram.com/",
    snapchat: "https://www.snapchat.com/add/",
    twitter: "https://x.com/",
  }[kind];
  return base + encodeURIComponent(h);
}
function openModal(title, html) {
  $("modalTitle").textContent = title;
  $("modalBody").innerHTML = html;
  const d = $("modal");
  if (!d.open) d.showModal();
}
function closeModal() {
  if ($("modal").open) $("modal").close();
  $("modalBody").replaceChildren();
}
function appendBot(text, kind = "bot") {
  const log = $("botLog");
  const div = document.createElement("div");
  div.className = `chat-message ${kind}`;
  const bubble = document.createElement("div");
  bubble.className = "chat-bubble";
  bubble.textContent = text;
  div.append(bubble);
  log.append(div);
  log.scrollTop = log.scrollHeight;
  return div;
}
function setPage(page) {
  if (!["home", "bot", "community", "messages", "settings"].includes(page))
    return;
  state.page = page;
  document
    .querySelectorAll(".page")
    .forEach((p) => (p.hidden = p.id !== `page-${page}`));
  document.querySelectorAll(".nav-item").forEach((b) => {
    const active = b.dataset.page === page;
    b.classList.toggle("active", active);
    if (active) b.setAttribute("aria-current", "page");
    else b.removeAttribute("aria-current");
  });
  $("appScreen").classList.toggle("bot-active", page === "bot");
  $("appScreen").classList.toggle(
    "dm-open",
    page === "messages" && $("page-messages").classList.contains("conversation-open"),
  );
  if (page === "home") renderHome();
  if (page === "community") {
    loadCommunity();
    startChallengePolling();
  }
  if (page === "messages") {
    loadThreads();
    startMessagePolling();
  }
  if (page === "settings") renderSettings();
  if (state.challengeToken && page === "community") renderChallengePanel();
}
function showApp(session) {
  state.user = session.user;
  state.csrf = session.csrf;
  state.unreadNotifications = session.unread_notifications || 0;
  state.unreadMessages = session.unread_messages || 0;
  $("authScreen").hidden = true;
  $("appScreen").hidden = false;
  setLanguage();
  setTheme();
  updateBadges();
  updateBotIdentity();
  if (!$("botLog").children.length) botPrompt();
  renderHome();
  setPage("home");
  startNotificationPolling();
  if (state.pendingInvite) loadInvite(state.pendingInvite);
}
function updateBadges() {
  const n = $("notificationBadge"),
    m = $("messageBadge");
  n.textContent =
    state.unreadNotifications > 99 ? "99+" : String(state.unreadNotifications);
  n.hidden = !state.unreadNotifications;
  m.textContent =
    state.unreadMessages > 99 ? "99+" : String(state.unreadMessages);
  m.hidden = !state.unreadMessages;
}
function updateBotIdentity() {
  if (!state.user) return;
  $("botName").textContent =
    state.user.bot?.name || tr("رفيق الكتابة", "Typing companion");
  $("botAvatar").src = state.user.bot?.avatar_url || "/static/brand.svg";
  $("botStatus").textContent = tr(
    "اكتب «ابدأ» لبدء التدريب · «وقف» للإيقاف",
    "Type “start” to practice · “stop” to finish",
  );
  $("selfProfileButton").innerHTML = avatar(
    state.user.avatar_url,
    state.user.display_name,
    "avatar",
  );
  $("selfProfileButton").setAttribute(
    "aria-label",
    tr("ملفي الشخصي", "My profile"),
  );
}
async function loadSession() {
  try {
    const s = await api("/api/session", { auth: false });
    if (s.user) showApp(s);
    else {
      $("authScreen").hidden = false;
      $("appScreen").hidden = true;
      setLanguage();
    }
  } catch (e) {
    showError(e, $("authError"));
  }
}
function authStrings() {
  const reg = state.authMode === "register";
  $("loginTab").classList.toggle("active", !reg);
  $("registerTab").classList.toggle("active", reg);
  $("nicknameField").hidden = !reg;
  $("authPassword").autocomplete = reg ? "new-password" : "current-password";
  $("authSubmit").textContent = reg
    ? tr("إنشاء الحساب", "Create account")
    : tr("دخول إلى مساحتك", "Sign in");
  $("usernameLabel").textContent = tr("اسم المستخدم", "Username");
  $("passwordLabel").textContent = tr("كلمة المرور", "Password");
  $("nicknameLabel").textContent = tr("الاسم الظاهر", "Display name");
  $("authTagline").textContent = tr(
    "مساحة هادئة للتدريب، وأصدقاء يشاركونك الحماس.",
    "A calm space to practice and share the challenge.",
  );
  $("usernameHint").textContent = tr(
    "حروف إنجليزية وأرقام ونقطة وشرطة سفلية فقط؛ اليوزر فريد ولا يتكرر.",
    "English letters, numbers, dots and underscores only; usernames are unique.",
  );
  $("passwordHint").textContent = tr(
    "10 أحرف على الأقل. لا نضع كلمات مرور افتراضية.",
    "At least 10 characters. No default passwords.",
  );
}
$("loginTab").addEventListener("click", () => {
  state.authMode = "login";
  authStrings();
});
$("registerTab").addEventListener("click", () => {
  state.authMode = "register";
  authStrings();
});
$("authLanguage").addEventListener("click", () => {
  state.lang = state.lang === "ar" ? "en" : "ar";
  setPref("lang", state.lang);
  setLanguage();
  authStrings();
  if (state.user) {
    renderHome();
    if (state.page === "settings") renderSettings();
  }
});
$("authForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (state.busy) return;
  state.busy = true;
  $("authError").hidden = true;
  $("authError").classList.remove("form-success");
  $("authError").classList.add("form-error");
  $("authSubmit").disabled = true;
  try {
    const body = {
      username: $("authUsername").value.trim(),
      password: $("authPassword").value,
    };
    if (state.authMode === "register")
      body.display_name = $("authNickname").value.trim() || body.username;
    const s = await api(
      "/api/auth/" + (state.authMode === "register" ? "register" : "login"),
      { method: "POST", body, auth: false },
    );
    showApp(s);
  } catch (err) {
    showError(err, $("authError"));
  } finally {
    state.busy = false;
    $("authSubmit").disabled = false;
  }
});
function statCard(label, value) {
  return `<article class="stat-card"><span class="muted">${esc(label)}</span><strong>${esc(value)}</strong></article>`;
}
function renderHome() {
  if (!state.user) return;
  const s = state.user.stats || {};
  const host = $("page-home");
  host.innerHTML = `<header class="page-header"><div><p class="eyebrow">mr.typing</p><h1>${tr("أهلًا، ", "Welcome, ")}${who(state.user)}</h1><p class="muted">${tr("كل جولة تقرّبك من كتابة أسرع وأدق.", "Every round brings faster, more accurate typing.")}</p></div></header><section class="hero"><div class="hero-copy"><p class="eyebrow">${tr("مساحة تدريبك", "Your practice space")}</p><h2>${tr("اكتب بثقة. وتقدّم على طريقتك.", "Type with confidence. Improve at your pace.")}</h2><p>${tr("ابدأ جولة مع رفيقك، ثم تابع تقدمك وتحدَّ أصدقاءك.", "Start a round with your companion, track progress and challenge friends.")}</p></div><div class="hero-actions"><button class="primary-button" type="button" data-action="go-bot">${tr("ابدأ التدريب", "Start practicing")}</button><button class="secondary-button" type="button" data-action="go-community">${tr("استكشف المجتمع", "Explore community")}</button></div></section><section class="stat-grid">${statCard(tr("الجولات", "Rounds"), s.rounds || 0)}${statCard(tr("مجموع النقاط", "Total points"), s.total_points || 0)}${statCard(tr("أفضل سرعة", "Best speed"), `${s.best_wpm || 0} WPM`)}${statCard(tr("الدقة", "Accuracy"), `${s.accuracy || 0}%`)}</section><section class="event-hero section-gap"><div><p class="eyebrow">${tr("موعد أسبوعي", "Weekly event")}</p><h2>${tr("فعالية الجمعة", "Friday event")}</h2><p class="muted">${tr("تُجدول الفعالية القادمة للجمعة الساعة 8 مساءً بتوقيت السعودية؛ جولات متعددة وحكم آلي وإحصاءات لكل مشارك.", "Schedule the next event for Friday at 8 PM Saudi time, with multiple rounds, automatic judging, and participant stats.")}</p></div><button class="primary-button" type="button" data-action="create-friday">${tr("جهّز فعالية الجمعة", "Set up Friday event")}</button></section><section class="section-gap"><div class="section-heading"><div><p class="eyebrow">${tr("تحديات فعلية", "Play-ready formats")}</p><h2>${tr("اختر نمط التحدي", "Choose a challenge format")}</h2></div></div><div class="challenge-presets"><button class="action-card" type="button" data-action="create-preset" data-preset="speed"><strong>${tr("سباق السرعة", "Speed sprint")}</strong><span class="muted">${tr("جولتان وحكم السرعة.", "Two rounds judged by speed.")}</span></button><button class="action-card" type="button" data-action="create-preset" data-preset="accuracy"><strong>${tr("كأس الدقة", "Accuracy cup")}</strong><span class="muted">${tr("ثلاث جولات؛ الدقة أولًا.", "Three rounds; accuracy first.")}</span></button><button class="action-card" type="button" data-action="create-preset" data-preset="marathon"><strong>${tr("ماراثون بلا أخطاء", "Few-error marathon")}</strong><span class="muted">${tr("خمس جولات وحكم الأخطاء الأقل.", "Five rounds judged by fewest errors.")}</span></button></div></section><section class="section-gap"><div class="section-heading"><div><p class="eyebrow">${tr("من المجتمع", "From the community")}</p><h2>${tr("الفعاليات والتحديات القادمة", "Upcoming events and challenges")}</h2></div><button class="secondary-button" type="button" data-action="go-community">${tr("عرض المجتمع", "Open community")}</button></div><div id="homeChallengeList" class="challenge-list"><p class="empty-state">${tr("جارٍ تحميل التحديات…", "Loading challenges…")}</p></div></section><section class="section-gap"><div class="section-heading"><div><p class="eyebrow">${tr("ابدأ من هنا", "Start here")}</p><h2>${tr("اختر خطوتك التالية", "Choose your next step")}</h2></div></div><div class="card-grid"><button class="action-card" data-action="go-bot"><strong>${tr("تدريب مستمر", "Continuous practice")}</strong><span class="muted">${tr("اختر اللعبة والمستوى وتدرّب دون توقف.", "Choose a game and keep practicing.")}</span></button><button class="action-card" data-action="go-community"><strong>${tr("تحدَّ أصدقاءك", "Challenge friends")}</strong><span class="muted">${tr("أنشئ تحديًا أو انضم إلى فعالية عامة.", "Create or join a challenge.")}</span></button><button class="action-card" data-action="go-messages"><strong>${tr("رسائلك", "Your messages")}</strong><span class="muted">${tr("تواصل مع المتابعين والأصدقاء.", "Connect with people you follow.")}</span></button></div></section>`;
  loadHomeChallenges();
}
async function loadHomeChallenges() {
  const host = $("homeChallengeList");
  if (!host || !state.user) return;
  try {
    const data = await api("/api/challenges");
    const cards = (data.challenges || []).slice(0, 4).map((c) => challengeCard(c, false)).join("");
    host.innerHTML = cards || `<p class="empty-state">${tr("لا توجد فعاليات عامة بعد؛ أنشئ فعالية أو تحديًا من الأزرار أعلاه.", "No public events yet. Set one up with the buttons above.")}</p>`;
  } catch (error) {
    if (error.status !== 401) host.innerHTML = `<p class="form-error">${esc(errorText(error))}</p>`;
  }
}
function clearRoundTimers() {
  clearInterval(state.elapsedTimer);
  clearTimeout(state.nextTimer);
  clearInterval(state.botLiveTimer);
  state.elapsedTimer = state.nextTimer = state.botLiveTimer = null;
}
function cancelLocalRound() {
  state.roundToken++;
  state.roundAbort?.abort();
  state.roundAbort = null;
  clearRoundTimers();
  state.round = null;
  state.started = false;
  state.beginPromise = null;
  state.stopAfterCurrent = false;
}
function clearRuntime() {
  cancelLocalRound();
  clearInterval(state.challengeTimer);
  clearInterval(state.messagePoll);
  clearInterval(state.notificationPoll);
  state.challengeTimer = state.messagePoll = state.notificationPoll = null;
  state.challengeAbort?.abort();
  state.challenge = null;
  state.challengeToken = null;
  state.threads = [];
  state.activeThread = null;
  state.messageAfter = 0;
  state.botMode = "idle";
  $("threadList").replaceChildren();
  $("messageLog").replaceChildren();
  $("messageInput").value = "";
  $("messageInput").style.height = "";
  $("conversationPanel").hidden = true;
  $("conversationEmpty").hidden = false;
  $("page-messages").classList.remove("conversation-open");
  $("page-community").replaceChildren();
  $("botLog").replaceChildren();
  $("botInput").value = "";
  $("roundPanel").hidden = true;
  document.body.classList.remove("round-active");
  $("appScreen").classList.remove("dm-open");
}
function botPrompt() {
  if (state.botMode === "idle")
    appendBot(
      tr(
        "اكتب «جمل متوسط» لبدء جولة مباشرة، أو «مساعدة» للأوامر.",
        "Type “sentences medium” to start, or “help” for commands.",
      ),
    );
}
function command(text) {
  return text.trim().toLocaleLowerCase();
}
function commandTokens(text) {
  return command(text)
    .replace(/[٠-٩]/g, (digit) => String("٠١٢٣٤٥٦٧٨٩".indexOf(digit)))
    .replace(/[۰-۹]/g, (digit) => String("۰۱۲۳۴۵۶۷۸۹".indexOf(digit)))
    .replace(/[،,]/g, " ")
    .split(/\s+/)
    .filter(Boolean);
}
const gameAliases = {
  sentences: "sentences",
  sentence: "sentences",
  words: "sentences",
  جمل: "sentences",
  جملة: "sentences",
  كلمات: "sentences",
  stories: "stories",
  story: "stories",
  قصة: "stories",
  قصص: "stories",
  news: "news",
  أخبار: "news",
  اخبار: "news",
  جريدة: "news",
  repeat: "repeat",
  تكرار: "repeat",
};
function findGame(tokens) {
  const index = tokens.findIndex((token) => gameAliases[token]);
  return index < 0 ? null : { game: gameAliases[tokens[index]], index };
}
function findLevel(tokens) {
  const aliases = {
    easy: "easy",
    سهل: "easy",
    medium: "medium",
    متوسط: "medium",
    hard: "hard",
    صعب: "hard",
  };
  const index = tokens.findIndex((token) => aliases[token]);
  return index < 0 ? null : { level: aliases[tokens[index]], index };
}
const topicAliases = {
  مختلط: "mixed", متنوع: "mixed", mixed: "mixed",
  علوم: "science", science: "science", طبيعة: "nature", الطبيعة: "nature", nature: "nature",
  تقنية: "technology", التقنية: "technology", technology: "technology",
  تاريخ: "history", التاريخ: "history", history: "history",
  فضاء: "space", الفضاء: "space", space: "space",
  صحة: "health", الصحة: "health", health: "health",
  سفر: "travel", السفر: "travel", travel: "travel",
  فنون: "arts", arts: "arts", رياضة: "sports", الرياضة: "sports", sports: "sports",
  تعليم: "education", التعليم: "education", education: "education",
  ثقافة: "culture", الثقافة: "culture", culture: "culture",
  طعام: "food", الطعام: "food", food: "food",
};
function findTopic(tokens) {
  const index = tokens.findIndex((token) => topicAliases[token]);
  return index < 0 ? null : { topic: topicAliases[tokens[index]], index };
}
function showBotHelp() {
  appendBot(
    tr(
      "اكتب اللعبة والمستوى والموضوع، مثل «جمل متوسط علوم» أو «تكرار متوسط ٥». الموضوعات: علوم، طبيعة، تقنية، تاريخ، فضاء، صحة، سفر، فنون، رياضة، تعليم، ثقافة، طعام، أو متنوع تلقائيًا. الأوامر: وقف، إحصائيات، مساعدة، إعدادات.",
      "Type a game, level and topic, e.g. “sentences medium science” or “repeat medium 5”. Topics include science, nature, technology, history, space, health, travel, arts, sports, education, culture, food, or auto-mixed. Commands: stop, stats, help, settings.",
    ),
  );
}
async function showStats() {
  try {
    const d = await api("/api/attempts");
    const a = d.attempts || [];
    const total = a.length;
    const avg = total
      ? (a.reduce((n, x) => n + (+x.wpm || 0), 0) / total).toFixed(1)
      : 0;
    appendBot(
      tr(
        `آخر ${total} جولة: متوسط السرعة ${avg} WPM، أفضل نتيجة ${Math.max(0, ...a.map((x) => +x.wpm || 0))} WPM. إجمالي النقاط ${state.user?.stats?.total_points || 0}.`,
        `Last ${total} rounds: average speed ${avg} WPM, best ${Math.max(0, ...a.map((x) => +x.wpm || 0))} WPM. Total points: ${state.user?.stats?.total_points || 0}.`,
      ),
    );
  } catch (e) {
    showError(e);
  }
}
async function startFlow(initialTokens = []) {
  if (state.challenge && state.challenge.status === "active") {
    appendBot(
      tr(
        "أنت داخل تحدٍّ نشط؛ أكمل الجولة أو انتظر نتيجته قبل التدريب المستمر.",
        "You are in an active challenge. Finish it or wait for results before continuous practice.",
      ),
    );
    return;
  }
  state.botMode = "choose-game";
  state.flow = {};
  if (!initialTokens.length)
    appendBot(
      tr(
        "اكتب نوع التدريب: جمل، قصة، أخبار، أو تكرار. مثال: جمل متوسط.",
        "Type a game: sentences, stories, news, or repeat. Example: sentences medium.",
      ),
    );
  if (initialTokens.length) await advanceBotFlow(initialTokens);
}
function startKeyListener() {
  $("botInput").addEventListener("input", () => {
    if (
      state.round &&
      !state.started &&
      !state.beginPromise &&
      $("botInput").value.length
    ) {
      beginCurrentRound().catch(() => {});
    }
  });
}
function bindKeyboardComposer(id) {
  const input = $(id);
  input.addEventListener("keydown", (event) => {
    if (id === "botInput" && state.round && event.key.length === 1 && !event.ctrlKey && !event.metaKey) {
      const typed = graphemes(input.value, state.round.language);
      const expected = graphemes(state.round.target || "", state.round.language);
      playTypingTone(expected[typed.length] === event.key.normalize("NFC"));
    }
    if (event.key !== "Enter" || event.shiftKey || event.isComposing) return;
    event.preventDefault();
    input.form.requestSubmit();
  });
  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
    if (id === "botInput" && state.round) renderTargetProgress(input.value);
  });
}
function playTypingTone(correct = true) {
  if (!state.soundEnabled) return;
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) return;
  try {
    const context = state.audioContext || (state.audioContext = new AudioContextClass());
    if (context.state === "suspended") context.resume().catch(() => {});
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    const now = context.currentTime;
    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(correct ? 720 : 300, now);
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.026, now + 0.008);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.055);
    oscillator.connect(gain);
    gain.connect(context.destination);
    oscillator.start(now);
    oscillator.stop(now + 0.06);
  } catch {}
}
function updateSoundButton() {
  const button = $("soundToggleButton");
  if (!button) return;
  button.setAttribute("aria-pressed", String(state.soundEnabled));
  button.textContent = state.soundEnabled
    ? tr("النغمة: مفعّلة", "Key sound: on")
    : tr("النغمة: صامتة", "Key sound: off");
}
function speakRoundText() {
  if (!state.round) return;
  if (!window.speechSynthesis || !window.SpeechSynthesisUtterance) {
    toast(tr("ميزة قراءة النص تعتمد على الأصوات المتاحة في جهازك.", "Speech playback depends on voices available on your device."));
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(state.round.target || "");
  utterance.lang = state.round.language === "ar" ? "ar-SA" : "en-US";
  utterance.rate = 0.9;
  const prefix = state.round.language === "ar" ? "ar" : "en";
  const voice = window.speechSynthesis.getVoices().find((item) => item.lang.toLowerCase().startsWith(prefix));
  if (voice) utterance.voice = voice;
  window.speechSynthesis.speak(utterance);
}
bindKeyboardComposer("botInput");
bindKeyboardComposer("messageInput");
async function advanceBotFlow(tokens) {
  if (state.botMode === "choose-game") {
    const selected = findGame(tokens);
    if (!selected) {
      appendBot(
        tr("اكتب: جمل، قصة، أخبار، أو تكرار.", "Type: sentences, stories, news, or repeat."),
      );
      return;
    }
    state.flow.game = selected.game;
    state.botMode = "choose-level";
    const remaining = tokens.slice(selected.index + 1);
    if (remaining.length)
      await advanceBotFlow(remaining);
    else
      appendBot(tr("اكتب المستوى: سهل، متوسط، أو صعب.", "Type a level: easy, medium, or hard."));
    return;
  }
  if (state.botMode === "choose-level") {
    const selected = findLevel(tokens);
    if (!selected) {
      appendBot(tr("اكتب المستوى: سهل، متوسط، أو صعب.", "Type: easy, medium, or hard."));
      return;
    }
    state.flow.difficulty = selected.level;
    const remaining = tokens.slice(selected.index + 1);
    const selectedTopic = findTopic(remaining);
    state.flow.topic = selectedTopic?.topic || "mixed";
    if (state.flow.game === "repeat") {
      state.botMode = "choose-count";
      if (remaining.length) await advanceBotFlow(remaining);
      else appendBot(tr("كم كلمة؟ اكتب رقمًا من 1 إلى 20.", "How many words? Type a number from 1 to 20."));
    } else {
      await createPracticeRound();
    }
    return;
  }
  if (state.botMode === "choose-count") {
    const count = tokens.map(Number).find((value) => Number.isInteger(value) && value >= 1 && value <= 20);
    if (!count) {
      appendBot(tr("اكتب رقمًا من 1 إلى 20.", "Type a number from 1 to 20."));
      return;
    }
    state.flow.count = count;
    await createPracticeRound(count);
  }
}
async function createPracticeRound(count) {
  const continuing = state.botMode === "between";
  const token = ++state.roundToken;
  state.roundAbort?.abort();
  const controller = new AbortController();
  state.roundAbort = controller;
  state.botMode = "loading";
  try {
    const body = {
      game: state.flow.game,
      difficulty: state.flow.difficulty,
      language: state.lang,
      topic: state.flow.topic || "mixed",
    };
    if (body.game === "repeat")
      body.count = Number(count || state.flow.count || 1);
    const d = await api("/api/rounds", {
      method: "POST",
      body,
      signal: controller.signal,
    });
    if (token !== state.roundToken || controller.signal.aborted) return;
    state.round = d.round;
    if (state.stopAfterCurrent) {
      state.stopAfterCurrent = false;
      await stopBot({ silent: true });
      return;
    }
    state.started = false;
    state.beginPromise = null;
    state.challengeRoundSubmitted = false;
    state.botMode = "playing";
    renderRound();
    if (!continuing) $("botInput").focus({ preventScroll: true });
  } catch (e) {
    if (e.name !== "AbortError" && token === state.roundToken) {
      state.botMode = "idle";
      state.stopAfterCurrent = false;
      $("roundPanel").hidden = true;
      showError(e);
    }
  }
}
function renderRound() {
  const r = state.round;
  if (!r) return;
  $("roundPanel").hidden = false;
  $("targetText").classList.toggle("repeat-target", r.game === "repeat");
  $("targetText").dir = r.game === "repeat" ? "ltr" : "auto";
  renderTargetProgress("");
  const topic = labels.topics[r.topic] || labels.topics.mixed;
  $("roundLabel").textContent = `${tr(...(labels.games[r.game] || ["تدريب", "Practice"]))} · ${tr(...(labels.levels[r.difficulty] || ["متوسط", "Medium"]))} · ${tr(...topic)}`;
  $("roundCounter").textContent = r.challenge_id
    ? tr(`الجولة ${r.round_number || 1}/${r.round_count || 1}`, `Round ${r.round_number || 1}/${r.round_count || 1}`)
    : r.game === "repeat"
      ? `${r.word_count || state.flow.count || 1} ${tr("كلمة", "word(s)")} · 3×`
      : "";
  $("roundHint").textContent = r.game === "repeat"
    ? tr("اكتب كل كلمة ثلاث مرات بمسافة بين الكلمات، دون الأقواس والرقم.", "Type each word three times, separated by spaces; omit parentheses and the number.")
    : tr("اكتب النص كما يظهر؛ المسافات وعلامات الترقيم محسوبة.", "Type the text as shown; spaces and punctuation count.");
  $("roundState").textContent = tr("بانتظار أول حرف", "Waiting for first key");
  $("liveSpeed").textContent = "0 WPM";
  $("liveAccuracy").textContent = "100%";
  $("botInput").value = "";
  $("botInput").style.height = "auto";
  $("botInput").placeholder = tr("اكتب إجابتك…", "Type your answer…");
  updateSoundButton();
  window.speechSynthesis?.cancel();
  document.body.classList.add("round-active");
}
function graphemes(value, language = state.lang) {
  if (typeof Intl.Segmenter === "function") {
    return Array.from(
      new Intl.Segmenter(language, { granularity: "grapheme" }).segment(value),
      (part) => part.segment,
    );
  }
  return Array.from(value);
}
function renderTargetProgress(typedText = "") {
  const round = state.round;
  const host = $("targetText");
  if (!round || !host) return;
  host.replaceChildren();
  if (round.game === "repeat") {
    host.textContent = round.display || round.target || "";
    host.setAttribute("aria-label", host.textContent);
    return;
  }
  const expected = graphemes(round.target || "", round.language);
  const typed = graphemes(typedText || "", round.language);
  host.setAttribute("aria-label", round.target || "");
  const fragment = document.createDocumentFragment();
  expected.forEach((character, index) => {
    const span = document.createElement("span");
    span.className = "target-char";
    span.setAttribute("aria-hidden", "true");
    if (index < typed.length) span.classList.add(typed[index] === character ? "is-correct" : "is-error");
    else if (index === typed.length) span.classList.add("is-current");
    span.textContent = character;
    fragment.append(span);
  });
  typed.slice(expected.length).forEach((character) => {
    const span = document.createElement("span");
    span.className = "target-char is-error is-extra";
    span.setAttribute("aria-hidden", "true");
    span.textContent = character;
    fragment.append(span);
  });
  host.append(fragment);
}
function scoreLiveText(expectedText, typedText) {
  const expected = graphemes((expectedText || "").normalize("NFC"));
  const typed = graphemes((typedText || "").normalize("NFC"));
  const n = expected.length;
  const m = typed.length;
  const width = m + 1;
  const expectedLetters = expected.map((cluster) => /[\p{L}\p{N}]/u.test(cluster));
  const typedLetters = typed.map((cluster) => /[\p{L}\p{N}]/u.test(cluster));
  const trace = new Uint8Array((n + 1) * width);
  let previous = new Uint16Array(width);
  let current = new Uint16Array(width);
  for (let j = 1; j <= m; j++) {
    previous[j] = previous[j - 1] + (typedLetters[j - 1] ? 2 : 1);
    trace[j] = 3;
  }
  for (let i = 1; i <= n; i++) {
    const expectedCost = expectedLetters[i - 1] ? 2 : 1;
    current[0] = previous[0] + expectedCost;
    trace[i * width] = 2;
    for (let j = 1; j <= m; j++) {
      const same = expected[i - 1] === typed[j - 1];
      const diagonal =
        previous[j - 1] +
        (same ? 0 : expectedLetters[i - 1] || typedLetters[j - 1] ? 2 : 1);
      const deletion = previous[j] + expectedCost;
      const insertion = current[j - 1] + (typedLetters[j - 1] ? 2 : 1);
      const best = Math.min(diagonal, deletion, insertion);
      current[j] = best;
      const index = i * width + j;
      trace[index] =
        diagonal === best ? (same ? 0 : 1) : deletion === best ? 2 : 3;
    }
    [previous, current] = [current, previous];
  }
  let correctCharacters = 0;
  let i = n;
  let j = m;
  while (i || j) {
    const action = trace[i * width + j];
    if (action === 0) {
      correctCharacters++;
      i--;
      j--;
    } else if (action === 1) {
      i--;
      j--;
    } else if (action === 2) {
      i--;
    } else {
      j--;
    }
  }
  const length = Math.max(n, m);
  return {
    correctCharacters,
    accuracy: length ? (100 * correctCharacters) / length : 100,
  };
}
function beginCurrentRound() {
  if (!state.round || state.started)
    return state.beginPromise || Promise.resolve();
  state.started = true;
  $("roundState").textContent = tr("الجولة جارية", "Round in progress");
  const id = state.round.id,
    token = state.roundToken;
  state.beginPromise = api(`/api/rounds/${encodeURIComponent(id)}/begin`, {
    method: "POST",
    body: {},
    signal: state.roundAbort?.signal,
  })
    .then((x) => {
      if (token !== state.roundToken) return x;
      state.roundStartedAt = Date.now();
      state.elapsedTimer = setInterval(() => {
        if (!state.round || token !== state.roundToken) return;
        const sec = Math.max(1, (Date.now() - state.roundStartedAt) / 1000),
          txt = $("botInput").value;
        const score = scoreLiveText(state.round.target || "", txt),
          wpm = score.correctCharacters / 5 / (sec / 60);
        $("liveSpeed").textContent = `${wpm.toFixed(1)} WPM`;
        $("liveAccuracy").textContent = `${score.accuracy.toFixed(1)}%`;
      }, 500);
      return x;
    })
    .catch((e) => {
      if (token === state.roundToken) {
        state.started = false;
        state.beginPromise = null;
        if (e.name !== "AbortError") showError(e);
      }
      throw e;
    });
  return state.beginPromise;
}
function validateImage(file) {
  return (
    !!file &&
    ["image/jpeg", "image/png", "image/webp"].includes(file.type) &&
    file.size <= 2 * 1024 * 1024
  );
}
async function submitPractice(text, userMessage) {
  const r = state.round;
  if (!r) return;
  state.botMode = "submitting";
  const token = state.roundToken;
  try {
    await beginCurrentRound();
    if (token !== state.roundToken || !state.round) return;
    const controller = state.roundAbort;
    const d = await api(`/api/rounds/${encodeURIComponent(r.id)}/submit`, {
      method: "POST",
      body: { text },
      signal: controller?.signal,
    });
    if (token !== state.roundToken) return;
    clearRoundTimers();
    if (r.challenge_id) {
      state.challengeSubmittedRound = Number(r.round_number || state.challengeSubmittedRound || 1);
      state.challengeRoundSubmitted = true;
    }
    state.round = null;
    $("roundPanel").hidden = true;
    document.body.classList.remove("round-active");
    state.started = false;
    state.beginPromise = null;
    state.user.stats = d.stats || d.result.stats || state.user.stats;
    renderResult(d.result, userMessage);
    if (state.challenge && state.challenge.status === "active") {
      state.botMode = "challenge-wait";
      $("roundPanel").hidden = true;
      appendBot(
        tr(
          "أُرسلت نتيجتك. ننتظر بقية المشاركين…",
          "Your result is submitted. Waiting for the other players…",
        ),
      );
      pollChallenge(true);
    } else if (state.stopAfterCurrent) {
      await stopBot({ silent: true });
      return;
    } else {
      state.botMode = "between";
      state.nextTimer = setTimeout(() => {
        if (token === state.roundToken && state.botMode === "between")
          createPracticeRound();
      }, 220);
    }
  } catch (e) {
    if (e.name !== "AbortError" && token === state.roundToken) {
      state.botMode = "playing";
      state.stopAfterCurrent = false;
      if (!$("botInput").value) $("botInput").value = text;
      showError(e);
    }
  }
}
function renderResult(result, userMessage) {
  const formatNumber = (value) =>
    Number.isFinite(Number(value)) ? Number(value).toFixed(1) : "0.0";
  if (!userMessage) return;
  const strip = document.createElement("div");
  strip.className = "result-strip";
  strip.setAttribute("aria-label", tr("نتيجة الجولة", "Round result"));
  strip.innerHTML = `<span><bdi dir="ltr">${formatNumber(result.wpm)} WPM</bdi></span><span><bdi dir="ltr">${formatNumber(result.accuracy)}%</bdi> ${tr("دقة", "accuracy")}</span><span><bdi dir="ltr">+${esc(result.points || 0)}</bdi> ${tr("مضافة", "earned")}</span><span><bdi dir="ltr">−${esc(result.penalty || 0)}</bdi> ${tr("خصم", "penalty")}</span>`;
  userMessage.insertBefore(strip, userMessage.firstChild);
}
async function stopBot({ silent = false } = {}) {
  if (state.challenge?.status === "active" && state.round?.challenge_id) {
    if (!silent)
      appendBot(
        tr(
          "الجولة جزء من تحدٍّ نشط ولا يمكن إلغاؤها بإيقاف التدريب. المضيف وحده يستطيع إلغاء التحدي صراحةً.",
          "This round belongs to an active challenge and cannot be cancelled by stopping practice. Only the host can explicitly cancel the challenge.",
        ),
      );
    return;
  }
  const r = state.round;
  if (r) {
    state.botMode = "stopping";
    try {
      await api(`/api/rounds/${encodeURIComponent(r.id)}/cancel`, {
        method: "POST",
        body: {},
      });
    } catch (e) {
      if (e.status === 401) return;
      state.botMode = "playing";
      if ($("roundPanel").hidden) renderRound();
      if (silent)
        toast(
          tr(
            "تعذّر إيقاف الجولة. ما زالت مفتوحة؛ أعد كتابة «وقف».",
            "Could not cancel the round. It is still open; type “stop” to retry.",
          ),
        );
      else showError(e);
      return;
    }
  }
  cancelLocalRound();
  state.botMode = "idle";
  $("roundPanel").hidden = true;
  document.body.classList.remove("round-active");
  $("botInput").placeholder = tr("اكتب أمرًا…", "Type a command…");
  $("botInput").value = "";
  $("botInput").style.height = "";
  if (!silent)
    appendBot(
      tr(
        "تم إيقاف التدريب. اكتب «ابدأ» متى أردت المتابعة.",
        "Practice stopped. Type “start” whenever you want to continue.",
      ),
    );
}
async function handleBotSubmit(e) {
  e.preventDefault();
  const input = $("botInput");
  const text = input.value;
  const tokens = commandTokens(text);
  const cmd = tokens[0] || "";
  const exactCommand = tokens.length === 1;
  const stopCommand = exactCommand && ["وقف", "stop"].includes(cmd);
  if (state.botMode === "stopping") return;
  if (["submitting", "loading"].includes(state.botMode)) {
    if (stopCommand) {
      input.value = "";
      input.style.height = "";
      appendBot(text, "user");
      if (
        state.botMode === "submitting" &&
        state.challenge?.status === "active" &&
        state.round?.challenge_id
      ) {
        toast(
          tr(
            "لا يمكن إيقاف جولة التحدي أثناء إرسالها.",
            "A challenge round cannot be stopped while its result is submitting.",
          ),
        );
      } else {
        state.stopAfterCurrent = true;
        toast(
          tr(
            "سيُوقف التدريب بعد اكتمال الخطوة الحالية.",
            "Practice will stop after the current step completes.",
          ),
        );
      }
    }
    return;
  }
  if (state.botMode === "between" && !stopCommand)
    return;
  input.value = "";
  input.style.height = "";
  if (!text.trim()) return;
  const userMessage = appendBot(text, "user");
  if (exactCommand && ["وقف", "stop"].includes(cmd)) {
    await stopBot();
    return;
  }
  if (exactCommand && ["مساعدة", "help", "?"].includes(cmd)) {
    showBotHelp();
    return;
  }
  if (exactCommand && ["إحصائيات", "احصائيات", "stats"].includes(cmd)) {
    showStats();
    return;
  }
  if (exactCommand && ["إعدادات", "اعدادات", "settings"].includes(cmd)) {
    setPage("settings");
    return;
  }
  if (
    ["ابدأ", "ابدا", "start"].includes(cmd) &&
    (!state.round || exactCommand)
  ) {
    if (state.round) {
      appendBot(
        tr("هناك جولة قيد التشغيل بالفعل.", "A round is already in progress."),
      );
      return;
    }
    await startFlow(tokens.slice(1));
    return;
  }
  if (!state.round && state.botMode === "idle" && findGame(tokens)) {
    await startFlow(tokens);
    return;
  }
  if (["choose-game", "choose-level", "choose-count"].includes(state.botMode)) {
    await advanceBotFlow(tokens);
    return;
  }
  if (state.round) {
    await submitPractice(text, userMessage);
    return;
  }
  appendBot(
    tr(
      "لم أفهم الأمر. اكتب «مساعدة» لعرض الخيارات أو «ابدأ» للتدريب.",
      "I did not recognize that command. Type “help” or “start”.",
    ),
  );
}
$("botForm").addEventListener("submit", handleBotSubmit);
startKeyListener();
function renderCommunity() {
  const el = $("page-community");
  if (el.innerHTML) return;
  el.innerHTML = `<header class="page-header"><div><p class="eyebrow">${tr("تواصل وتحدَّ", "Connect & compete")}</p><h1>${tr("المجتمع", "Community")}</h1><p class="muted">${tr("ابحث عن مستخدمين، تابع الترتيب، وشارك في تحديات بجولات وحكم وإحصاءات واضحة.", "Find users, check rankings, and join multi-round challenges with clear judging and stats.")}</p></div></header><section class="card section-gap"><div class="section-heading"><h2>${tr("ابحث عن مستخدم", "Find a user")}</h2></div><label class="search-field"><span class="muted">@</span><input id="communitySearch" type="search" maxlength="24" autocomplete="off" placeholder="${tr("اسم المستخدم", "Username")}"></label><div id="searchResults" class="list"></div></section><section class="card section-gap"><div class="section-heading"><h2>${tr("لوحة المتصدرين", "Leaderboard")}</h2><div class="segmented"><button type="button" data-sort="points" class="${state.communitySort === "points" ? "active" : ""}">${tr("النقاط", "Points")}</button><button type="button" data-sort="wpm" class="${state.communitySort === "wpm" ? "active" : ""}">${tr("السرعة", "Speed")}</button></div></div><div id="leaderboard" class="list"></div></section><section class="section-gap"><div class="section-heading"><div><p class="eyebrow">${tr("فعاليات أسبوعية", "Weekly events")}</p><h2>${tr("أنماط التحدي", "Challenge formats")}</h2><p class="muted">${tr("كل فعالية لها مضيف، مشاركون، جولات، وحكم آلي قابل للاختيار.", "Every event has a host, participants, rounds, and a selectable automatic judge.")}</p></div><button class="primary-button" type="button" data-action="create-challenge">${tr("إعداد تحدٍّ", "Configure challenge")}</button></div><div class="challenge-presets"><button class="action-card" type="button" data-action="create-preset" data-preset="speed"><strong>${tr("سباق السرعة", "Speed sprint")}</strong><span class="muted">${tr("جولتان · السرعة أولًا", "2 rounds · speed first")}</span></button><button class="action-card" type="button" data-action="create-preset" data-preset="accuracy"><strong>${tr("كأس الدقة", "Accuracy cup")}</strong><span class="muted">${tr("3 جولات · الدقة أولًا", "3 rounds · accuracy first")}</span></button><button class="action-card" type="button" data-action="create-preset" data-preset="marathon"><strong>${tr("ماراثون الأخطاء الأقل", "Few-error marathon")}</strong><span class="muted">${tr("5 جولات · الأخطاء الأقل أولًا", "5 rounds · fewest errors first")}</span></button><button class="action-card event-preset" type="button" data-action="create-friday"><strong>${tr("فعالية الجمعة", "Friday event")}</strong><span class="muted">${tr("جدولة للجمعة القادمة · 8 مساءً السعودية", "Next Friday · 8 PM Saudi time")}</span></button></div><section class="card challenge-list-card"><div class="section-heading"><div><h2>${tr("الفعاليات والتحديات العامة", "Public events and challenges")}</h2><p class="muted">${tr("تظهر هنا الردهة والفعاليات النشطة ونتائج الأسبوع الأخير.", "Open lobbies, active events, and the past week's results appear here.")}</p></div></div><div id="challengePanel"></div></section></section><div id="challengeInvite"></div>`;
}
async function loadCommunity() {
  renderCommunity();
  loadLeaderboard();
  loadPublicChallenges();
}
async function loadLeaderboard() {
  const host = $("leaderboard");
  if (!host) return;
  try {
    const d = await api("/api/leaderboard?sort=" + state.communitySort);
    host.innerHTML =
      (d.users || [])
        .map(
          (u, i) =>
            `<button class="leaderboard-row" data-action="profile" data-username="${esc(u.username)}"><span class="rank-number">${i + 1}</span>${avatar(u.avatar_url, u.display_name)}<span class="user-copy"><strong>${who(u)}</strong><small>@${esc(u.username)}</small></span><span class="pill">${state.communitySort === "wpm" ? `${esc(u.stats?.best_wpm || 0)} WPM` : esc(u.stats?.total_points || 0)}</span></button>`,
        )
        .join("") ||
      `<p class="empty-state">${tr("لا توجد نتائج مؤهلة بعد.", "No eligible results yet.")}</p>`;
  } catch (e) {
    if (e.status !== 401)
      host.innerHTML = `<p class="form-error">${esc(errorText(e))}</p>`;
  }
}
async function searchUsers(q) {
  const host = $("searchResults");
  if (!host) return;
  if (!q.trim()) {
    host.replaceChildren();
    return;
  }
  try {
    const d = await api("/api/users/search?q=" + encodeURIComponent(q.trim()));
    host.innerHTML =
      (d.users || [])
        .map(
          (u) =>
            `<button class="user-row" data-action="profile" data-username="${esc(u.username)}">${avatar(u.avatar_url, u.display_name)}<span class="user-copy"><strong>${who(u)}</strong><small>@${esc(u.username)}</small></span><span class="text-link">${tr("عرض", "View")}</span></button>`,
        )
        .join("") ||
      `<p class="empty-state">${tr("لا يوجد مستخدمون بهذا الاسم.", "No users found.")}</p>`;
  } catch (e) {
    if (e.status !== 401)
      host.innerHTML = `<p class="form-error">${esc(errorText(e))}</p>`;
  }
}
async function loadPublicChallenges() {
  const host = $("challengePanel");
  if (!host) return;
  if (state.pendingInvite && !state.challenge) {
    host.innerHTML = `<article class="challenge-card"><h2>${tr("دعوة تحدٍّ خاص", "Private challenge invitation")}</h2><p>${tr("اضغط للانضمام إلى الردهة. لن يتم الانضمام تلقائيًا.", "Press to join the lobby. You will not be joined automatically.")}</p><button class="primary-button" data-action="challenge-join" data-token="${esc(state.pendingInvite)}">${tr("انضم إلى التحدي", "Join challenge")}</button></article>`;
    return;
  }
  try {
    const d = await api("/api/challenges");
    const html = (d.challenges || [])
      .map((c) => challengeCard(c, false))
      .join("");
    host.innerHTML =
      html ||
      `<p class="empty-state">${tr("لا توجد فعاليات أو نتائج عامة حديثة الآن.", "No public events or recent results right now.")}</p>`;
  } catch (e) {
    if (e.status !== 401)
      host.innerHTML = `<p class="form-error">${esc(errorText(e))}</p>`;
  }
}
function challengeCard(c, detail = true) {
  const me = c.owner?.id === state.user?.id;
  const mine = (c.participants || []).some((p) => p.user?.id === state.user?.id);
  const member = (c.participants || []).map((p) => {
    const result = p.result;
    const summary = result
      ? `<div class="participant-stats"><span><bdi dir="ltr">${esc(result.wpm)} WPM</bdi></span><span><bdi dir="ltr">${esc(result.accuracy)}%</bdi></span><span>${tr("النقاط", "Points")}: ${esc(result.points)}</span><span>${tr("الأخطاء", "Errors")}: ${esc(result["error_count"])}</span><span>${tr("الجولات", "Rounds")}: ${esc(result.rounds_completed)}/${esc(c.round_count || 1)}</span></div>`
      : `<small class="muted">${tr("لم يرسل نتيجة بعد", "No result yet")}</small>`;
    const rounds = (p.round_results || []).map((round) =>
      `<span class="round-result-chip">${tr("ج", "R")}${esc(round.round)}: <bdi dir="ltr">${esc(round.wpm)} WPM</bdi> · ${esc(round.accuracy)}% · ${tr("أخطاء", "err")}: ${esc(round.error_count)}</span>`,
    ).join("");
    return `<div class="challenge-player"><div class="player-row">${avatar(p.user?.avatar_url, p.user?.display_name)}<span class="player-name">${who(p.user)}${p.judge ? ` · ${tr("المضيف", "Host")}` : ""}${p.finished ? ` · ${tr("أنهى الجولة", "round done")}` : ""}</span></div>${summary}${rounds ? `<div class="round-result-list">${rounds}</div>` : ""}</div>`;
  }).join("");
  const controls = [];
  if (c.status === "lobby" && !mine && c.token)
    controls.push(`<button class="primary-button" data-action="challenge-join" data-token="${esc(c.token)}">${tr("انضمام", "Join")}</button>`);
  if (c.status === "lobby" && me)
    controls.push(`<button class="primary-button" data-action="challenge-start" data-token="${esc(c.token || state.challengeToken)}" ${c.participants?.length < 2 ? "disabled" : ""}>${tr("ابدأ التحدي", "Start challenge")}</button>`);
  if (["lobby", "active"].includes(c.status) && me)
    controls.push(`<button class="danger-button" data-action="challenge-cancel" data-token="${esc(c.token || state.challengeToken)}">${tr("إلغاء التحدي", "Cancel challenge")}</button>`);
  if (c.status === "lobby" && me && c.visibility === "private" && c.token)
    controls.push(`<button class="secondary-button" data-action="copy-invite" data-token="${esc(c.token)}">${tr("نسخ رابط الدعوة", "Copy invite link")}</button>`);
  const winnerList = c.winners?.length ? c.winners : c.winner ? [c.winner] : [];
  const winner = c.status === "complete"
    ? c.draw
      ? `<div class="winner-card">${tr("تعادل: ", "Draw: ")}${winnerList.map(who).join(" · ")}</div>`
      : winnerList.length
        ? `<div class="winner-card">${tr("الفائز: ", "Winner: ")}${who(winnerList[0])}</div>`
        : `<div class="winner-card">${tr("لا توجد نتيجة مؤهلة للفوز.", "No eligible result for a winner.")}</div>`
    : "";
  const dateValue = c.scheduled_at || c.starts_at;
  const dateText = dateValue
    ? new Intl.DateTimeFormat(state.lang === "ar" ? "ar-SA" : "en", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Riyadh" }).format(new Date(dateValue))
    : tr("بانتظار بدء المضيف", "Waiting for host to start");
  const eventLabel = c.event_kind === "friday" ? tr("فعالية الجمعة", "Friday event") : tr("تحدٍّ", "Challenge");
  const judgeLabels = { points: tr("النقاط", "Points"), speed: tr("السرعة", "Speed"), accuracy: tr("الدقة", "Accuracy"), fewest_errors: tr("الأخطاء الأقل", "Fewest errors") };
  const topic = labels.topics[c.topic] || labels.topics.mixed;
  const roundText = c.status === "active"
    ? tr(`الجولة ${c.current_round || 1}/${c.round_count || 1}`, `Round ${c.current_round || 1}/${c.round_count || 1}`)
    : tr(`${c.round_count || 1} جولات`, `${c.round_count || 1} rounds`);
  return `<article class="challenge-card"><div class="section-heading"><div><span class="eyebrow">${eventLabel}</span><strong>${esc(c.owner?.display_name || c.owner?.username || tr("تحدٍّ", "Challenge"))}</strong><p class="muted">${tr(...(labels.games[c.game] || ["تدريب", "Practice"]))} · ${tr(...(labels.levels[c.difficulty] || ["متوسط", "Medium"]))} · ${tr(...topic)} · ${c.visibility === "private" ? tr("خاص", "Private") : tr("عام", "Public")}</p></div><span class="pill">${esc(c.status)}</span></div><p class="muted">${roundText} · ${tr("الحكم الآلي", "Automatic judge")}: ${esc(judgeLabels[c.judge_mode] || judgeLabels.points)} · ${tr("الموعد", "Time")}: ${esc(dateText)} · ${tr("المشاركون", "Players")}: ${c.participants?.length || 0}/${c.max_players}</p><div class="challenge-player-list">${member}</div>${winner}<div class="wrap">${controls.join("")}</div></article>`;
}
function showChallengeDetail(c) {
  if (c.status === "active" && c.round && Number(c.round.round_number || 1) > state.challengeSubmittedRound)
    state.challengeRoundSubmitted = false;
  state.challenge = c;
  const host = $("challengePanel");
  if (host) host.innerHTML = challengeCard(c, true);
  if (c.status === "active" && c.round && !state.challengeRoundSubmitted) {
    state.round = c.round;
    state.roundToken++;
    state.botMode = "challenge";
    renderRound();
    appendBot(
      tr(
        "التحدي يبدأ بعد العد التنازلي الظاهر. استعد…",
        "The challenge starts after the countdown. Get ready…",
      ),
    );
    startChallengeCountdown(c);
    setPage("bot");
  } else if (c.status === "complete") {
    const msg = c.winner
      ? tr(
          `الفائز: ${c.winner.display_name || c.winner.username}`,
          `Winner: ${c.winner.display_name || c.winner.username}`,
        )
      : tr(
          "انتهى التحدي دون نتيجة مؤهلة.",
          "Challenge ended without an eligible result.",
        );
    if (!state._lastWinner || state._lastWinner !== c.id) {
      state._lastWinner = c.id;
      appendBot(msg);
    }
    state.challenge = null;
    state.challengeRoundSubmitted = false;
    state.challengeToken = null;
    clearInterval(state.challengeTimer);
    clearInterval(state.botLiveTimer);
    if (state.page === "community") loadPublicChallenges();
  } else if (c.status === "cancelled" || c.status === "expired") {
    toast(tr("أُغلق التحدي.", "Challenge is closed."));
    state.challenge = null;
    state.challengeToken = null;
    clearInterval(state.challengeTimer);
    clearInterval(state.botLiveTimer);
  }
}
function startChallengeCountdown(c) {
  clearInterval(state.botLiveTimer);
  state.challengeOffset = c.server_now
    ? Date.parse(c.server_now) - Date.now()
    : 0;
  const tick = () => {
    const diff = Math.max(
      0,
      (Date.parse(c.starts_at || "") - (Date.now() + state.challengeOffset)) /
        1000,
    );
    $("roundState").textContent =
      diff > 0
        ? tr(`يبدأ خلال ${Math.ceil(diff)} ث`, `Starts in ${Math.ceil(diff)}s`)
        : tr("ابدأ الكتابة!", "Start typing!");
  };
  tick();
  state.botLiveTimer = setInterval(tick, 250);
}
async function loadInvite(token) {
  state.challengeToken = token;
  state.pendingInvite = token;
  setPage("community");
}
async function renderChallengePanel() {
  if (!state.challengeToken) return;
  if (state.pendingInvite && !state.challenge) {
    loadPublicChallenges();
    return;
  }
  try {
    const d = await api(
      `/api/challenges/${encodeURIComponent(state.challengeToken)}`,
    );
    showChallengeDetail(d.challenge);
  } catch (e) {
    if (e.status !== 401) showError(e);
  }
}
async function pollChallenge(force = false) {
  if (
    !state.challengeToken ||
    (state.pendingInvite && !state.challenge) ||
    document.hidden ||
    (!force && state.page !== "community" && state.page !== "bot")
  )
    return;
  try {
    const d = await api(
      `/api/challenges/${encodeURIComponent(state.challengeToken)}`,
    );
    const c = d.challenge;
    const prior = state.challenge?.status;
    if (c.status === "active" && c.round && Number(c.round.round_number || 1) > state.challengeSubmittedRound)
      state.challengeRoundSubmitted = false;
    state.challenge = c;
    if (state.page === "community") {
      const host = $("challengePanel");
      if (host) host.innerHTML = challengeCard(c, true);
    }
    if (c.status !== prior || c.status === "active") {
      if (
        c.status === "active" &&
        c.round &&
        !state.challengeRoundSubmitted &&
        !state.round
      ) {
        state.round = c.round;
        state.roundToken++;
        state.botMode = "challenge";
        renderRound();
        startChallengeCountdown(c);
        setPage("bot");
      }
      if (
        c.status === "complete" ||
        c.status === "cancelled" ||
        c.status === "expired"
      )
        showChallengeDetail(c);
    }
  } catch (e) {
    if ([403, 404].includes(e.status)) {
      clearInterval(state.challengeTimer);
      state.challengeTimer = null;
      if (e.status === 403) showError(e);
      else if (state.page === "community")
        toast(tr("لم يعد التحدي متاحًا.", "Challenge is no longer available."));
    } else if (e.status !== 401) console.warn("challenge poll", e);
  }
}
function startChallengePolling() {
  clearInterval(state.challengeTimer);
  state.challengeTimer = setInterval(() => {
    if (state.challengeToken && !state.pendingInvite) pollChallenge();
    else if (state.page === "community" && !document.hidden)
      loadPublicChallenges();
  }, 2000);
}
const challengePresets = {
  speed: { game: "sentences", difficulty: "medium", visibility: "public", round_count: 2, judge_mode: "speed", topic: "mixed", event_kind: "challenge" },
  accuracy: { game: "stories", difficulty: "medium", visibility: "public", round_count: 3, judge_mode: "accuracy", topic: "science", event_kind: "challenge" },
  marathon: { game: "news", difficulty: "hard", visibility: "public", round_count: 5, judge_mode: "fewest_errors", topic: "culture", event_kind: "challenge" },
  friday: { game: "stories", difficulty: "medium", visibility: "public", round_count: 3, judge_mode: "points", topic: "mixed", event_kind: "friday" },
};
async function createChallengeForm(preset = {}, opponentUsername = "") {
  const direct = Boolean(opponentUsername);
  const defaults = { game: "sentences", difficulty: "medium", visibility: direct ? "private" : "private", max_players: direct ? 2 : 2, round_count: direct ? 3 : 1, judge_mode: "points", topic: "mixed", event_kind: "challenge", ...preset };
  if (direct) Object.assign(defaults, { visibility: "private", max_players: 2, event_kind: "challenge" });
  const games = Object.keys(labels.games);
  const levels = Object.keys(labels.levels);
  const topics = Object.keys(labels.topics);
  const judgeModes = ["points", "speed", "accuracy", "fewest_errors"];
  openModal(
    direct ? `${tr("تحدٍّ خاص مع", "Private challenge with")} @${esc(opponentUsername)}` : defaults.event_kind === "friday" ? tr("إعداد فعالية الجمعة", "Set up Friday event") : tr("إنشاء تحدٍّ", "Create a challenge"),
    `<form class="stack-form challenge-form" data-form="create-challenge" data-opponent="${esc(opponentUsername)}"><label>${tr("اللعبة", "Game")}<select name="game">${games.map((g) => `<option value="${g}" ${defaults.game === g ? "selected" : ""}>${tr(...labels.games[g])}</option>`).join("")}</select></label><label>${tr("المستوى", "Difficulty")}<select name="difficulty">${levels.map((level) => `<option value="${level}" ${defaults.difficulty === level ? "selected" : ""}>${tr(...labels.levels[level])}</option>`).join("")}</select></label><label data-topic-label>${tr("موضوع النص", "Text topic")}<select name="topic">${topics.map((topic) => `<option value="${topic}" ${defaults.topic === topic ? "selected" : ""}>${tr(...labels.topics[topic])}</option>`).join("")}</select></label><label data-repeat-label hidden>${tr("عدد الكلمات (1–20)", "Word count (1–20)")}<input name="count" type="number" min="1" max="20" value="3"></label><label>${tr("عدد الجولات (1–10)", "Rounds (1–10)")}<input name="round_count" type="number" min="1" max="10" value="${defaults.round_count}" required></label><label>${tr("طريقة الحكم الآلي", "Automatic judging")}<select name="judge_mode">${judgeModes.map((mode) => `<option value="${mode}" ${defaults.judge_mode === mode ? "selected" : ""}>${mode === "fewest_errors" ? tr("الأخطاء الأقل ثم الدقة", "Fewest errors, then accuracy") : mode === "accuracy" ? tr("الدقة أولًا", "Accuracy first") : mode === "speed" ? tr("السرعة أولًا", "Speed first") : tr("النقاط ثم الدقة والسرعة", "Points, then accuracy and speed")}</option>`).join("")}</select></label><label data-event-label>${tr("نوع الفعالية", "Event type")}<select name="event_kind"><option value="challenge" ${defaults.event_kind === "challenge" ? "selected" : ""}>${tr("تحدٍّ عادي", "Regular challenge")}</option><option value="friday" ${defaults.event_kind === "friday" ? "selected" : ""}>${tr("فعالية الجمعة القادمة · 8 مساءً السعودية", "Next Friday · 8 PM Saudi time")}</option></select></label><label data-visibility-label>${tr("نوع التحدي", "Visibility")}<select name="visibility"><option value="private" ${defaults.visibility === "private" ? "selected" : ""}>${tr("خاص (رابط دعوة)", "Private (invite link)")}</option><option value="public" ${defaults.visibility === "public" ? "selected" : ""}>${tr("عام (يظهر للمجتمع)", "Public (visible to community)")}</option></select></label><label data-maxplayers-label>${tr("الحد الأقصى للمشاركين (2–8)", "Maximum participants (2–8)")}<input name="max_players" type="number" min="2" max="8" value="${defaults.max_players}" required></label><p class="field-hint">${direct ? tr("سيتلقى الطرف الآخر بطاقة دعوة داخل هذه المحادثة، وسيبدأ المضيف الجولة عند جاهزية الطرفين.", "The other person will receive an invite card in this conversation; the host starts once both are ready.") : tr("الحكم آلي وفق الترتيب الظاهر؛ إحصاءات كل لاعب وكل جولة يراها المشاركون.", "The automatic judge uses the selected order; every participant's overall and per-round stats are visible.")}</p><p class="form-error" data-error hidden></p><button class="primary-button" type="submit">${tr("إنشاء", "Create")}</button></form>`,
  );
  const form = $("modalBody").querySelector("form");
  const syncForm = () => {
    form.querySelector("[data-repeat-label]").hidden = form.elements.game.value !== "repeat";
    form.querySelector("[data-topic-label]").hidden = form.elements.game.value === "repeat";
    form.querySelector("[data-event-label]").hidden = direct;
    form.querySelector("[data-visibility-label]").hidden = direct;
    form.querySelector("[data-maxplayers-label]").hidden = direct;
    const isFriday = form.elements.event_kind.value === "friday" && !direct;
    form.elements.round_count.min = isFriday ? "2" : "1";
    if (isFriday) {
      form.elements.visibility.value = "public";
      form.elements.round_count.value = String(Math.max(2, Number(form.elements.round_count.value) || 2));
    }
    form.elements.visibility.querySelector('option[value="private"]').disabled = isFriday;
    if (direct) {
      form.elements.visibility.value = "private";
      form.elements.event_kind.value = "challenge";
      form.elements.max_players.value = "2";
    }
  };
  form.elements.game.addEventListener("change", syncForm);
  form.elements.event_kind.addEventListener("change", syncForm);
  syncForm();
}
async function challengeAction(action, token) {
  if (state.page !== "community") setPage("community");
  try {
    const d = await api(
      `/api/challenges/${encodeURIComponent(token)}/${action}`,
      { method: "POST", body: {} },
    );
    if (d.challenge) {
      state.pendingInvite = "";
      state.challengeToken = d.challenge.token || token;
      state.challenge = d.challenge;
      showChallengeDetail(d.challenge);
      startChallengePolling();
    } else if (action === "cancel") {
      state.challenge = null;
      state.challengeToken = null;
      state.pendingInvite = "";
      clearInterval(state.challengeTimer);
      toast(tr("تم إلغاء التحدي.", "Challenge cancelled."));
      loadPublicChallenges();
    }
  } catch (e) {
    showError(e);
  }
}
async function copyInvite(token) {
  const url = `${location.origin}/?challenge=${encodeURIComponent(token)}`;
  try {
    await navigator.clipboard.writeText(url);
    toast(tr("نُسخ رابط الدعوة.", "Invite link copied."));
  } catch {
    openModal(
      tr("رابط الدعوة", "Invite link"),
      `<p><a href="${esc(url)}">${esc(url)}</a></p>`,
    );
  }
}
function renderSettings() {
  if (!state.user) return;
  const u = state.user;
  const host = $("page-settings");
  host.innerHTML = `<header class="page-header"><div><p class="eyebrow">${tr("حسابك", "Your account")}</p><h1>${tr("الإعدادات", "Settings")}</h1><p class="muted">${tr("عدّل ملفك الشخصي، رفيق التدريب، وتفضيلات العرض.", "Update your profile, training companion and preferences.")}</p></div></header><div class="settings-grid"><section class="settings-card"><h2>${tr("الملف الشخصي", "Profile")}</h2><div class="upload-row">${avatar(u.avatar_url, u.display_name)}<label class="upload-control">${tr("تغيير الصورة", "Change photo")}<input type="file" id="profileAvatar" accept="image/jpeg,image/png,image/webp"></label></div><form class="stack-form" data-form="profile"><label>${tr("الاسم الظاهر", "Display name")}<input name="display_name" maxlength="40" value="${esc(u.display_name || "")}" required></label><label>${tr("اسم المستخدم (ثابت)", "Username (immutable)")}<input value="@${esc(u.username)}" disabled dir="ltr"></label><label class="social-field"><span>Instagram</span><input name="instagram" maxlength="100" value="${esc(u.instagram || "")}" placeholder="username"></label><label class="social-field"><span>Snapchat</span><input name="snapchat" maxlength="100" value="${esc(u.snapchat || "")}" placeholder="username"></label><label class="social-field"><span>X / Twitter</span><input name="twitter" maxlength="100" value="${esc(u.twitter || "")}" placeholder="username"></label><p class="form-error" data-error hidden></p><button class="primary-button" type="submit">${tr("حفظ الملف", "Save profile")}</button></form></section><section class="settings-card"><h2>${tr("رفيق التدريب", "Training companion")}</h2><div class="upload-row">${avatar(u.bot?.avatar_url, u.bot?.name)}<label class="upload-control">${tr("تغيير الصورة", "Change photo")}<input type="file" id="botAvatarUpload" accept="image/jpeg,image/png,image/webp"></label></div><form class="stack-form" data-form="bot"><label>${tr("اسم البوت", "Companion name")}<input name="name" maxlength="40" value="${esc(u.bot?.name || "")}" required></label><p class="form-error" data-error hidden></p><button class="primary-button" type="submit">${tr("حفظ التخصيص", "Save companion")}</button></form><button class="secondary-button" type="button" data-action="suggestion-form">${tr("اقترح لعبة", "Suggest a game")}</button></section><section class="settings-card"><h2>${tr("المظهر واللغة", "Appearance & language")}</h2><label>${tr("اللغة", "Language")}<select id="prefLanguage"><option value="ar" ${state.lang === "ar" ? "selected" : ""}>العربية</option><option value="en" ${state.lang === "en" ? "selected" : ""}>English</option></select></label><label>${tr("المظهر", "Theme")}<select id="prefTheme"><option value="dark" ${state.theme === "dark" ? "selected" : ""}>${tr("داكن", "Dark")}</option><option value="light" ${state.theme === "light" ? "selected" : ""}>${tr("فاتح", "Light")}</option></select></label><label>${tr("لون التمييز", "Accent color")}<select id="prefAccent"><option value="violet" ${state.accent === "violet" ? "selected" : ""}>${tr("بنفسجي", "Violet")}</option><option value="ocean" ${state.accent === "ocean" ? "selected" : ""}>${tr("أزرق محيطي", "Ocean blue")}</option><option value="mint" ${state.accent === "mint" ? "selected" : ""}>${tr("نعناعي", "Mint")}</option><option value="rose" ${state.accent === "rose" ? "selected" : ""}>${tr("وردي", "Rose")}</option></select></label><p class="field-hint">${tr("تُحفظ تفضيلات اللغة والمظهر ولون التمييز على هذا الجهاز فقط.", "Language and theme preferences are stored on this device only.")}</p></section><section class="settings-card"><div class="section-heading"><h2>${tr("اقتراحاتي", "My suggestions")}</h2><button class="quiet-button" type="button" data-action="load-mine-suggestions">${tr("عرض الحالة", "View status")}</button></div><div id="mineSuggestions"></div></section>${u.role === "admin" ? `<section class="settings-card"><div class="section-heading"><h2>${tr("مراجعة اقتراحات الألعاب", "Game suggestions review")}</h2><button class="quiet-button" data-action="admin-suggestions">${tr("تحميل قائمة المراجعة", "Load queue")}</button></div><div id="adminSuggestions"></div></section>` : ""}<section class="settings-card"><h2>${tr("تسجيل الخروج", "Sign out")}</h2><button class="danger-button" type="button" data-action="logout">${tr("تسجيل الخروج من هذا الجهاز", "Sign out on this device")}</button></section></div>`;
  host.querySelector(".settings-grid").insertAdjacentHTML(
    "beforeend",
    `<section class="settings-card"><h2>${tr("حذف الحساب", "Delete account")}</h2><p class="field-hint">${tr("سيُحذف الحساب نهائيًا، بما في ذلك الرسائل التي أرسلتها أو استقبلتها، من قاعدة البيانات لدى جميع الأطراف. لا يمكن التراجع عن الحذف.", "Your account and all messages you sent or received will be permanently deleted from the database for everyone. This cannot be undone.")}</p><p class="field-hint">${tr("قد تبقى نسخ البيانات في النسخ الاحتياطية حتى انتهاء مدة احتفاظ المشغّل بها.", "Backup copies may remain until the operator's backup-retention period expires.")}</p><form class="stack-form" data-form="delete-account" autocomplete="off"><label>${tr("كلمة المرور الحالية", "Current password")}<input name="password" type="password" minlength="1" maxlength="128" autocomplete="current-password" required></label><label>${tr("اكتب اسم المستخدم لتأكيد الحذف", "Type your username to confirm")}<input name="confirm_username" maxlength="24" autocomplete="off" autocapitalize="none" spellcheck="false" placeholder="${esc(u.username)}" required></label><p class="form-error" data-error hidden></p><button class="danger-button" type="submit">${tr("حذف الحساب نهائيًا", "Permanently delete account")}</button></form></section>`,
  );
}
async function updateUser(data) {
  state.user = data.user || state.user;
  updateBotIdentity();
  if (state.page === "home") renderHome();
}
async function uploadAvatar(file, kind) {
  if (!validateImage(file)) {
    toast(
      tr(
        "اختر JPEG أو PNG أو WebP بحجم لا يتجاوز 2 ميغابايت.",
        "Choose JPEG, PNG or WebP up to 2 MB.",
      ),
    );
    return;
  }
  const fd = new FormData();
  fd.append("image", file);
  try {
    const d = await api(`/api/me/${kind === "bot" ? "bot/" : ""}avatar`, {
      method: "POST",
      form: fd,
    });
    await updateUser(d);
    renderSettings();
    toast(tr("تم تحديث الصورة.", "Photo updated."));
  } catch (e) {
    showError(e);
  }
}
$("page-settings").addEventListener("change", (e) => {
  if (e.target.id === "profileAvatar" && e.target.files[0])
    uploadAvatar(e.target.files[0], "profile");
  if (e.target.id === "botAvatarUpload" && e.target.files[0])
    uploadAvatar(e.target.files[0], "bot");
  if (e.target.id === "prefLanguage") {
    const saved = {};
    $("page-settings")
      .querySelectorAll("form input,form textarea,form select")
      .forEach((x) => {
        if (x.name && x.type !== "file") saved[x.name] = x.value;
      });
      state.lang = e.target.value;
      setPref("lang", state.lang);
      setLanguage();
      renderSettings();
      $("page-community").replaceChildren();
      $("page-settings")
      .querySelectorAll("form input,form textarea,form select")
      .forEach((x) => {
        if (x.name && saved[x.name] !== undefined) x.value = saved[x.name];
      });
  }
  if (e.target.id === "prefTheme") {
    state.theme = e.target.value;
    setPref("theme", state.theme);
    setTheme();
  }
  if (e.target.id === "prefAccent") {
    state.accent = ["violet", "ocean", "mint", "rose"].includes(e.target.value)
      ? e.target.value
      : "violet";
    setPref("accent", state.accent);
    setTheme();
  }
});
async function suggestForm() {
  openModal(
    tr("اقتراح لعبة", "Suggest a game"),
    `<form class="stack-form" data-form="suggestion"><label>${tr("اسم اللعبة أو الفكرة", "Game name or idea")}<input name="title" maxlength="80" required></label><label>${tr("التفاصيل", "Details")}<textarea name="body" maxlength="2000" rows="4" required></textarea></label><p class="form-error" data-error hidden></p><button class="primary-button" type="submit">${tr("إرسال الاقتراح", "Send suggestion")}</button></form>`,
  );
}
async function loadMineSuggestions() {
  try {
    const d = await api("/api/suggestions/mine");
    const host = $("mineSuggestions");
    if (host)
      host.innerHTML =
        (d.suggestions || [])
          .map(
            (s) =>
              `<article class="notification-row"><strong>${esc(s.title)}</strong><span class="pill">${esc(s.status)}</span><p>${esc(s.body)}</p>${s.admin_note ? `<small>${tr("ملاحظة الإدارة: ", "Admin note: ")}${esc(s.admin_note)}</small>` : ""}</article>`,
          )
          .join("") ||
        `<p class="empty-state">${tr("لا توجد اقتراحات بعد.", "No suggestions yet.")}</p>`;
  } catch (e) {
    showError(e);
  }
}
async function loadAdminSuggestions() {
  try {
    const d = await api("/api/admin/suggestions");
    const host = $("adminSuggestions");
    if (!host) return;
    host.innerHTML =
      (d.suggestions || [])
        .map(
          (s) =>
            `<article class="notification-row"><div class="section-heading"><strong>${esc(s.title)}</strong><span class="pill">${esc(s.status)}</span></div><p>${esc(s.body)}</p><small>${tr("من ", "By ")}${who(s.user)} (@${esc(s.user?.username || "")})</small>${s.status === "pending" ? `<form class="inline-form" data-form="review" data-id="${esc(s.id)}"><input name="admin_note" maxlength="500" placeholder="${tr("ملاحظة اختيارية", "Optional note")}"><button class="primary-button" name="status" value="approved">${tr("اعتماد", "Approve")}</button><button class="danger-button" name="status" value="rejected">${tr("رفض", "Reject")}</button><p class="form-error" data-error hidden></p></form>` : ""}</article>`,
        )
        .join("") ||
      `<p class="empty-state">${tr("قائمة المراجعة فارغة.", "Review queue is empty.")}</p>`;
  } catch (e) {
    showError(e);
  }
}
async function reviewSuggestion(form, status) {
  const err = form.querySelector("[data-error]");
  try {
    await api(`/api/admin/suggestions/${encodeURIComponent(form.dataset.id)}`, {
      method: "PATCH",
      body: { status, admin_note: form.elements.admin_note.value },
    });
    loadAdminSuggestions();
    toast(tr("تم حفظ قرار المراجعة.", "Review decision saved."));
  } catch (e) {
    showError(e, err);
  }
}
$("modalBody").addEventListener("submit", async (e) => {
  const f = e.target.closest("form[data-form]");
  if (!f) return;
  e.preventDefault();
  const err = f.querySelector("[data-error]");
  if (err) err.hidden = true;
  const fd = new FormData(f);
  try {
    if (f.dataset.form === "create-challenge") {
      const game = fd.get("game");
      const body = {
        game,
        difficulty: fd.get("difficulty"),
        language: state.lang,
        visibility: fd.get("event_kind") === "friday" ? "public" : fd.get("visibility"),
        max_players: Math.max(2, Math.min(8, Number(fd.get("max_players")) || 2)),
        round_count: Math.max(1, Math.min(10, Number(fd.get("round_count")) || 1)),
        judge_mode: fd.get("judge_mode"),
        event_kind: fd.get("event_kind"),
        topic: game === "repeat" ? "mixed" : fd.get("topic"),
      };
      if (f.dataset.opponent) {
        body.visibility = "private";
        body.max_players = 2;
        body.event_kind = "challenge";
        body.opponent_username = f.dataset.opponent;
      }
      if (body.event_kind === "friday") body.round_count = Math.max(2, body.round_count);
      if (game === "repeat")
        body.count = Math.max(1, Math.min(20, Number(fd.get("count")) || 1));
      const d = await api("/api/challenges", { method: "POST", body });
      state.challenge = d.challenge;
      state.challengeToken = d.challenge.token;
      state.challengeRoundSubmitted = false;
      state.challengeSubmittedRound = 0;
      startChallengePolling();
      closeModal();
      setPage("community");
      showChallengeDetail(d.challenge);
      if (d.challenge.visibility === "private" && !f.dataset.opponent) copyInvite(d.challenge.token);
      if (f.dataset.opponent) toast(tr(`تم إرسال دعوة التحدي إلى @${f.dataset.opponent}.`, `Challenge invite sent to @${f.dataset.opponent}.`));
    } else if (f.dataset.form === "suggestion") {
      await api("/api/suggestions", {
        method: "POST",
        body: { title: fd.get("title"), body: fd.get("body") },
      });
      closeModal();
      toast(
        tr(
          "وصل اقتراح اللعبة إلى قائمة المراجعة.",
          "Game suggestion added to the review queue.",
        ),
      );
      if (state.page === "settings") loadMineSuggestions();
    } else if (f.dataset.form === "review") {
      const submitter = e.submitter;
      await reviewSuggestion(f, submitter?.value || "approved");
    }
  } catch (ex) {
    if (err) showError(ex, err);
    else showError(ex);
  }
});
function renderProfile(p) {
  const social = ["instagram", "snapchat", "twitter"]
    .map((k) => {
      const h = p[k];
      if (!h) return "";
      const names = {
        instagram: "Instagram",
        snapchat: "Snapchat",
        twitter: "X",
      };
      return `<a class="social-link" href="${esc(safeSocialUrl(k, h))}" target="_blank" rel="noopener noreferrer"><img src="/static/icons/${k === "twitter" ? "x" : k}.svg" alt="">${esc(names[k])} · @${esc(h)}</a>`;
    })
    .join("");
  const s = p.stats || {};
  const self = p.id === state.user?.id;
  openModal(
    tr("الملف الشخصي", "Profile"),
    `<div class="profile-view">${avatar(p.avatar_url, p.display_name, "avatar")}<h2>${who(p)}</h2><p dir="ltr">@${esc(p.username)}</p><p>${esc(p.followers || 0)} ${tr("متابع", "followers")} · ${esc(p.following || 0)} ${tr("يتابع", "following")}</p><div class="stat-grid">${statCard(tr("الجولات", "Rounds"), s.rounds || 0)}${statCard(tr("النقاط", "Points"), s.total_points || 0)}${statCard(tr("أفضل سرعة", "Best speed"), `${s.best_wpm || 0} WPM`)}${statCard(tr("الدقة", "Accuracy"), `${s.accuracy || 0}%`)}</div>${social ? `<div class="social-links">${social}</div>` : ""}<div class="wrap">${!self ? `<button class="primary-button" data-action="toggle-follow" data-username="${esc(p.username)}" data-following="${p.is_following ? "1" : "0"}">${p.is_following ? tr("إلغاء المتابعة", "Unfollow") : p.follows_you ? tr("متابعة متبادلة", "Follow back") : tr("متابعة", "Follow")}</button><button class="secondary-button" data-action="message-user" data-username="${esc(p.username)}">${tr("إرسال رسالة", "Message")}</button><button class="quiet-button" data-action="block-user" data-username="${esc(p.username)}" data-blocked="${p.blocked_by_you ? "1" : "0"}">${p.blocked_by_you ? tr("إلغاء الحظر", "Unblock") : tr("حظر", "Block")}</button>` : ""}</div></div>`,
  );
}
async function openProfile(username) {
  try {
    const d = await api(`/api/users/${encodeURIComponent(username)}`);
    renderProfile(d.user);
  } catch (e) {
    showError(e);
  }
}
async function profileAction(action, username, blocked) {
  try {
    if (action === "toggle-follow") {
      const method = blocked ? "DELETE" : "POST";
      const d = await api(`/api/users/${encodeURIComponent(username)}/follow`, {
        method,
        body: method === "POST" ? {} : undefined,
      });
      renderProfile(d.user);
    }
    if (action === "block-user") {
      const method = blocked ? "DELETE" : "POST";
      await api(`/api/users/${encodeURIComponent(username)}/block`, {
        method,
        body: method === "POST" ? {} : undefined,
      });
      closeModal();
      toast(
        blocked
          ? tr("أُلغي الحظر.", "User unblocked.")
          : tr("تم الحظر.", "User blocked."),
      );
    }
    if (action === "message-user") {
      closeModal();
      setPage("messages");
      openThread(username);
    }
  } catch (e) {
    showError(e);
  }
}
function renderThreadList() {
  const host = $("threadList");
  if (!host) return;
  host.innerHTML =
    state.threads
      .map(
        (t) =>
          `<button class="thread-row ${state.activeThread === t.user.username ? "active" : ""}" data-action="open-thread" data-username="${esc(t.user.username)}">${avatar(t.user.avatar_url, t.user.display_name)}<span class="thread-preview"><strong>${who(t.user)}</strong><small>${esc(t.last_message?.image_url ? tr("صورة", "Photo") : t.last_message?.challenge_token ? tr("دعوة تحدٍّ", "Challenge invite") : t.last_message?.body || "")}</small></span>${t.unread ? `<span class="badge unread">${esc(t.unread)}</span>` : ""}</button>`,
      )
      .join("") ||
    `<p class="empty-state">${tr("لا توجد محادثات. ابدأ محادثة من المجتمع.", "No conversations yet. Start one from Community.")}</p>`;
}
async function loadThreads() {
  try {
    const d = await api("/api/messages/threads");
    state.threads = d.threads || [];
    renderThreadList();
  } catch (e) {
    if (e.status !== 401) showError(e);
  }
}
function validChatTheme(value) {
  return ["violet", "ocean", "mint", "rose", "amber"].includes(value) ? value : "violet";
}
function validChatBackground(value) {
  return ["plain", "aurora", "dunes", "stars", "paper"].includes(value) ? value : "plain";
}
function syncChatAppearance(username = state.activeThread) {
  const panel = $("conversationPanel");
  if (!panel || !username) return;
  panel.dataset.chatTheme = validChatTheme(localPref(`chat-theme:${username}`, "violet"));
  panel.dataset.chatBackground = validChatBackground(localPref(`chat-background:${username}`, "plain"));
}
function openChatAppearance() {
  if (!state.activeThread) return;
  const theme = validChatTheme(localPref(`chat-theme:${state.activeThread}`, "violet"));
  const background = validChatBackground(localPref(`chat-background:${state.activeThread}`, "plain"));
  const themes = [
    ["violet", tr("بنفسجي", "Violet")], ["ocean", tr("محيطي", "Ocean")],
    ["mint", tr("نعناعي", "Mint")], ["rose", tr("وردي", "Rose")],
    ["amber", tr("عنبر", "Amber")],
  ];
  const backgrounds = [
    ["plain", tr("هادئة", "Plain")], ["aurora", tr("الشفق", "Aurora")],
    ["dunes", tr("الكثبان", "Dunes")], ["stars", tr("النجوم", "Stars")],
    ["paper", tr("ورقية", "Paper")],
  ];
  openModal(tr("مظهر المحادثة", "Chat appearance"), `<p class="field-hint">${tr("يُحفظ المظهر لهذا الحوار على هذا الجهاز فقط.", "Appearance is saved for this conversation on this device only.")}</p><section class="appearance-section"><h3>${tr("لون المحادثة", "Chat theme")}</h3><div class="appearance-choices">${themes.map(([value, label]) => `<button type="button" class="appearance-choice theme-${value} ${theme === value ? "selected" : ""}" data-action="set-chat-theme" data-value="${value}" aria-pressed="${theme === value}"><span class="appearance-dot"></span>${label}</button>`).join("")}</div></section><section class="appearance-section"><h3>${tr("الخلفية", "Background")}</h3><div class="appearance-choices">${backgrounds.map(([value, label]) => `<button type="button" class="appearance-choice background-${value} ${background === value ? "selected" : ""}" data-action="set-chat-background" data-value="${value}" aria-pressed="${background === value}"><span class="appearance-swatch"></span>${label}</button>`).join("")}</div></section>`);
}
function applyChatAppearanceChoice(kind, value) {
  if (!state.activeThread) return;
  if (kind === "theme") {
    value = validChatTheme(value);
    setPref(`chat-theme:${state.activeThread}`, value);
    $("conversationPanel").dataset.chatTheme = value;
    $("modalBody").querySelectorAll("[data-action='set-chat-theme']").forEach((button) => {
      const selected = button.dataset.value === value;
      button.classList.toggle("selected", selected);
      button.setAttribute("aria-pressed", String(selected));
    });
  } else {
    value = validChatBackground(value);
    setPref(`chat-background:${state.activeThread}`, value);
    $("conversationPanel").dataset.chatBackground = value;
    $("modalBody").querySelectorAll("[data-action='set-chat-background']").forEach((button) => {
      const selected = button.dataset.value === value;
      button.classList.toggle("selected", selected);
      button.setAttribute("aria-pressed", String(selected));
    });
  }
}
function openConversationView(user) {
  state.activeThread = user.username;
  state.messageAfter = 0;
  syncChatAppearance(user.username);
  $("conversationPanel").hidden = false;
  $("conversationEmpty").hidden = true;
  $("page-messages").classList.add("conversation-open");
  $("conversationProfile").innerHTML =
    `${avatar(user.avatar_url, user.display_name)}<span><bdi>${who(user)}</bdi><small dir="ltr">@${esc(user.username)}</small></span>`;
  $("messageLog").replaceChildren();
  $("appScreen").classList.add("dm-open");
  $("messageInput").value = "";
  renderThreadList();
  api(`/api/messages/${encodeURIComponent(user.username)}/read`, {
    method: "POST",
    body: {},
  })
    .then(() => {
      const t = state.threads.find((x) => x.user.username === user.username);
      if (t)
        state.unreadMessages = Math.max(
          0,
          state.unreadMessages - (t.unread || 0),
        );
      updateBadges();
    })
    .catch((e) => {
      if (e.status !== 401) showError(e);
    });
  startMessagePolling();
}
async function openThread(username) {
  try {
    const d = await api(
      `/api/messages/${encodeURIComponent(username)}?after=0`,
    );
    openConversationView(d.user);
    appendMessages(d.messages || []);
  } catch (e) {
    showError(e);
  }
}
function appendMessages(messages) {
  const log = $("messageLog");
  const atBottom = log.scrollHeight - log.scrollTop - log.clientHeight < 60;
  for (const m of messages) {
    if (+m.id <= state.messageAfter) continue;
    const mine = String(m.sender_id) === String(state.user.id);
    const row = document.createElement("div");
    row.className = `message-bubble ${mine ? "mine" : ""}`;
    if (m.body) {
      const body = document.createElement("div");
      body.className = "message-body";
      body.textContent = m.body;
      row.append(body);
    }
    if (m.image_url) {
      const image = document.createElement("img");
      image.className = "message-image";
      image.src = m.image_url;
      image.alt = tr("صورة في رسالة خاصة", "Image in a private message");
      image.loading = "lazy";
      image.decoding = "async";
      row.append(image);
    }
    if (m.challenge_token) {
      const invitation = document.createElement("button");
      invitation.className = "secondary-button message-challenge-invite";
      invitation.type = "button";
      invitation.dataset.action = "open-challenge-invite";
      invitation.dataset.token = m.challenge_token;
      invitation.textContent = tr("فتح تحدي الكتابة", "Open typing challenge");
      row.append(invitation);
    }
    const time = document.createElement("time");
    time.className = "message-time";
    time.textContent = m.created_at
      ? new Date(m.created_at).toLocaleTimeString(
          state.lang === "ar" ? "ar" : "en",
          { hour: "2-digit", minute: "2-digit" },
        )
      : "";
    row.append(time);
    log.append(row);
    state.messageAfter = Math.max(state.messageAfter, +m.id || 0);
  }
  if (atBottom) log.scrollTop = log.scrollHeight;
}
async function loadMessages(initial) {
  const username = state.activeThread;
  if (!username || document.hidden) return;
  try {
    const d = await api(
      `/api/messages/${encodeURIComponent(username)}?after=${initial ? 0 : state.messageAfter}`,
    );
    if (username !== state.activeThread) return;
    appendMessages(d.messages || []);
    if (d.messages?.length)
      api(`/api/messages/${encodeURIComponent(username)}/read`, {
        method: "POST",
        body: {},
      }).catch(() => {});
  } catch (e) {
    if (e.status === 403) {
      clearInterval(state.messagePoll);
      state.messagePoll = null;
      showError(e);
    } else if (e.status !== 401) console.warn("messages poll", e);
  }
}
$("messageForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = $("messageInput"),
    text = input.value;
  const form = e.currentTarget;
  if (!text.trim() || !state.activeThread || form.dataset.sending === "1") return;
  const username = state.activeThread;
  form.dataset.sending = "1";
  try {
    const d = await api(`/api/messages/${encodeURIComponent(username)}`, {
      method: "POST",
      body: { body: text },
    });
    input.value = "";
    input.style.height = "";
    appendMessages([d.message]);
    loadThreads();
  } catch (e) {
    showError(e);
  } finally {
    form.dataset.sending = "";
  }
});
async function uploadMessageImage(file) {
  if (!state.activeThread || !file) return;
  if (!/^image\/(jpeg|png|webp)$/.test(file.type) || file.size > 5 * 1024 * 1024) {
    toast(tr("اختر صورة JPEG أو PNG أو WebP لا تتجاوز 5 ميغابايت.", "Choose a JPEG, PNG or WebP image no larger than 5 MB."));
    return;
  }
  const username = state.activeThread;
  const form = $("messageForm");
  const button = $("messageImageButton");
  const input = $("messageImageInput");
  if (form.dataset.sending === "1") return;
  form.dataset.sending = "1";
  button.disabled = true;
  try {
    const payload = new FormData();
    payload.append("image", file);
    payload.append("caption", $("messageInput").value);
    const result = await api(`/api/messages/${encodeURIComponent(username)}/image`, { method: "POST", form: payload });
    if (state.activeThread !== username) return;
    $("messageInput").value = "";
    $("messageInput").style.height = "";
    appendMessages([result.message]);
    loadThreads();
  } catch (error) {
    showError(error);
  } finally {
    form.dataset.sending = "";
    button.disabled = false;
    input.value = "";
  }
}
$("messageImageButton").addEventListener("click", () => $("messageImageInput").click());
$("messageImageInput").addEventListener("change", (event) => {
  const file = event.target.files?.[0];
  if (file) uploadMessageImage(file);
});
async function openChallengeInvitation(token) {
  if (!token) return;
  try {
    const result = await api(`/api/challenges/${encodeURIComponent(token)}`);
    state.challenge = result.challenge;
    state.challengeToken = result.challenge.token || token;
    state.challengeRoundSubmitted = false;
    state.challengeSubmittedRound = 0;
    setPage("community");
    showChallengeDetail(result.challenge);
    startChallengePolling();
  } catch (error) {
    showError(error);
  }
}
function startMessagePolling() {
  clearInterval(state.messagePoll);
  state.messagePoll = setInterval(() => {
    if (document.hidden || state.page !== "messages") return;
    if (state.activeThread) loadMessages(false);
    else loadThreads();
  }, 2000);
}
$("backToThreads").addEventListener("click", () => {
  $("page-messages").classList.remove("conversation-open");
  $("appScreen").classList.remove("dm-open");
  $("conversationPanel").hidden = true;
  $("conversationEmpty").hidden = false;
  state.activeThread = null;
  loadThreads();
  startMessagePolling();
});
$("conversationProfile").addEventListener(
  "click",
  () => state.activeThread && openProfile(state.activeThread),
);
async function newMessageChooser() {
  openModal(
    tr("محادثة جديدة", "New conversation"),
    `<div class="stack-form"><label class="search-field">${tr("ابحث عن مستخدم", "Search users")}<input id="dmSearch" type="search" maxlength="24" autocomplete="off"></label><button class="quiet-button" type="button" data-action="load-following">${tr("عرض من أتابع", "Show following")}</button><div id="dmResults" class="list"></div></div>`,
  );
}
async function loadFollowing() {
  try {
    const d = await api("/api/me/following");
    const host = $("dmResults");
    host.innerHTML =
      (d.users || [])
        .map(
          (u) =>
            `<button class="user-row" data-action="start-dm" data-username="${esc(u.username)}">${avatar(u.avatar_url, u.display_name)}<span class="user-copy"><strong>${who(u)}</strong><small>@${esc(u.username)}</small></span></button>`,
        )
        .join("") ||
      `<p class="empty-state">${tr("لا أتابع أحدًا بعد.", "You are not following anyone yet.")}</p>`;
  } catch (e) {
    showError(e);
  }
}
async function searchForDM(q) {
  if (!q.trim()) return;
  try {
    const d = await api("/api/users/search?q=" + encodeURIComponent(q.trim()));
    $("dmResults").innerHTML =
      (d.users || [])
        .map(
          (u) =>
            `<button class="user-row" data-action="start-dm" data-username="${esc(u.username)}">${avatar(u.avatar_url, u.display_name)}<span class="user-copy"><strong>${who(u)}</strong><small>@${esc(u.username)}</small></span></button>`,
        )
        .join("") ||
      `<p class="empty-state">${tr("لا توجد نتائج.", "No results.")}</p>`;
  } catch (e) {
    showError(e);
  }
}
$("notificationsButton").addEventListener("click", async () => {
  try {
    const d = await api("/api/notifications");
    openModal(
      tr("الإشعارات", "Notifications"),
      `<div class="list">${(d.notifications || []).map((n) => `<article class="notification-row ${n.read ? "" : "unread"}"><strong>${esc(n.actor?.display_name || tr("النظام", "System"))}</strong><p>${esc(n.body)}</p><small>${n.created_at ? esc(new Date(n.created_at).toLocaleString(state.lang === "ar" ? "ar" : "en")) : ""}</small></article>`).join("") || `<p class="empty-state">${tr("لا توجد إشعارات.", "No notifications.")}</p>`}</div><button class="secondary-button" data-action="read-notifications">${tr("تحديد الكل كمقروء", "Mark all read")}</button>`,
    );
    state.unreadNotifications = 0;
    updateBadges();
  } catch (e) {
    showError(e);
  }
});
function startNotificationPolling() {
  clearInterval(state.notificationPoll);
  state.notificationPoll = setInterval(async () => {
    if (document.hidden || !state.user) return;
    try {
      const d = await api("/api/session");
      state.unreadNotifications = d.unread_notifications || 0;
      state.unreadMessages = d.unread_messages || 0;
      updateBadges();
    } catch (e) {
      if (e.status !== 401) console.warn("session poll", e);
    }
  }, 15000);
}
async function logout() {
  const round = state.round;
  clearRuntime();
  try {
    if (round && !round.challenge_id)
      try {
        await api(`/api/rounds/${encodeURIComponent(round.id)}/cancel`, {
          method: "POST",
          body: {},
        });
      } catch {}
    await api("/api/auth/logout", { method: "POST", body: {} });
  } catch (e) {
    if (e.status !== 401) showError(e);
  } finally {
    state.user = null;
    state.csrf = null;
    state.threads = [];
    state.pendingInvite = "";
    state.unreadMessages = state.unreadNotifications = 0;
    updateBadges();
    history.replaceState(null, "", location.pathname);
    closeModal();
    $("botLog").replaceChildren();
    $("messageLog").replaceChildren();
    $("threadList").replaceChildren();
    $("page-home").replaceChildren();
    $("page-community").replaceChildren();
    $("page-settings").replaceChildren();
    $("roundPanel").hidden = true;
    $("appScreen").hidden = true;
    $("authScreen").hidden = false;
    $("authForm").reset();
    $("authError").hidden = true;
  }
}
$("selfProfileButton").addEventListener(
  "click",
  () => state.user && renderProfile(state.user),
);
$("newMessageButton").addEventListener("click", newMessageChooser);
$("page-community").addEventListener("input", (e) => {
  if (e.target.id === "communitySearch") {
    clearTimeout(state.searchTimer);
    state.searchTimer = setTimeout(() => searchUsers(e.target.value), 250);
  }
});
$("page-community").addEventListener("click", (e) => {
  const sort = e.target.closest("[data-sort]");
  if (sort) {
    state.communitySort = sort.dataset.sort;
    $("page-community")
      .querySelectorAll("[data-sort]")
      .forEach((b) => b.classList.toggle("active", b === sort));
    loadLeaderboard();
  }
});
$("modalBody").addEventListener("input", (e) => {
  if (e.target.id === "dmSearch") {
    clearTimeout(state.searchTimer);
    state.searchTimer = setTimeout(() => searchForDM(e.target.value), 250);
  }
});
document.addEventListener("click", async (e) => {
  const b = e.target.closest("[data-action]");
  if (!b) return;
  const action = b.dataset.action,
    username = b.dataset.username,
    token = b.dataset.token;
  switch (action) {
    case "go-bot":
      setPage("bot");
      break;
    case "go-community":
      setPage("community");
      break;
    case "go-messages":
      setPage("messages");
      break;
    case "profile":
      if (username) openProfile(username);
      break;
    case "toggle-follow":
      profileAction(action, username, b.dataset.following === "1");
      break;
    case "block-user":
      profileAction(action, username, b.dataset.blocked === "1");
      break;
    case "message-user":
      profileAction(action, username);
      break;
    case "create-challenge":
      createChallengeForm();
      break;
    case "direct-challenge":
      if (state.activeThread) createChallengeForm({ game: "sentences", difficulty: "medium", visibility: "private", max_players: 2, round_count: 3, judge_mode: "points", topic: "mixed", event_kind: "challenge" }, state.activeThread);
      break;
    case "open-chat-appearance":
      openChatAppearance();
      break;
    case "set-chat-theme":
      applyChatAppearanceChoice("theme", b.dataset.value);
      break;
    case "set-chat-background":
      applyChatAppearanceChoice("background", b.dataset.value);
      break;
    case "select-message-image":
      $("messageImageInput").click();
      break;
    case "open-challenge-invite":
      openChallengeInvitation(token);
      break;
    case "create-preset":
      createChallengeForm(challengePresets[b.dataset.preset] || {});
      break;
    case "create-friday":
      createChallengeForm(challengePresets.friday);
      break;
    case "speak-round":
      speakRoundText();
      break;
    case "toggle-key-sound":
      state.soundEnabled = !state.soundEnabled;
      setPref("key-sound", state.soundEnabled ? "on" : "off");
      updateSoundButton();
      if (state.soundEnabled) playTypingTone(true);
      break;
    case "challenge-join":
      challengeAction("join", token);
      break;
    case "challenge-start":
      challengeAction("start", token);
      break;
    case "challenge-cancel":
      if (confirm(tr("إلغاء هذا التحدي؟", "Cancel this challenge?")))
        challengeAction("cancel", token);
      break;
    case "copy-invite":
      copyInvite(token);
      break;
    case "suggestion-form":
      suggestForm();
      break;
    case "load-mine-suggestions":
      loadMineSuggestions();
      break;
    case "admin-suggestions":
      loadAdminSuggestions();
      break;
    case "logout":
      logout();
      break;
    case "open-thread":
      if (username) openThread(username);
      break;
    case "load-following":
      loadFollowing();
      break;
    case "start-dm":
      if (username) {
        closeModal();
        openThread(username);
      }
      break;
    case "read-notifications":
      try {
        await api("/api/notifications/read", { method: "POST", body: {} });
        state.unreadNotifications = 0;
        updateBadges();
        closeModal();
      } catch (err) {
        showError(err);
      }
      break;
  }
});
$("bottomNav").addEventListener("click", (e) => {
  const b = e.target.closest("[data-page]");
  if (b) setPage(b.dataset.page);
});
$("exitBotButton").addEventListener("click", () => setPage("home"));
$("closeModal").addEventListener("click", closeModal);
$("modal").addEventListener("click", (e) => {
  if (e.target === $("modal")) closeModal();
});
$("modal").addEventListener("cancel", (e) => {
  e.preventDefault();
  closeModal();
});
$("page-settings").addEventListener("submit", async (e) => {
  const f = e.target.closest("form[data-form]");
  if (!f) return;
  e.preventDefault();
  const err = f.querySelector("[data-error]");
  if (err) err.hidden = true;
  const fd = new FormData(f);
  try {
    if (f.dataset.form === "delete-account") {
      await api("/api/me", {
        method: "DELETE",
        body: {
          password: fd.get("password"),
          confirm_username: fd.get("confirm_username"),
        },
      });
      fd.delete("password");
      state.user = null;
      state.csrf = null;
      state.threads = [];
      state.pendingInvite = "";
      state.unreadMessages = state.unreadNotifications = 0;
      clearRuntime();
      updateBadges();
      history.replaceState(null, "", location.pathname);
      $("page-settings").replaceChildren();
      $("botLog").replaceChildren();
      $("messageLog").replaceChildren();
      $("threadList").replaceChildren();
      $("appScreen").hidden = true;
      $("authScreen").hidden = false;
      $("authForm").reset();
      $("authError").classList.remove("form-error");
      $("authError").classList.add("form-success");
      $("authError").textContent = tr(
        "حُذف الحساب نهائيًا، بما في ذلك الرسائل المرتبطة به.",
        "The account and its associated messages have been permanently deleted.",
      );
      $("authError").hidden = false;
    } else if (f.dataset.form === "profile") {
      const d = await api("/api/me/profile", {
        method: "PATCH",
        body: {
          display_name: fd.get("display_name"),
          instagram: fd.get("instagram"),
          snapchat: fd.get("snapchat"),
          twitter: fd.get("twitter"),
        },
      });
      await updateUser(d);
      renderSettings();
      toast(tr("تم حفظ الملف الشخصي.", "Profile saved."));
    } else if (f.dataset.form === "bot") {
      const d = await api("/api/me/bot", {
        method: "PATCH",
        body: { name: fd.get("name") },
      });
      await updateUser(d);
      renderSettings();
      toast(tr("تم حفظ تخصيص رفيقك.", "Companion settings saved."));
    } else if (f.dataset.form === "review") {
      await reviewSuggestion(f, e.submitter?.value || "approved");
    }
  } catch (ex) {
    showError(ex, err);
  }
});
function onVisibility() {
  if (document.hidden) return;
  if (state.page === "messages" && state.activeThread) loadMessages(false);
  if (state.challengeToken) pollChallenge(true);
}
document.addEventListener("visibilitychange", onVisibility);
setTheme();
setLanguage();
authStrings();
syncViewport();
loadSession();
