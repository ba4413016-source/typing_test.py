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
  storedAccent = localPref("accent", "violet");
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
  challengeOffset: 0,
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
      if (vv && Math.abs(vv.scale - 1) > 0.01) return;
      const h = vv?.height || window.innerHeight;
      const top = vv?.offsetTop || 0;
      document.documentElement.style.setProperty("--app-height", `${h}px`);
      document.documentElement.style.setProperty("--app-top", `${top}px`);
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
  host.innerHTML = `<header class="page-header"><div><p class="eyebrow">mr.typing</p><h1>${tr("أهلًا، ", "Welcome, ")}${who(state.user)}</h1><p class="muted">${tr("كل جولة تقرّبك من كتابة أسرع وأدق.", "Every round brings faster, more accurate typing.")}</p></div></header><section class="hero"><div class="hero-copy"><p class="eyebrow">${tr("مساحة تدريبك", "Your practice space")}</p><h2>${tr("اكتب بثقة. وتقدّم على طريقتك.", "Type with confidence. Improve at your pace.")}</h2><p>${tr("ابدأ جولة مع رفيقك، ثم تابع تقدمك وتحدَّ أصدقاءك.", "Start a round with your companion, track progress and challenge friends.")}</p></div><div class="hero-actions"><button class="primary-button" type="button" data-action="go-bot">${tr("ابدأ التدريب", "Start practicing")}</button><button class="secondary-button" type="button" data-action="go-community">${tr("استكشف المجتمع", "Explore community")}</button></div></section><section class="stat-grid">${statCard(tr("الجولات", "Rounds"), s.rounds || 0)}${statCard(tr("مجموع النقاط", "Total points"), s.total_points || 0)}${statCard(tr("أفضل سرعة", "Best speed"), `${s.best_wpm || 0} WPM`)}${statCard(tr("الدقة", "Accuracy"), `${s.accuracy || 0}%`)}</section><section class="section-gap"><div class="section-heading"><div><p class="eyebrow">${tr("ابدأ من هنا", "Start here")}</p><h2>${tr("اختر خطوتك التالية", "Choose your next step")}</h2></div></div><div class="card-grid"><button class="action-card" data-action="go-bot"><strong>${tr("تدريب مستمر", "Continuous practice")}</strong><span class="muted">${tr("اختر اللعبة والمستوى وتدرّب دون توقف.", "Choose a game and keep practicing.")}</span></button><button class="action-card" data-action="go-community"><strong>${tr("تحدَّ أصدقاءك", "Challenge friends")}</strong><span class="muted">${tr("أنشئ تحديًا أو انضم إلى ردهة عامة.", "Create or join a challenge.")}</span></button><button class="action-card" data-action="go-messages"><strong>${tr("رسائلك", "Your messages")}</strong><span class="muted">${tr("تواصل مع المتابعين والأصدقاء.", "Connect with people you follow.")}</span></button></div></section>`;
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
  state.activeThread = null;
  state.botMode = "idle";
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
function showBotHelp() {
  appendBot(
    tr(
      "اكتب اللعبة والمستوى مباشرة، مثل «جمل متوسط» أو «تكرار متوسط ٥». الأوامر: وقف، إحصائيات، مساعدة، إعدادات. الألعاب: جمل، قصة، أخبار، تكرار؛ والمستويات: سهل، متوسط، صعب.",
      "Type a game and level, e.g. “sentences medium” or “repeat medium 5”. Commands: stop, stats, help, settings. Games: sentences, stories, news, repeat; levels: easy, medium, hard.",
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
    if (event.key !== "Enter" || event.shiftKey || event.isComposing) return;
    event.preventDefault();
    input.form.requestSubmit();
  });
  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
  });
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
  $("targetText").textContent = r.display ?? r.target ?? "";
  $("targetText").classList.toggle("repeat-target", r.game === "repeat");
  $("targetText").dir = r.game === "repeat" ? "ltr" : "auto";
  $("roundLabel").textContent =
    `${tr(...(labels.games[r.game] || ["تدريب", "Practice"]))} · ${tr(...(labels.levels[r.difficulty] || ["متوسط", "Medium"]))}`;
  $("roundCounter").textContent =
    r.game === "repeat"
      ? `${r.word_count || state.flow.count || 1} ${tr("كلمة", "word(s)")} · 3×`
      : "";
  $("roundHint").textContent =
    r.game === "repeat"
      ? tr(
          "اكتب كل كلمة ثلاث مرات بمسافة بين الكلمات، دون الأقواس والرقم.",
          "Type each word three times, separated by spaces; omit parentheses and the number.",
        )
      : tr(
          "اكتب النص كما يظهر؛ المسافات وعلامات الترقيم محسوبة.",
          "Type the text as shown; spaces and punctuation count.",
        );
  $("roundState").textContent = tr("بانتظار أول حرف", "Waiting for first key");
  $("liveSpeed").textContent = "0 WPM";
  $("liveAccuracy").textContent = "100%";
  $("botInput").placeholder = tr("اكتب إجابتك…", "Type your answer…");
  document.body.classList.add("round-active");
}
function graphemes(value) {
  if (typeof Intl.Segmenter === "function") {
    return Array.from(
      new Intl.Segmenter(state.lang, { granularity: "grapheme" }).segment(value),
      (part) => part.segment,
    );
  }
  return Array.from(value);
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
    state.round = null;
    state.started = false;
    state.beginPromise = null;
    state.user.stats = d.stats || d.result.stats || state.user.stats;
    renderResult(d.result, userMessage);
    if (state.challenge && state.challenge.status === "active") {
      state.challengeRoundSubmitted = true;
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
  if (!el.innerHTML)
    el.innerHTML = `<header class="page-header"><div><p class="eyebrow">${tr("تواصل وتحدَّ", "Connect & compete")}</p><h1>${tr("المجتمع", "Community")}</h1><p class="muted">${tr("ابحث عن مستخدمين، تابع الترتيب، أو ابدأ تحديًا.", "Find users, check rankings, or start a challenge.")}</p></div></header><section class="card section-gap"><div class="section-heading"><h2>${tr("ابحث عن مستخدم", "Find a user")}</h2></div><label class="search-field"><span class="muted">@</span><input id="communitySearch" type="search" maxlength="24" autocomplete="off" placeholder="${tr("اسم المستخدم", "Username")}"></label><div id="searchResults" class="list"></div></section><section class="card section-gap"><div class="section-heading"><h2>${tr("لوحة المتصدرين", "Leaderboard")}</h2><div class="segmented"><button type="button" data-sort="points" class="${state.communitySort === "points" ? "active" : ""}">${tr("النقاط", "Points")}</button><button type="button" data-sort="wpm" class="${state.communitySort === "wpm" ? "active" : ""}">${tr("السرعة", "Speed")}</button></div></div><div id="leaderboard" class="list"></div></section><section class="card section-gap"><div class="section-heading"><div><h2>${tr("التحديات", "Challenges")}</h2><p class="muted">${tr("تحديات خاصة بالرابط أو ردهات عامة.", "Private invite links or public lobbies.")}</p></div><button class="primary-button" type="button" data-action="create-challenge">${tr("إنشاء تحدٍّ", "Create challenge")}</button></div><div id="challengePanel"></div></section><div id="challengeInvite"></div>`;
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
      `<p class="empty-state">${tr("لا توجد ردهات عامة مفتوحة الآن.", "No public lobbies are open right now.")}</p>`;
  } catch (e) {
    if (e.status !== 401)
      host.innerHTML = `<p class="form-error">${esc(errorText(e))}</p>`;
  }
}
function challengeCard(c, detail = true) {
  const me = c.owner?.id === state.user?.id;
  const mine = (c.participants || []).some(
    (p) => p.user?.id === state.user?.id,
  );
  const member = (c.participants || [])
    .map(
      (p) =>
        `<div class="player-row">${avatar(p.user?.avatar_url, p.user?.display_name)}<span>${who(p.user)}${p.finished ? ` · ${esc(p.result?.wpm || 0)} WPM` : ""}</span></div>`,
    )
    .join("");
  const controls = [];
  if (c.status === "lobby" && !mine && c.token)
    controls.push(
      `<button class="primary-button" data-action="challenge-join" data-token="${esc(c.token)}">${tr("انضمام", "Join")}</button>`,
    );
  if (c.status === "lobby" && me)
    controls.push(
      `<button class="primary-button" data-action="challenge-start" data-token="${esc(c.token || state.challengeToken)}" ${c.participants?.length < 2 ? "disabled" : ""}>${tr("ابدأ التحدي", "Start challenge")}</button>`,
    );
  if (["lobby", "active"].includes(c.status) && me)
    controls.push(
      `<button class="danger-button" data-action="challenge-cancel" data-token="${esc(c.token || state.challengeToken)}">${tr("إلغاء التحدي", "Cancel challenge")}</button>`,
    );
  if (c.status === "lobby" && me && c.visibility === "private" && c.token)
    controls.push(
      `<button class="secondary-button" data-action="copy-invite" data-token="${esc(c.token)}">${tr("نسخ رابط الدعوة", "Copy invite link")}</button>`,
    );
  const winner = c.winner
    ? `<div class="winner-card">${tr("الفائز: ", "Winner: ")}${who(c.winner)}</div>`
    : "";
  const start = c.starts_at
    ? new Date(c.starts_at).toLocaleString(state.lang === "ar" ? "ar" : "en")
    : "—";
  return `<article class="challenge-card"><div class="section-heading"><div><strong>${esc(c.owner?.display_name || c.owner?.username || tr("تحدٍّ", "Challenge"))}</strong><p class="muted">${tr(...(labels.games[c.game] || ["تدريب", "Practice"]))} · ${tr(...(labels.levels[c.difficulty] || ["متوسط", "Medium"]))} · ${c.visibility === "private" ? tr("خاص", "Private") : tr("عام", "Public")}</p></div><span class="pill">${esc(c.status)}</span></div><p class="muted">${tr("اللاعبون", "Players")}: ${c.participants?.length || 0}/${c.max_players} · ${tr("البدء", "Starts")}: ${esc(start)}</p><div class="player-list">${member}</div>${winner}<div class="wrap">${controls.join("")}</div></article>`;
}
function showChallengeDetail(c) {
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
async function createChallengeForm() {
  const games = Object.keys(labels.games),
    levels = Object.keys(labels.levels);
  openModal(
    tr("إنشاء تحدٍّ", "Create a challenge"),
    `<form class="stack-form" data-form="create-challenge"><label>${tr("اللعبة", "Game")}<select name="game">${games.map((g) => `<option value="${g}">${tr(...labels.games[g])}</option>`).join("")}</select></label><label>${tr("المستوى", "Difficulty")}<select name="difficulty">${levels.map((l) => `<option value="${l}">${tr(...labels.levels[l])}</option>`).join("")}</select></label><label data-repeat-label hidden>${tr("عدد التكرارات (1–20)", "Repetitions (1–20)")}<input name="count" type="number" min="1" max="20" value="3"></label><label>${tr("نوع التحدي", "Visibility")}<select name="visibility"><option value="private">${tr("خاص (رابط دعوة)", "Private (invite link)")}</option><option value="public">${tr("عام (ردهة)", "Public lobby")}</option></select></label><label>${tr("الحد الأقصى للاعبين (2–8)", "Maximum players (2–8)")}<input name="max_players" type="number" min="2" max="8" value="2" required></label><p class="form-error" data-error hidden></p><button class="primary-button" type="submit">${tr("إنشاء", "Create")}</button></form>`,
  );
  const f = $("modalBody").querySelector("form");
  f.elements.game.addEventListener(
    "change",
    () =>
      (f.querySelector("[data-repeat-label]").hidden =
        f.elements.game.value !== "repeat"),
  );
}
async function challengeAction(action, token) {
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
        visibility: fd.get("visibility"),
        max_players: Math.max(
          2,
          Math.min(8, Number(fd.get("max_players")) || 2),
        ),
      };
      if (game === "repeat")
        body.count = Math.max(1, Math.min(20, Number(fd.get("count")) || 1));
      const d = await api("/api/challenges", { method: "POST", body });
      state.challenge = d.challenge;
      state.challengeToken = d.challenge.token;
      state.challengeRoundSubmitted = false;
      startChallengePolling();
      closeModal();
      setPage("community");
      showChallengeDetail(d.challenge);
      if (d.challenge.visibility === "private") copyInvite(d.challenge.token);
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
          `<button class="thread-row ${state.activeThread === t.user.username ? "active" : ""}" data-action="open-thread" data-username="${esc(t.user.username)}">${avatar(t.user.avatar_url, t.user.display_name)}<span class="thread-preview"><strong>${who(t.user)}</strong><small>${esc(t.last_message?.body || "")}</small></span>${t.unread ? `<span class="badge unread">${esc(t.unread)}</span>` : ""}</button>`,
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
function openConversationView(user) {
  state.activeThread = user.username;
  state.messageAfter = 0;
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
    const body = document.createElement("div");
    body.textContent = m.body;
    const time = document.createElement("time");
    time.className = "message-time";
    time.textContent = m.created_at
      ? new Date(m.created_at).toLocaleTimeString(
          state.lang === "ar" ? "ar" : "en",
          { hour: "2-digit", minute: "2-digit" },
        )
      : "";
    row.append(body, time);
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
