// MangoToon Frontend - Application Shell

(function () {
  "use strict";

  var library = [];
  var filtered = [];

  var statusFilter = "all";
  var sourceFilter = "all";
  var sortBy = "added";

  var statusEl = document.getElementById("api-status");
  var gridEl = document.getElementById("library-grid");
  var emptyEl = document.getElementById("empty-library");
  var loadingEl = document.getElementById("library-loading");
  var searchEl = document.getElementById("library-search");
  var addBtn = document.getElementById("btn-add");

  var sidebarEl = document.getElementById("sidebar");
  var sidebarOverlay = document.getElementById("sidebar-overlay");
  var sidebarToggle = document.getElementById("btn-sidebar-toggle");
  var sidebarClose = document.getElementById("sidebar-close");
  var sidebarSort = document.getElementById("sidebar-sort");
  var sidebarCount = document.getElementById("sidebar-count");
  var filterStatusEl = document.getElementById("filter-status");
  var filterSourceEl = document.getElementById("filter-source");

  var _sourcesCache = [];

  var _wizardUrl = "";
  var _wizardPreview = null;

  var addModal = document.getElementById("add-modal");
  var addCancel = document.getElementById("add-cancel");
  var addUrl = document.getElementById("add-url");
  var addSourceDetected = document.getElementById("add-source-detected");
  var addCapabilities = document.getElementById("add-source-capabilities");
  var addStep1 = document.getElementById("add-step1");
  var addStep2 = document.getElementById("add-step2");
  var addStep3 = document.getElementById("add-step3");
  var btnPreview = document.getElementById("btn-preview");
  var btnBackToUrl = document.getElementById("btn-back-to-url");
  var btnConfirmStep = document.getElementById("btn-confirm-step");
  var btnBackToPreview = document.getElementById("btn-back-to-preview");
  var btnConfirm = document.getElementById("btn-confirm");
  var previewCover = document.getElementById("preview-cover");
  var previewPlaceholder = document.getElementById("preview-placeholder");
  var previewTitle = document.getElementById("preview-title");
  var previewSource = document.getElementById("preview-source");
  var previewChapters = document.getElementById("preview-chapters");
  var previewLanguages = document.getElementById("preview-languages");
  var previewDescription = document.getElementById("preview-description");
  var previewDuplicate = document.getElementById("preview-duplicate");
  var previewWarnings = document.getElementById("preview-warnings");
  var addAutoDownload = document.getElementById("add-auto-download");
  var addErrorStep2 = document.getElementById("add-error-step2");
  var addErrorStep3 = document.getElementById("add-error-step3");

  var contextMenu = document.getElementById("context-menu");
  var contextComicId = null;

  var _pollTimers = {};

  var toastEl = document.getElementById("toast");
  var toastMsg = document.getElementById("toast-msg");
  var _toastTimer = null;

  document.addEventListener("DOMContentLoaded", function () {
    init();
  });

  function init() {
    loadPersistedState();

    searchEl && searchEl.addEventListener("input", applyFilters);
    addBtn && addBtn.addEventListener("click", openAddModal);

    sidebarToggle && sidebarToggle.addEventListener("click", toggleSidebar);
    sidebarClose && sidebarClose.addEventListener("click", closeSidebar);
    sidebarOverlay && sidebarOverlay.addEventListener("click", closeSidebar);
    sidebarSort && sidebarSort.addEventListener("change", function () {
      sortBy = sidebarSort.value;
      persistSidebarState();
      applyFilters();
    });

    filterStatusEl && filterStatusEl.addEventListener("click", function (e) {
      var chip = e.target.closest("[data-status]");
      if (!chip) return;
      statusFilter = chip.dataset.status;
      updateFilterChips(filterStatusEl, chip);
      persistSidebarState();
      applyFilters();
    });

    filterSourceEl && filterSourceEl.addEventListener("click", function (e) {
      var chip = e.target.closest("[data-source]");
      if (!chip) return;
      sourceFilter = chip.dataset.source;
      updateFilterChips(filterSourceEl, chip);
      persistSidebarState();
      applyFilters();
    });

    addCancel && addCancel.addEventListener("click", closeAddModal);
    btnPreview && btnPreview.addEventListener("click", onPreviewClick);
    btnBackToUrl && btnBackToUrl.addEventListener("click", function () { showWizardStep(1); });
    btnConfirmStep && btnConfirmStep.addEventListener("click", onContinueToConfirm);
    btnBackToPreview && btnBackToPreview.addEventListener("click", function () { showWizardStep(2); });
    btnConfirm && btnConfirm.addEventListener("click", onConfirmClick);
    addUrl && addUrl.addEventListener("input", detectSource);

    if (contextMenu) {
      contextMenu.addEventListener("click", handleContextAction);
      document.addEventListener("click", hideContextMenu);
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") hideContextMenu();
      });
    }

    updateApiStatus();
    loadSources();
    loadLibrary();
  }

  function loadSources() {
    API.getSources().then(function (sources) {
      _sourcesCache = sources;
      var container = filterSourceEl;
      if (!container) return;
      sources.forEach(function (src) {
        var key = src.name.toLowerCase();
        var chip = document.createElement("button");
        chip.className = "filter-chip";
        chip.dataset.source = key;
        chip.textContent = src.name;
        chip.addEventListener("click", function () {
          sourceFilter = key;
          updateFilterChips(container, chip);
          persistSidebarState();
          applyFilters();
        });
        container.appendChild(chip);
      });
    }).catch(function (err) {
      console.warn("Failed to load sources:", err);
    });
  }

  function loadPersistedState() {
    try {
      var raw = localStorage.getItem("mangotoon_sidebar");
      if (raw) {
        var state = JSON.parse(raw);
        statusFilter = state.statusFilter || "all";
        sourceFilter = state.sourceFilter || "all";
        sortBy = state.sortBy || "added";
      }
    } catch (e) {}
  }

  function persistSidebarState() {
    try {
      localStorage.setItem(
        "mangotoon_sidebar",
        JSON.stringify({
          statusFilter: statusFilter,
          sourceFilter: sourceFilter,
          sortBy: sortBy,
        })
      );
    } catch (e) {}
  }

  function syncSidebarUI() {
    if (sidebarSort) sidebarSort.value = sortBy;

    if (filterStatusEl) {
      var chips = filterStatusEl.querySelectorAll("[data-status]");
      chips.forEach(function (c) {
        c.classList.toggle("active", c.dataset.status === statusFilter);
      });
    }

    if (filterSourceEl) {
      var srcChips = filterSourceEl.querySelectorAll("[data-source]");
      srcChips.forEach(function (c) {
        c.classList.toggle("active", c.dataset.source === sourceFilter);
      });
    }
  }

  function updateFilterChips(container, activeChip) {
    var chips = container.querySelectorAll(".filter-chip");
    chips.forEach(function (c) {
      c.classList.toggle("active", c === activeChip);
    });
  }

  function toggleSidebar() {
    var open = sidebarEl && !sidebarEl.hidden;
    if (open) {
      closeSidebar();
    } else {
      openSidebar();
    }
  }

  function openSidebar() {
    if (sidebarEl) sidebarEl.hidden = false;
    if (sidebarOverlay) sidebarOverlay.hidden = false;
    document.body.classList.add("sidebar-open");
  }

  function closeSidebar() {
    if (sidebarEl) sidebarEl.hidden = true;
    if (sidebarOverlay) sidebarOverlay.hidden = true;
    document.body.classList.remove("sidebar-open");
  }

  function updateApiStatus() {
    if (!statusEl) return;
    statusEl.textContent = "Checking...";
    statusEl.dataset.state = "";

    API.get("/health")
      .then(function () {
        statusEl.textContent = "API online";
        statusEl.dataset.state = "ok";
      })
      .catch(function () {
        statusEl.textContent = "API offline";
        statusEl.dataset.state = "error";
      });
  }

  function loadLibrary() {
    showLoading(true);
    hideEmpty();

    API.get("/library")
      .then(function (data) {
        library = data.comics || [];
        syncSidebarUI();
        applyFilters();
      })
      .catch(function (err) {
        console.error("Failed to load library:", err);
        library = [];
        filtered = [];
        renderGrid();
      })
      .finally(function () {
        showLoading(false);
      });
  }

  function applyFilters() {
    var result = library.slice();

    var query = (searchEl && searchEl.value || "").toLowerCase().trim();
    if (query) {
      result = result.filter(function (comic) {
        return (comic.title || "").toLowerCase().indexOf(query) !== -1;
      });
    }

    if (statusFilter && statusFilter !== "all") {
      result = result.filter(function (comic) {
        var s = comic.status || "";
        switch (statusFilter) {
          case "reading":
            return s === "downloading" || s === "queued" || s === "metadata_fetching";
          case "completed":
            return s === "complete";
          case "downloaded":
            return s === "complete" || s === "partial" || (comic.downloaded_count > 0);
          case "pending":
            return s === "pending";
          default:
            return true;
        }
      });
    }

    if (sourceFilter && sourceFilter !== "all") {
      result = result.filter(function (comic) {
        return (comic.source || "").toLowerCase() === sourceFilter;
      });
    }

    switch (sortBy) {
      case "title":
        result.sort(function (a, b) {
          return (a.title || "").localeCompare(b.title || "");
        });
        break;
      case "read":
        result.sort(function (a, b) {
          var aTime = a.progress ? new Date(a.progress.updated_at).getTime() : 0;
          var bTime = b.progress ? new Date(b.progress.updated_at).getTime() : 0;
          return bTime - aTime;
        });
        break;
      case "progress":
        result.sort(function (a, b) {
          var aPct = a.chapter_count > 0 ? a.downloaded_count / a.chapter_count : 0;
          var bPct = b.chapter_count > 0 ? b.downloaded_count / b.chapter_count : 0;
          return bPct - aPct;
        });
        break;
      case "added":
      default:
        result.sort(function (a, b) {
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        });
        break;
    }

    filtered = result;
    renderGrid();
  }

  function renderGrid() {
    if (!gridEl) return;

    if (filtered.length === 0) {
      gridEl.innerHTML = "";
      showEmpty();
    } else {
      hideEmpty();
      gridEl.innerHTML = filtered
        .map(function (comic) {
          return renderCard(comic);
        })
        .join("");
    }

    updateCount();
  }

  function updateCount() {
    if (!sidebarCount) return;
    var total = library.length;
    var showing = filtered.length;
    if (total === showing) {
      sidebarCount.textContent = showing + " manga";
    } else {
      sidebarCount.textContent = showing + " / " + total + " manga";
    }
  }

  function renderCard(comic) {
    var coverHtml;
    if (comic.cover_url) {
      coverHtml =
        '<img class="comic-cover" src="' +
        escapeAttr(comic.cover_url) +
        '" alt="' +
        escapeHtml(comic.title) +
        '" loading="lazy">';
    } else {
      coverHtml =
        '<div class="comic-cover-placeholder" aria-hidden="true">' +
        escapeHtml(comic.title.charAt(0).toUpperCase()) +
        "</div>";
    }

    var progressHtml = "";
    if (comic.downloaded_count > 0 || comic.chapter_count > 0) {
      var pct =
        comic.chapter_count > 0
          ? Math.round((comic.downloaded_count / comic.chapter_count) * 100)
          : 0;
      progressHtml =
        '<div class="comic-progress">' +
        '<div class="comic-progress-bar" style="width:' +
        pct +
        '%"></div>' +
        "</div>" +
        '<div class="comic-chapter-info">' +
        comic.downloaded_count +
        " / " +
        comic.chapter_count +
        " chapters" +
        "</div>";
    }

    var sourceHtml = comic.source
      ? '<span class="comic-source">' + escapeHtml(comic.source) + "</span>"
      : "";

    return (
      '<article class="comic-card" data-comic-id="' +
      escapeAttr(comic.comic_id) +
      '">' +
      coverHtml +
      '<div class="comic-info">' +
      '<h3 class="comic-title" title="' +
      escapeAttr(comic.title) +
      '">' +
      escapeHtml(comic.title) +
      "</h3>" +
      '<div class="comic-meta">' +
      sourceHtml +
      '<span class="status-badge status-' +
      escapeAttr(comic.status) +
      '">' +
      escapeHtml(comic.status) +
      "</span>" +
      "</div>" +
      progressHtml +
      (comic.status !== "complete" && comic.chapter_count > comic.downloaded_count
        ? '<button class="card-download" title="Download chapters" aria-label="Download chapters" data-download="' +
          escapeAttr(comic.comic_id) +
          '">&#x2B07;</button>'
        : "") +
      '<div class="card-controls" hidden>' +
        '<button class="card-ctrl-btn card-pause" title="Pause download" data-pause="' +
          escapeAttr(comic.comic_id) + '">❚❚</button>' +
        '<button class="card-ctrl-btn card-resume" title="Resume download" data-resume="' +
          escapeAttr(comic.comic_id) + '">▶</button>' +
        '<button class="card-ctrl-btn card-cancel" title="Cancel download" data-cancel="' +
          escapeAttr(comic.comic_id) + '">✕</button>' +
        '<button class="card-ctrl-btn card-retry" title="Retry download" data-retry="' +
          escapeAttr(comic.comic_id) + '">↻</button>' +
      '</div>' +
      '<button class="card-delete" title="Delete ' +
      escapeAttr(comic.title) +
      '" aria-label="Delete ' +
      escapeAttr(comic.title) +
      '" data-delete="' +
      escapeAttr(comic.comic_id) +
      '">&times;</button>' +
      "</div>" +
      "</article>"
    );
  }

  function onPreviewClick() {
    var url = (addUrl.value || "").trim();
    showAddError("");

    if (!url) {
      showAddError("Please enter a manga URL.");
      return;
    }

    btnPreview.disabled = true;
    btnPreview.textContent = "Loading...";

    API.previewImport(url)
      .then(function (data) {
        _wizardUrl = url;
        _wizardPreview = data;
        showWizardStep(2);
        renderPreview(data);
      })
      .catch(function (err) {
        var msg = "Failed to preview manga.";
        if (err.detail) {
          if (typeof err.detail === "string") msg = err.detail;
          else if (err.detail.error && err.detail.error.message) msg = err.detail.error.message;
        } else if (err.message) {
          msg = err.message;
        }
        showAddError(msg);
      })
      .finally(function () {
        btnPreview.disabled = false;
        btnPreview.textContent = "Preview";
      });
  }

  function onContinueToConfirm() {
    showWizardStep(3);
  }

  function onConfirmClick() {
    var titleOverride = (document.getElementById("add-title-override").value || "").trim();
    var autoDownload = addAutoDownload ? addAutoDownload.checked : true;
    var payload = { url: _wizardUrl, auto_download: autoDownload };
    if (titleOverride) payload.title = titleOverride;

    hideAddErrors();
    btnConfirm.disabled = true;
    btnConfirm.textContent = "Importing...";

    API.confirmImport(payload)
      .then(function (data) {
        closeAddModal();
        loadLibrary();
        if (data.comic_id && !data.duplicate) {
          startPolling(data.comic_id);
        }
      })
      .catch(function (err) {
        var msg = "Failed to add manga.";
        if (err.detail) {
          if (typeof err.detail === "string") msg = err.detail;
          else if (err.detail.error && err.detail.error.message) msg = err.detail.error.message;
        } else if (err.message) {
          msg = err.message;
        }
        showErrorStep3(msg);
      })
      .finally(function () {
        btnConfirm.disabled = false;
        btnConfirm.textContent = "Confirm";
      });
  }

  function showWizardStep(step) {
    var panels = [addStep1, addStep2, addStep3];
    panels.forEach(function (panel, i) {
      if (panel) panel.hidden = (i + 1 !== step);
    });
    updateStepIndicators(step);
    hideAddErrors();

    if (step === 1) {
      addUrl && addUrl.focus();
    }
  }

  function updateStepIndicators(step) {
    var indicators = document.querySelectorAll(".wizard-step");
    indicators.forEach(function (el) {
      var s = parseInt(el.dataset.wizardStep, 10);
      el.classList.remove("active", "completed");
      if (s === step) el.classList.add("active");
      else if (s < step) el.classList.add("completed");
    });
  }

  function renderPreview(data) {
    if (data.cover_url) {
      if (previewCover) {
        previewCover.src = data.cover_url;
        previewCover.hidden = false;
      }
      if (previewPlaceholder) previewPlaceholder.hidden = true;
    } else {
      if (previewCover) previewCover.hidden = true;
      if (previewPlaceholder) {
        previewPlaceholder.textContent = (data.title || "?").charAt(0).toUpperCase();
        previewPlaceholder.hidden = false;
      }
    }

    if (previewTitle) previewTitle.textContent = data.title || "Unknown Title";
    if (previewSource) previewSource.textContent = data.source || "";

    var chapterText = data.chapter_count + " chapter" + (data.chapter_count !== 1 ? "s" : "");
    if (previewChapters) previewChapters.textContent = chapterText;

    if (previewLanguages && data.languages && data.languages.length > 0) {
      previewLanguages.textContent = data.languages.join(", ");
      previewLanguages.hidden = false;
    } else if (previewLanguages) {
      previewLanguages.hidden = true;
    }

    if (previewDescription) {
      previewDescription.textContent = data.description || "";
      previewDescription.hidden = !data.description;
    }

    if (previewDuplicate) previewDuplicate.hidden = !data.duplicate;

    if (previewWarnings) {
      if (data.warnings && data.warnings.length > 0) {
        previewWarnings.innerHTML = data.warnings
          .map(function (w) { return '<span class="preview-warning-item">' + escapeHtml(w) + '</span>'; })
          .join("");
        previewWarnings.hidden = false;
      } else {
        previewWarnings.hidden = true;
      }
    }
  }

  function openAddModal() {
    if (addModal) {
      addModal.hidden = false;
      showWizardStep(1);
      _wizardUrl = "";
      _wizardPreview = null;
      addUrl.value = "";
      var titleOverride = document.getElementById("add-title-override");
      if (titleOverride) titleOverride.value = "";
      if (addAutoDownload) addAutoDownload.checked = true;
      addSourceDetected && (addSourceDetected.textContent = "");
      addCapabilities && (addCapabilities.innerHTML = "");
    }
  }

  function closeAddModal() {
    if (addModal) {
      addModal.hidden = true;
      _wizardUrl = "";
      _wizardPreview = null;
      addUrl.value = "";
      var titleOverride = document.getElementById("add-title-override");
      if (titleOverride) titleOverride.value = "";
      if (addAutoDownload) addAutoDownload.checked = true;
      addSourceDetected && (addSourceDetected.textContent = "");
      addCapabilities && (addCapabilities.innerHTML = "");
      hideAddErrors();
    }
  }

  function detectSource() {
    var url = addUrl.value.trim();
    if (!url) {
      addSourceDetected.textContent = "";
      addCapabilities && (addCapabilities.innerHTML = "");
      return;
    }
    API.detectSource(url).then(function (result) {
      if (result.supported) {
        addSourceDetected.textContent = "Detected: " + result.source;
        renderCapabilities(result.source);
      } else {
        addSourceDetected.textContent = "Currently supported: MangaDex title URLs only.";
        addCapabilities && (addCapabilities.innerHTML = "");
      }
    }).catch(function () {
      addSourceDetected.textContent = "Could not detect source";
      addCapabilities && (addCapabilities.innerHTML = "");
    });
  }

  function renderCapabilities(sourceName) {
    if (!addCapabilities) return;
    addCapabilities.innerHTML = "";

    var cached = null;
    for (var i = 0; i < _sourcesCache.length; i++) {
      if (_sourcesCache[i].name === sourceName) {
        cached = _sourcesCache[i];
        break;
      }
    }

    if (!cached || !cached.capabilities) return;

    var caps = cached.capabilities;
    var badges = [];

    if (caps.metadata) badges.push('<span class="cap-badge cap-metadata">Metadata</span>');
    if (caps.cover) badges.push('<span class="cap-badge cap-cover">Cover</span>');
    if (caps.chapter_list) badges.push('<span class="cap-badge cap-chapters">Chapters</span>');
    if (caps.page_download) badges.push('<span class="cap-badge cap-download">Download</span>');
    if (caps.supports_refresh) badges.push('<span class="cap-badge cap-refresh">Refresh</span>');
    if (caps.supports_search) badges.push('<span class="cap-badge cap-search">Search</span>');

    if (caps.languages && caps.languages.length > 0) {
      badges.push('<span class="cap-badge cap-lang">' + caps.languages.join(", ") + '</span>');
    }

    var html = badges.join("");

    var warnings = [];
    if (caps.requires_auth) {
      warnings.push('<span class="cap-warning">Requires login</span>');
    }
    if (caps.requires_javascript) {
      warnings.push('<span class="cap-warning">Requires browser</span>');
    }
    html += warnings.join("");

    addCapabilities.innerHTML = html;
  }

  function showAddError(msg) {
    var errEl = document.getElementById("add-error");
    if (!errEl) return;
    errEl.textContent = msg;
    errEl.hidden = !msg;
  }

  function showErrorStep3(msg) {
    if (addErrorStep3) {
      addErrorStep3.textContent = msg;
      addErrorStep3.hidden = !msg;
    }
  }

  function hideAddErrors() {
    showAddError("");
    if (addErrorStep2) { addErrorStep2.textContent = ""; addErrorStep2.hidden = true; }
    if (addErrorStep3) { addErrorStep3.textContent = ""; addErrorStep3.hidden = true; }
  }

  function triggerDownload(comicId) {
    API.post("/library/" + encodeURIComponent(comicId) + "/download", {})
      .then(function () {
        startPolling(comicId);
      })
      .catch(function (err) {
        console.error("Download trigger failed:", err);
      });
  }

  function startPolling(comicId) {
    if (_pollTimers[comicId]) return;
    _pollTimers[comicId] = setInterval(function () {
      pollStatus(comicId);
    }, 3000);
  }

  function stopPolling(comicId) {
    clearInterval(_pollTimers[comicId]);
    delete _pollTimers[comicId];
  }

  function pollStatus(comicId) {
    API.get("/downloads/" + encodeURIComponent(comicId) + "/status")
      .then(function (status) {
        updateCardLive(comicId, status);
        if (
          status.status === "complete" ||
          status.status === "error" ||
          status.status === "partial"
        ) {
          stopPolling(comicId);
          loadLibrary();
        }
      })
      .catch(function () {
        stopPolling(comicId);
      });
  }

  function updateCardLive(comicId, status) {
    var card = gridEl.querySelector(
      '[data-comic-id="' + escapeAttr(comicId) + '"]'
    );
    if (!card) return;

    var badge = card.querySelector(".status-badge");
    if (badge) {
      badge.className = "status-badge status-" + status.status;
      badge.textContent = status.status;
    }

    var pct =
      status.total_chapters > 0
        ? Math.round(
            (status.downloaded_chapters / status.total_chapters) * 100
          )
        : 0;
    var bar = card.querySelector(".comic-progress-bar");
    if (bar) bar.style.width = pct + "%";

    var info = card.querySelector(".comic-chapter-info");
    if (info) {
      info.textContent =
        status.downloaded_chapters +
        " / " +
        status.total_chapters +
        " chapters";
    }

    // Show error message if present
    var errorEl = card.querySelector(".comic-error-msg");
    if (status.error_message) {
      if (!errorEl) {
        errorEl = document.createElement("div");
        errorEl.className = "comic-error-msg";
        card.querySelector(".comic-info").appendChild(errorEl);
      }
      errorEl.textContent = status.error_message;
      errorEl.hidden = false;
    } else if (errorEl) {
      errorEl.hidden = true;
    }

    var dlBtn = card.querySelector("[data-download]");
    if (dlBtn && status.status === "complete") {
      dlBtn.hidden = true;
    }

    updateCardControls(card, comicId, status);
  }

  function updateCardControls(card, comicId, status) {
    var controls = card.querySelector(".card-controls");
    if (!controls) return;

    var pauseBtn = controls.querySelector("[data-pause]");
    var resumeBtn = controls.querySelector("[data-resume]");
    var cancelBtn = controls.querySelector("[data-cancel]");
    var retryBtn = controls.querySelector("[data-retry]");

    var s = status.status || "";

    var showPause = s === "downloading";
    var showResume = s === "paused";
    var showCancel = s === "downloading" || s === "queued" || s === "paused";
    var showRetry = s === "error";
    var showAny = showPause || showResume || showCancel || showRetry;

    controls.hidden = !showAny;
    if (pauseBtn) pauseBtn.hidden = !showPause;
    if (resumeBtn) resumeBtn.hidden = !showResume;
    if (cancelBtn) cancelBtn.hidden = !showCancel;
    if (retryBtn) retryBtn.hidden = !showRetry;
  }

  function pauseDownload(comicId) {
    API.post("/downloads/" + encodeURIComponent(comicId) + "/pause", {})
      .catch(function (err) {
        console.error("Pause failed:", err);
      });
  }

  function resumeDownload(comicId) {
    API.post("/downloads/" + encodeURIComponent(comicId) + "/resume", {})
      .then(function () {
        startPolling(comicId);
      })
      .catch(function (err) {
        console.error("Resume failed:", err);
      });
  }

  function cancelDownload(comicId) {
    API.post("/downloads/" + encodeURIComponent(comicId) + "/cancel", {})
      .then(function () {
        stopPolling(comicId);
        loadLibrary();
      })
      .catch(function (err) {
        console.error("Cancel failed:", err);
      });
  }

  function retryDownload(comicId) {
    triggerDownload(comicId);
  }

  // Context menu

  gridEl &&
    gridEl.addEventListener("contextmenu", function (e) {
      var card = e.target.closest(".comic-card");
      if (!card) return;

      e.preventDefault();
      contextComicId = card.dataset.comicId;

      if (!contextMenu || !contextComicId) return;

      contextMenu.style.top = e.clientY + "px";
      contextMenu.style.left = e.clientX + "px";
      contextMenu.hidden = false;
    });

  function hideContextMenu() {
    if (contextMenu) {
      contextMenu.hidden = true;
      contextComicId = null;
    }
  }

  function handleContextAction(e) {
    var actionBtn = e.target.closest("[data-action]");
    if (!actionBtn) return;
    var action = actionBtn.dataset.action;

    hideContextMenu();

    if (!contextComicId) return;

    switch (action) {
      case "read":
        window.location.href = "/comic?comic_id=" + encodeURIComponent(contextComicId);
        break;
      case "download":
        triggerDownload(contextComicId);
        break;
      case "refresh":
        refreshMetadata(contextComicId);
        break;
      case "delete":
        deleteComic(contextComicId, null);
        break;
      case "mark-completed":
        markCompleted(contextComicId);
        break;
    }
  }

  function markCompleted(comicId) {
    var comic = null;
    for (var i = 0; i < library.length; i++) {
      if (library[i].comic_id === comicId) {
        comic = library[i];
        break;
      }
    }
    if (!comic) return;

    API.post("/library/" + encodeURIComponent(comicId) + "/status", {
      status: "completed",
    })
      .then(function () {
        loadLibrary();
      })
      .catch(function (err) {
        console.error("Failed to update status:", err);
      });
  }

  function refreshMetadata(comicId) {
    showToast("Refreshing metadata...", "info");
    API.refreshComic(comicId)
      .then(function () {
        showToast("Metadata refreshed successfully.", "success");
        loadLibrary();
      })
      .catch(function (err) {
        var msg = "Failed to refresh metadata.";
        if (err.detail) {
          if (typeof err.detail === "string") msg = err.detail;
          else if (err.detail.error && err.detail.error.message) msg = err.detail.error.message;
        }
        showToast(msg, "error");
      });
  }

  function showToast(message, type) {
    if (!toastEl || !toastMsg) return;
    if (_toastTimer) clearTimeout(_toastTimer);

    toastMsg.textContent = message;
    toastEl.className = "toast" + (type === "error" ? " toast-error" : "");
    toastEl.hidden = false;

    _toastTimer = setTimeout(function () {
      toastEl.hidden = true;
    }, 3500);
  }

  gridEl &&
    gridEl.addEventListener("click", function (e) {
      var dlBtn = e.target.closest("[data-download]");
      if (dlBtn) {
        e.preventDefault();
        e.stopPropagation();
        var dlComicId = dlBtn.dataset.download;
        if (dlComicId) triggerDownload(dlComicId);
        return;
      }

      var btn = e.target.closest("[data-delete]");
      if (btn) {
        e.preventDefault();
        e.stopPropagation();
        var comicId = btn.dataset.delete;
        if (comicId) {
          deleteComic(comicId, btn.closest(".comic-card"));
        }
        return;
      }

      var pauseBtn = e.target.closest("[data-pause]");
      if (pauseBtn) {
        e.preventDefault();
        e.stopPropagation();
        pauseDownload(pauseBtn.dataset.pause);
        return;
      }

      var resumeBtn = e.target.closest("[data-resume]");
      if (resumeBtn) {
        e.preventDefault();
        e.stopPropagation();
        resumeDownload(resumeBtn.dataset.resume);
        return;
      }

      var cancelBtn = e.target.closest("[data-cancel]");
      if (cancelBtn) {
        e.preventDefault();
        e.stopPropagation();
        cancelDownload(cancelBtn.dataset.cancel);
        return;
      }

      var retryBtn = e.target.closest("[data-retry]");
      if (retryBtn) {
        e.preventDefault();
        e.stopPropagation();
        retryDownload(retryBtn.dataset.retry);
        return;
      }

      var card = e.target.closest(".comic-card");
      if (card) {
        var comicId = card.dataset.comicId;
        if (comicId) {
          window.location.href = "/comic?comic_id=" + encodeURIComponent(comicId);
        }
      }
    });

  function deleteComic(comicId, cardEl) {
    var title =
      cardEl && cardEl.querySelector(".comic-title")
        ? cardEl.querySelector(".comic-title").textContent
        : comicId;

    if (
      !confirm(
        'Delete "' + title + '" and all its downloaded chapters? This cannot be undone.'
      )
    ) {
      return;
    }

    API.del("/library/" + encodeURIComponent(comicId))
      .then(function () {
        library = library.filter(function (c) {
          return c.comic_id !== comicId;
        });
        applyFilters();
      })
      .catch(function (err) {
        console.error("Delete failed:", err);
        alert("Failed to delete: " + (err.detail || err.message));
      });
  }

  function showLoading(show) {
    if (loadingEl) {
      loadingEl.hidden = !show;
    }
  }

  function showEmpty() {
    if (emptyEl) {
      emptyEl.hidden = false;
    }
  }

  function hideEmpty() {
    if (emptyEl) {
      emptyEl.hidden = true;
    }
  }

  function escapeHtml(str) {
    var div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function escapeAttr(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/'/g, "&#39;");
  }
})();
