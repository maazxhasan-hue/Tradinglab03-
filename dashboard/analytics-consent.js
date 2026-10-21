(function () {
  "use strict";
  // Set this only to the verified GA4 Web stream Measurement ID (G-XXXXXXXXXX).
  // A blank value intentionally disables all analytics until configuration is complete.
  let MEASUREMENT_ID = "";
  const PRODUCTION_HOSTS = new Set(["nexora-ai-public.netlify.app"]);
  const CONSENT_KEY = "nexora.analytics-consent.v1";
  const ALLOWED_KEY_EVENTS = new Set(["generate_lead", "sign_up", "purchase"]);

  if (!PRODUCTION_HOSTS.has(String(window.location.hostname || "").toLowerCase())) return;
  const gpc = navigator.globalPrivacyControl === true;
  const dnt = String(navigator.doNotTrack || window.doNotTrack || "").toLowerCase() === "1";
  if (gpc || dnt) return;

  let loaded = false;
  let consent = "unknown";

  function gtag() {
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push(arguments);
  }
  function initConsentMode() {
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
    window.gtag("consent", "default", {
      analytics_storage: "denied",
      ad_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied",
      functionality_storage: "granted",
      security_storage: "granted"
    });
  }
  function loadGoogleAnalytics() {
    if (loaded || consent !== "granted") return;
    loaded = true;
    window.gtag("consent", "update", {
      analytics_storage: "granted",
      ad_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied"
    });
    window.gtag("js", new Date());
    window.gtag("config", MEASUREMENT_ID, {
      send_page_view: true,
      allow_google_signals: false,
      allow_ad_personalization_signals: false
    });
    const tag = document.createElement("script");
    tag.async = true;
    tag.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(MEASUREMENT_ID);
    tag.referrerPolicy = "strict-origin-when-cross-origin";
    document.head.append(tag);
  }
  function saveConsent(value) {
    consent = value;
    try { window.localStorage.setItem(CONSENT_KEY, value); } catch (e) {}
    if (value === "granted") loadGoogleAnalytics();
    banner.hidden = true;
    settingsButton.hidden = false;
  }
  function makeButton(label, primary, handler) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.style.cssText = "border:1px solid " + (primary ? "#0071e3" : "#c7c7cc") + ";border-radius:999px;padding:10px 15px;min-height:42px;font:600 14px/1.2 system-ui,-apple-system,Segoe UI,sans-serif;background:" + (primary ? "#0071e3" : "#fff") + ";color:" + (primary ? "#fff" : "#1d1d1f") + ";cursor:pointer";
    button.addEventListener("click", handler);
    button.addEventListener("focus", function () { button.style.outline = "3px solid #71a7f8"; button.style.outlineOffset = "2px"; });
    button.addEventListener("blur", function () { button.style.outline = ""; });
    return button;
  }
  const banner = document.createElement("section");
  banner.hidden = true;
  banner.setAttribute("role", "region");
  banner.setAttribute("aria-label", "Analytics preferences");
  banner.style.cssText = "position:fixed;z-index:2147483000;left:16px;right:16px;bottom:16px;margin:auto;max-width:780px;padding:18px;background:#fff;color:#1d1d1f;border:1px solid #d2d2d7;border-radius:18px;box-shadow:0 14px 48px rgba(0,0,0,.22);font:14px/1.55 system-ui,-apple-system,Segoe UI,sans-serif";
  const heading = document.createElement("h2");
  heading.textContent = "Your privacy choices";
  heading.style.cssText = "font:700 18px/1.3 system-ui,-apple-system,Segoe UI,sans-serif;margin:0 0 6px;color:#1d1d1f";
  const copy = document.createElement("p");
  copy.textContent = "Optional analytics help Nexora AI understand visits, traffic sources, and popular pages. Analytics stays off unless you allow it. Advertising and ad personalisation storage remain disabled.";
  copy.style.cssText = "margin:0 0 14px;color:#515154";
  const actions = document.createElement("div");
  actions.style.cssText = "display:flex;flex-wrap:wrap;gap:8px;justify-content:flex-end";
  actions.append(
    makeButton("Only necessary", false, function () { saveConsent("denied"); }),
    makeButton("Allow analytics", true, function () { saveConsent("granted"); })
  );
  banner.append(heading, copy, actions);
  const settingsButton = makeButton("Cookie settings", false, function () { banner.hidden = false; });
  settingsButton.hidden = true;
  settingsButton.style.cssText += ";position:fixed;z-index:2147482999;right:12px;bottom:12px;font-size:12px;box-shadow:0 4px 18px rgba(0,0,0,.15)";
  document.addEventListener("DOMContentLoaded", async function () {
    // Read only the public Measurement ID from the Worker. No tracking request is
    // sent to Google until the visitor explicitly grants analytics consent.
    try {
      const response = await fetch("https://tradinglab03-intake.maazxhasan.workers.dev/api/analytics/config", {
        method: "GET", headers: { "Accept": "application/json" }, mode: "cors", credentials: "omit", cache: "no-store"
      });
      if (!response.ok) return;
      const config = await response.json();
      if (!config || config.configured !== true || !/^G-[A-Z0-9]+$/.test(String(config.measurement_id || ""))) return;
      MEASUREMENT_ID = String(config.measurement_id);
    } catch (error) {
      return;
    }
    initConsentMode();
    document.body.append(banner, settingsButton);
    let existing = "";
    try { existing = window.localStorage.getItem(CONSENT_KEY) || ""; } catch (e) {}
    if (existing === "granted" || existing === "denied") {
      consent = existing;
      settingsButton.hidden = false;
      if (consent === "granted") loadGoogleAnalytics();
    } else {
      consent = "unknown";
      banner.hidden = false;
      settingsButton.hidden = true;
    }
  });

  window.nexoraAnalytics = {
    trackKeyEvent: function (eventName) {
      if (!loaded || consent !== "granted" || !ALLOWED_KEY_EVENTS.has(eventName)) return false;
      window.gtag("event", eventName);
      return true;
    }
  };
})();