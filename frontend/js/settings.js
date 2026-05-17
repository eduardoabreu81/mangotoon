// MangoToon Settings Page

(function () {
  "use strict";

  var form = document.getElementById("settings-form");
  var toast = document.getElementById("settings-toast");
  var toastMsg = document.getElementById("settings-toast-msg");
  var toastTimer = null;

  var rangeConcurrency = document.getElementById("set-download-concurrency");
  var rangeConcurrencyLabel = document.getElementById("set-download-concurrency-label");
  var rangeAdvanceDelay = document.getElementById("set-reader-auto-advance-delay");
  var rangeAdvanceDelayLabel = document.getElementById("set-delay-label");

  document.addEventListener("DOMContentLoaded", function () {
    init();
  });

  function init() {
    form.addEventListener("submit", onSave);

    document.getElementById("settings-cancel").addEventListener("click", function () {
      window.location.href = "/";
    });

    if (rangeConcurrency && rangeConcurrencyLabel) {
      rangeConcurrency.addEventListener("input", function () {
        rangeConcurrencyLabel.textContent = rangeConcurrency.value;
      });
    }

    if (rangeAdvanceDelay && rangeAdvanceDelayLabel) {
      rangeAdvanceDelay.addEventListener("input", function () {
        rangeAdvanceDelayLabel.textContent = rangeAdvanceDelay.value;
      });
    }

    loadSettings();
  }

  function loadSettings() {
    API.get("/settings")
      .then(function (settings) {
        populateForm(settings);
      })
      .catch(function (err) {
        console.error("Failed to load settings:", err);
        showToast("Could not load settings.", "error");
      });
  }

  function populateForm(s) {
    setValue("set-download-auto-start", s.download_auto_start);
    setValue("set-download-default-chapters", s.download_default_chapters);
    setRange("set-download-concurrency", s.download_concurrency, rangeConcurrencyLabel);
    setValue("set-rate-limit", s.rate_limit_per_domain);
    setValue("set-library-path", s.library_path);
    setValue("set-reader-default-fit", s.reader_default_fit);
    setValue("set-reader-auto-advance", s.reader_auto_advance);
    setRange("set-reader-auto-advance-delay", s.reader_auto_advance_delay, rangeAdvanceDelayLabel);
    setValue("set-reader-progress-bar", s.reader_show_progress_bar);
    setValue("set-theme", s.theme);
    setValue("set-language", s.language);
  }

  function setValue(id, value) {
    var el = document.getElementById(id);
    if (!el) return;
    if (el.type === "checkbox") {
      el.checked = !!value;
    } else {
      el.value = value !== undefined && value !== null ? value : "";
    }
  }

  function setRange(id, value, labelEl) {
    var el = document.getElementById(id);
    if (!el) return;
    el.value = value !== undefined ? value : el.getAttribute("min") || 0;
    if (labelEl) labelEl.textContent = el.value;
  }

  function collectForm() {
    var s = {};

    s.download_auto_start = getCheckbox("set-download-auto-start");
    s.download_default_chapters = getValue("set-download-default-chapters");
    s.download_concurrency = parseInt(getValue("set-download-concurrency"), 10) || 2;
    s.rate_limit_per_domain = parseFloat(getValue("set-rate-limit")) || 1.0;
    s.library_path = getValue("set-library-path").trim() || "./data/comics";
    s.reader_default_fit = getValue("set-reader-default-fit");
    s.reader_auto_advance = getCheckbox("set-reader-auto-advance");
    s.reader_auto_advance_delay = parseInt(getValue("set-reader-auto-advance-delay"), 10) || 4;
    s.reader_show_progress_bar = getCheckbox("set-reader-progress-bar");
    s.theme = getValue("set-theme");
    s.language = getValue("set-language");

    return s;
  }

  function getValue(id) {
    var el = document.getElementById(id);
    return el ? el.value : "";
  }

  function getCheckbox(id) {
    var el = document.getElementById(id);
    return el ? el.checked : false;
  }

  function onSave(e) {
    e.preventDefault();

    var submitBtn = form.querySelector('[type="submit"]');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Saving...";
    }

    var payload = collectForm();

    API.post("/settings", payload)
      .then(function () {
        showToast("Settings saved.");
      })
      .catch(function (err) {
        var msg = "Failed to save settings.";
        if (err.detail) {
          msg = typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
        } else if (err.message) {
          msg = err.message;
        }
        showToast(msg, "error");
      })
      .finally(function () {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = "Save Settings";
        }
      });
  }

  function showToast(msg, type) {
    if (!toast || !toastMsg) return;
    clearTimeout(toastTimer);

    toastMsg.textContent = msg;
    toast.className = "settings-toast" + (type === "error" ? " settings-toast-error" : "");
    toast.hidden = false;

    toastTimer = setTimeout(function () {
      toast.hidden = true;
    }, 2500);
  }
})();
