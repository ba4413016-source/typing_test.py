const welcome = document.getElementById("welcomeScreen");
const authScreen = document.getElementById("authScreen");
const appScreen = document.getElementById("appScreen");
const installButton = document.getElementById("installAppButton");
const continueButton = document.getElementById("welcomeContinueButton");
const instructions = document.getElementById("installInstructions");
let deferredInstallPrompt = null;

function savedLanguage() {
  try {
    return localStorage.getItem("typing.lang") === "en" ? "en" : "ar";
  } catch {
    return "ar";
  }
}

function applyWelcomeLanguage() {
  const language = savedLanguage();
  document.documentElement.lang = language;
  document.documentElement.dir = language === "ar" ? "rtl" : "ltr";
  welcome.querySelectorAll("[data-welcome-ar][data-welcome-en]").forEach((element) => {
    element.textContent =
      language === "ar" ? element.dataset.welcomeAr : element.dataset.welcomeEn;
  });
}

function isStandalone() {
  return (
    window.matchMedia?.("(display-mode: standalone)").matches ||
    window.navigator.standalone === true
  );
}

function hasSeenWelcome() {
  try {
    return localStorage.getItem("typing.welcome-seen") === "1";
  } catch {
    return false;
  }
}

function closeWelcome() {
  welcome.hidden = true;
  authScreen.inert = false;
  appScreen.inert = false;
  try {
    localStorage.setItem("typing.welcome-seen", "1");
  } catch {}
  if (!authScreen.hidden) {
    document.getElementById("authUsername").focus({ preventScroll: true });
  }
}

function showInstallInstructions() {
  const language = savedLanguage();
  const isIOS =
    /iPad|iPhone|iPod/.test(navigator.userAgent) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  instructions.textContent = isIOS
    ? language === "ar"
      ? "في Safari، اضغط زر المشاركة (المربع والسهم للأعلى)، ثم اختر «إضافة إلى الشاشة الرئيسية» واضغط «إضافة»."
      : "In Safari, tap Share (the square with the up arrow), choose “Add to Home Screen,” then tap “Add.”"
    : language === "ar"
      ? "افتح قائمة المتصفح، ثم اختر «تثبيت التطبيق» أو «إضافة إلى الشاشة الرئيسية»."
      : "Open your browser menu, then choose “Install app” or “Add to Home Screen.”";
  instructions.hidden = false;
}

applyWelcomeLanguage();
if (isStandalone() || hasSeenWelcome()) {
  welcome.hidden = true;
  authScreen.inert = false;
  appScreen.inert = false;
} else {
  welcome.hidden = false;
  authScreen.inert = true;
  appScreen.inert = true;
  requestAnimationFrame(() => continueButton.focus({ preventScroll: true }));
}

continueButton.addEventListener("click", closeWelcome);
installButton.addEventListener("click", async () => {
  if (!deferredInstallPrompt) {
    showInstallInstructions();
    return;
  }
  await deferredInstallPrompt.prompt();
  const choice = await deferredInstallPrompt.userChoice;
  deferredInstallPrompt = null;
  if (choice.outcome === "accepted") closeWelcome();
  else showInstallInstructions();
});

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredInstallPrompt = event;
});
window.addEventListener("appinstalled", closeWelcome);

function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) return;
  navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch((error) => {
    console.warn("Service worker registration failed", error);
  });
}
if (document.readyState === "complete") registerServiceWorker();
else window.addEventListener("load", registerServiceWorker, { once: true });
