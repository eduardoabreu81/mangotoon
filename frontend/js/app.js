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

  var addModal = document.getElementById("add-modal");
  var addForm = document.getElementById("add-form");
  var addCancel = document.getElementById("add-cancel");
  var addUrl = document.getElementById("add-url");
  var addSourceDetected = document.getElementById("add-source-detected");

  var contextMenu = document.getElementById("context-menu");
  var contextComicId = null;

  var _pollTimers = {};

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
    addForm && addForm.addEventListener("submit", onAddSubmit);
    addUrl && addUrl.addEventListener("input", detectSource);

    if (contextMenu) {
      contextMenu.addEventListener("click", handleContextAction);
      document.addEventListener("click", hideContextMenu);
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") hideContextMenu();
      });
    }

    updateApiStatus();
    loadLibrary();
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

  function onAddSubmit(e) {
    e.preventDefault();
    var url = (addUrl.value || "").trim();

    showAddError("");

    if (!url) {
      showAddError("Please enter a MangaDex URL.");
      return;
    }

    var submitBtn = addForm.querySelector('[type="submit"]');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Adding...";
    }

    API.post("/library/add", { url: url })
      .then(function (data) {
        if (data.duplicate) {
          showAddError("Already in your library.");
          setTimeout(function () {
            closeAddModal();
            loadLibrary();
          }, 1500);
        } else {
          closeAddModal();
          loadLibrary();
          if (data.comic && data.comic.comic_id) {
            startPolling(data.comic.comic_id);
          }
        }
      })
      .catch(function (err) {
        var msg = "Failed to add manga.";
        if (err.detail) {
          if (typeof err.detail === "string") {
            msg = err.detail;
          } else if (err.detail.error && err.detail.error.message) {
            msg = err.detail.error.message;
          }
        } else if (err.message) {
          msg = err.message;
        }
        showAddError(msg);
      })
      .finally(function () {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = "Add";
        }
      });
  }

  function openAddModal() {
    if (addModal) {
      addModal.hidden = false;
      addUrl && addUrl.focus();
    }
  }

  function closeAddModal() {
    if (addModal) {
      addModal.hidden = true;
      addForm && addForm.reset();
      addSourceDetected && (addSourceDetected.textContent = "");
      showAddError("");
    }
  }

  function detectSource() {
    var url = addUrl.value.trim();
    if (!url) {
      addSourceDetected.textContent = "";
      return;
    }
    if (url.indexOf("mangadex.org") !== -1) {
      addSourceDetected.textContent = "Detected: MangaDex";
    } else {
      addSourceDetected.textContent = "Source not recognized";
    }
  }

  function showAddError(msg) {
    var errEl = document.getElementById("add-error");
    if (!errEl) return;
    errEl.textContent = msg;
    errEl.hidden = !msg;
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

    var dlBtn = card.querySelector("[data-download]");
    if (dlBtn && status.status === "complete") {
      dlBtn.hidden = true;
    }
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
        window.location.href = "/reader?comic=" + encodeURIComponent(contextComicId);
        break;
      case "download":
        triggerDownload(contextComicId);
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

    API.post("/library/" + encodeURIComponent(comicId) + "/update", {
      status: "complete",
    })
      .then(function () {
        loadLibrary();
      })
      .catch(function (err) {
        console.error("Failed to update status:", err);
      });
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

      var card = e.target.closest(".comic-card");
      if (card) {
        var comicId = card.dataset.comicId;
        if (comicId) {
          window.location.href = "/reader?comic=" + encodeURIComponent(comicId);
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
