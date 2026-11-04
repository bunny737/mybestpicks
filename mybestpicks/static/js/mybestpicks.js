/* Optional Google Analytics 4, loaded only after the visitor accepts (invariant 9).
   Nothing is sent to Google, and no Google script is requested, before then. */
(function () {
  "use strict";

  var banner = document.getElementById("analytics-consent");
  if (!banner) { return; }

  var id = banner.getAttribute("data-ga4-id");
  var COOKIE = "analytics_consent";

  function readChoice() {
    var match = document.cookie.match(/(?:^|;\s*)analytics_consent=(granted|denied)/);
    return match ? match[1] : null;
  }

  function saveChoice(value) {
    var secure = location.protocol === "https:" ? "; Secure" : "";
    document.cookie = COOKIE + "=" + value + "; Max-Age=15552000; Path=/; SameSite=Lax" + secure;
  }

  function clearGoogleCookies() {
    var host = location.hostname.split(".");
    var domains = ["", location.hostname];
    if (host.length > 1) { domains.push("." + host.slice(-2).join(".")); }
    document.cookie.split(";").forEach(function (c) {
      var name = c.split("=")[0].trim();
      if (name === "_ga" || name.indexOf("_ga_") === 0) {
        domains.forEach(function (d) {
          document.cookie = name + "=; Max-Age=0; Path=/" + (d ? "; Domain=" + d : "");
        });
      }
    });
  }

  function loadAnalytics() {
    if (window.__ga4Loaded || !id) { return; }
    window.__ga4Loaded = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag("js", new Date());
    window.gtag("config", id);
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(id);
    document.head.appendChild(s);
  }

  var choice = readChoice();
  if (choice === "granted") {
    loadAnalytics();
  } else if (choice === null) {
    banner.hidden = false;
  }

  banner.addEventListener("click", function (event) {
    var button = event.target.closest("[data-analytics-choice]");
    if (!button) { return; }
    var value = button.getAttribute("data-analytics-choice");
    saveChoice(value);
    banner.hidden = true;
    if (value === "granted") { loadAnalytics(); } else { clearGoogleCookies(); }
  });

  /* Footer link lets visitors change their mind later. */
  var reopen = document.querySelectorAll("[data-analytics-reopen]");
  Array.prototype.forEach.call(reopen, function (el) {
    el.addEventListener("click", function (event) {
      event.preventDefault();
      banner.hidden = false;
      banner.focus();
    });
  });
})();
