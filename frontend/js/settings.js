// MangoToon Settings Page
// Phase 17.8: Reader, Comic and Settings UX Overhaul

(function () {
  "use strict";

  var saveBtn = document.getElementById("settings-save");
  var cancelBtn = document.getElementById("settings-cancel");
  var toast = document.getElementById("settings-toast");
  var toastMsg = document.getElementById("settings-toast-msg");
  var toastTimer = null;

  var rangeConcurrency = document.getElementById("set-download-concurrency");
  var rangeConcurrencyLabel = document.getElementById("set-download-concurrency-label");
  var rangeAdvanceDelay = document.getElementById("set-reader-auto-advance-delay");
  var rangeAdvanceDelayLabel = document.getElementById("set-delay-label");

  var originalSettings = null;

  document.addEventListener("DOMContentLoaded", function () {
    init();
  });

  function init() {
    if (saveBtn) {
      saveBtn.addEventListener("click", onSave);
    }

    if (cancelBtn) {
      cancelBtn.addEventListener("click", onCancel);
    }

    if (rangeConcurrency && rangeConcurrencyLabel) {
      rangeConcurrency.addEventListener("input", function () {
        rangeConcurrencyLabel.textContent = rangeConcurrency.value;
      });
    }

    if (rangeAdvanceDelay && rangeAdvanceDelayLabel) {
      rangeAdvanceDelay.addEventListener("input", function () {
        rangeAdvanceDelayLabel.textContent = rangeAdvanceDelay.value + "s";
      });
    }

    loadSettings();
  }

  function loadSettings() {
    API.get("/settings")
      .then(function (settings) {
        originalSettings = JSON.parse(JSON.stringify(settings));
        populateForm(settings);
      })
      .catch(function (err) {
        console.error("Failed to load settings:", err);
        showToast("Could not load settings. Please try again.", "error");
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
    setRange("set-reader-auto-advance-delay", s.reader_auto_advance_delay, rangeAdvanceDelayLabel, true);
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

  function setRange(id, value, labelEl, addSuffix) {
    var el = document.getElementById(id);
    if (!el) return;
    el.value = value !== undefined ? value : el.getAttribute("min") || 0;
    if (labelEl) {
      labelEl.textContent = el.value + (addSuffix ? "s" : "");
    }
  }

  function onCancel() {
    if (originalSettings) {
      populateForm(originalSettings);
      showToast("Settings restored to saved values.");
    } else {
      window.location.href = "/";
    }
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

  function onSave() {
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.textContent = "Saving...";
    }

    var payload = collectForm();

    API.post("/settings", payload)
      .then(function () {
        originalSettings = JSON.parse(JSON.stringify(payload));
        showToast("Settings saved successfully.");
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
        if (saveBtn) {
          saveBtn.disabled = false;
          saveBtn.textContent = "Save Settings";
        }
      });
  }

  function showToast(msg, type) {
    if (!toast || !toastMsg) return;
    clearTimeout(toastTimer);

    toastMsg.textContent = msg;
    toast.className = "toast" + (type === "error" ? " toast-error" : "");
    toast.hidden = false;

    toastTimer = setTimeout(function () {
      toast.hidden = true;
    }, 3500);
  }
})();
