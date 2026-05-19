// MangoToon Frontend - Comic Detail Page
// Phase 17.8: Reader and Comic UX Overhaul

(function () {
  "use strict";

  var comicId = null;
  var comicData = null;
  var allChapters = [];
  var filteredChapters = [];
  var sortAsc = true;
  var pageSize = 50;
  var currentPage = 0;

  var loadingEl = document.getElementById("detail-loading");
  var errorEl = document.getElementById("detail-error");
  var errorMsg = document.getElementById("detail-error-msg");
  var contentEl = document.getElementById("detail-content");

  var topTitle = document.getElementById("detail-top-title");
  var coverImg = document.getElementById("detail-cover");
  var coverPlaceholder = document.getElementById("detail-cover-placeholder");
  var titleDisplay = document.getElementById("detail-title-display");
  var sourceEl = document.getElementById("detail-source");
  var statusBadge = document.getElementById("detail-status");
  var descriptionEl = document.getElementById("detail-description");
  var chapterCountEl = document.getElementById("detail-chapter-count");
  var downloadedCountEl = document.getElementById("detail-downloaded-count");
  var progressEl = document.getElementById("detail-progress");
  var progressFill = document.getElementById("detail-progress-fill");
  var progressText = document.getElementById("detail-progress-text");
  var readingProgressEl = document.getElementById("detail-reading-progress");
  var readingText = document.getElementById("detail-reading-text");

  var chapterListEl = document.getElementById("detail-chapter-list");
  var noChaptersEl = document.getElementById("detail-no-chapters");
  var chaptersFilterCount = document.getElementById("detail-chapters-filter-count");
  var chapterSearchInput = document.getElementById("chapter-search");
  var chapterFilterSelect = document.getElementById("chapter-filter");
  var chapterSortBtn = document.getElementById("chapter-sort");
  var chapterShowMoreBtn = document.getElementById("chapter-show-more");

  var btnRead = document.getElementById("btn-detail-read");
  var btnDownloadMissing = document.getElementById("btn-detail-download-missing");
  var btnRetryFailed = document.getElementById("btn-detail-retry-failed");
  var btnRefresh = document.getElementById("btn-detail-refresh");
  var btnDelete = document.getElementById("btn-detail-delete");

  var toastEl = document.getElementById("toast");
  var toastMsg = document.getElementById("toast-msg");
  var _toastTimer = null;

  var _pollTimer = null;

  document.addEventListener("DOMContentLoaded", function () {
    init();
  });

  function init() {
    var params = new URLSearchParams(window.location.search);
    comicId = params.get("comic_id");

    if (!comicId) {
      showError("No comic selected.");
      return;
    }

    btnRead.addEventListener("click", onRead);
    btnDownloadMissing.addEventListener("click", onDownloadMissing);
    btnRetryFailed.addEventListener("click", onRetryFailed);
    btnRefresh.addEventListener("click", onRefresh);
    btnDelete.addEventListener("click", onDelete);

    if (chapterSearchInput) {
      chapterSearchInput.addEventListener("input", debounce(onSearch, 200));
    }
    if (chapterFilterSelect) {
      chapterFilterSelect.addEventListener("change", onFilter);
    }
    if (chapterSortBtn) {
      chapterSortBtn.addEventListener("click", onToggleSort);
    }
    if (chapterShowMoreBtn) {
      chapterShowMoreBtn.addEventListener("click", onShowMore);
    }

    window.addEventListener("beforeunload", stopPolling);

    loadDetail();
  }

  function debounce(fn, ms) {
    var timer = null;
    return function () {
      clearTimeout(timer);
      timer = setTimeout(fn, ms);
    };
  }

  function loadDetail() {
    showLoading(true);
    hideError();
    if (contentEl) contentEl.hidden = true;

    API.get("/library/" + encodeURIComponent(comicId) + "/detail")
      .then(function (data) {
        comicData = data;
        allChapters = data.chapters || [];
        applyFilters();
        renderDetail();
        if (contentEl) contentEl.hidden = false;
      })
      .catch(function (err) {
        var msg = "Failed to load comic details.";
        if (err.detail) {
          if (typeof err.detail === "string") msg = err.detail;
          else if (err.detail.error && err.detail.error.message) msg = err.detail.error.message;
        } else if (err.message) {
          msg = err.message;
        }
        showError(msg);
      })
      .finally(function () {
        showLoading(false);
      });
  }

  function renderDetail() {
    if (!comicData) return;

    if (topTitle) topTitle.textContent = comicData.title || "Untitled";
    if (titleDisplay) titleDisplay.textContent = comicData.title || "Untitled";

    renderCover();
    renderSource();
    renderStatus();
    renderDescription();
    renderStats();
    renderProgress();
    renderReadingProgress();
    renderChapters();
    updateActionButtons();
  }

  function renderCover() {
    if (comicData.cover_url) {
      if (coverImg) {
        coverImg.src = comicData.cover_url;
        coverImg.hidden = false;
      }
      if (coverPlaceholder) coverPlaceholder.hidden = true;
    } else {
      if (coverImg) coverImg.hidden = true;
      if (coverPlaceholder) {
        var initial = (comicData.title || "?").charAt(0).toUpperCase();
        coverPlaceholder.textContent = initial;
        coverPlaceholder.hidden = false;
      }
    }
  }

  function renderSource() {
    if (sourceEl) {
      sourceEl.textContent = comicData.source || "";
      sourceEl.hidden = !comicData.source;
    }
  }

  function renderStatus() {
    if (!statusBadge) return;
    var s = comicData.status || "pending";
    statusBadge.className = "status-badge status-" + s;
    statusBadge.textContent = s.replace(/_/g, " ");
  }

  function renderDescription() {
    if (!descriptionEl) return;
    var desc = comicData.description || "";
    if (desc) {
      descriptionEl.textContent = desc;
      descriptionEl.hidden = false;
    } else {
      descriptionEl.hidden = true;
    }
  }

  function renderStats() {
    var total = comicData.chapter_count || 0;
    var downloaded = comicData.downloaded_count || 0;

    if (chapterCountEl) {
      chapterCountEl.textContent = total + " chapter" + (total !== 1 ? "s" : "");
    }
    if (downloadedCountEl) {
      downloadedCountEl.textContent = downloaded + " downloaded";
    }

    // Phase 17.10: Show chapter language
    var languageEl = document.getElementById("detail-language");
    if (languageEl) {
      var languages = [];
      var chapters = comicData.chapters || [];
      for (var i = 0; i < chapters.length; i++) {
        var lang = chapters[i].language;
        if (lang && languages.indexOf(lang) === -1) {
          languages.push(lang);
        }
      }
      if (languages.length === 1) {
        languageEl.textContent = "Language: " + formatLanguageName(languages[0]);
      } else if (languages.length > 1) {
        languageEl.textContent = "Multiple languages";
      } else {
        languageEl.textContent = "";
      }
    }
  }

  function formatLanguageName(code) {
    var names = {
      "en": "English",
      "pt-br": "Portuguese (Brazil)",
      "es-la": "Spanish (Latin America)",
      "es": "Spanish",
      "fr": "French",
      "de": "German",
      "it": "Italian",
      "ru": "Russian",
      "ja": "Japanese",
      "ko": "Korean",
      "zh": "Chinese",
      "id": "Indonesian"
    };
    return names[code] || code;
  }

  function renderProgress() {
    if (!progressEl || !progressFill || !progressText) return;

    var total = comicData.chapter_count || 0;
    var downloaded = comicData.downloaded_count || 0;

    if (total > 0) {
      var pct = Math.round((downloaded / total) * 100);
      progressFill.style.width = pct + "%";
      progressText.textContent = pct + "% (" + downloaded + "/" + total + ")";
      progressEl.hidden = false;
    } else {
      progressEl.hidden = true;
    }
  }

  function renderReadingProgress() {
    if (!readingProgressEl || !readingText) return;

    var progress = comicData.reading_progress || comicData.progress;
    if (progress && progress.chapter_id) {
      var chapters = comicData.chapters || [];
      var chapterLabel = "";
      for (var i = 0; i < chapters.length; i++) {
        if (chapters[i].chapter_id === progress.chapter_id) {
          var cn = chapters[i].chapter_number || chapters[i].chapter_id;
          chapterLabel = "Ch. " + cn;
          break;
        }
      }

      var pageInfo = "";
      if (progress.page && progress.total_pages) {
        pageInfo = " — Page " + progress.page + " of " + progress.total_pages;
      }

      readingText.textContent = "Continue reading: " + chapterLabel + pageInfo;
      readingProgressEl.hidden = false;
    } else {
      readingProgressEl.hidden = true;
    }
  }

  /* ============================================================
     CHAPTER FILTERING / SORTING / PAGINATION
     ============================================================ */

  function onSearch() {
    currentPage = 0;
    applyFilters();
    renderChapters();
  }

  function onFilter() {
    currentPage = 0;
    applyFilters();
    renderChapters();
  }

  function onToggleSort() {
    sortAsc = !sortAsc;
    if (chapterSortBtn) {
      chapterSortBtn.textContent = sortAsc ? "\u2191" : "\u2193";
      chapterSortBtn.title = sortAsc ? "Sort ascending" : "Sort descending";
    }
    applyFilters();
    renderChapters();
  }

  function onShowMore() {
    currentPage++;
    renderChapters();
  }

  function applyFilters() {
    var query = (chapterSearchInput ? chapterSearchInput.value : "").toLowerCase().trim();
    var filter = chapterFilterSelect ? chapterFilterSelect.value : "all";

    filteredChapters = allChapters.filter(function (ch) {
      var matchQuery = true;
      if (query) {
        var num = String(ch.chapter_number || "").toLowerCase();
        var title = String(ch.title || "").toLowerCase();
        var id = String(ch.chapter_id || "").toLowerCase();
        matchQuery = num.indexOf(query) >= 0 || title.indexOf(query) >= 0 || id.indexOf(query) >= 0;
      }

      var matchFilter = true;
      if (filter !== "all") {
        matchFilter = (ch.status || "not_downloaded") === filter;
      }

      return matchQuery && matchFilter;
    });

    // Sort
    filteredChapters.sort(function (a, b) {
      var aNum = parseFloat(a.chapter_number) || 0;
      var bNum = parseFloat(b.chapter_number) || 0;
      if (aNum !== bNum) {
        return sortAsc ? aNum - bNum : bNum - aNum;
      }
      return sortAsc
        ? (a.chapter_id || "").localeCompare(b.chapter_id || "")
        : (b.chapter_id || "").localeCompare(a.chapter_id || "");
    });

    if (chaptersFilterCount) {
      chaptersFilterCount.textContent = filteredChapters.length + " / " + allChapters.length;
    }
  }

  function renderChapters() {
    if (!chapterListEl || !noChaptersEl) return;

    if (filteredChapters.length === 0) {
      chapterListEl.innerHTML = "";
      noChaptersEl.hidden = false;
      if (chapterShowMoreBtn) chapterShowMoreBtn.hidden = true;
      return;
    }

    noChaptersEl.hidden = true;

    var endIndex = (currentPage + 1) * pageSize;
    var hasMore = filteredChapters.length > endIndex;
    var visible = filteredChapters.slice(0, endIndex);

    chapterListEl.innerHTML = visible
      .map(function (ch) {
        return renderChapterRow(ch);
      })
      .join("");

    if (chapterShowMoreBtn) {
      chapterShowMoreBtn.hidden = !hasMore;
      chapterShowMoreBtn.textContent = "Show more (" + (filteredChapters.length - endIndex) + " remaining)";
    }
  }

  function renderChapterRow(ch) {
    var chapterNum = ch.chapter_number || ch.chapter_id;
    var chapterTitle = ch.title || "";

    var statusIcon = getChapterStatusIcon(ch.status);
    var statusClass = "chapter-status chapter-status-" + (ch.status || "not_downloaded");

    // Determine if this is the current chapter in progress
    var progress = comicData.reading_progress || comicData.progress;
    var isCurrent = progress && progress.chapter_id === ch.chapter_id;
    var rowClass = "chapter-row";
    if (isCurrent) rowClass += " chapter-current";
    if (ch.completed) rowClass += " chapter-read";

    var actionHtml = "";
    if (ch.status === "not_downloaded") {
      actionHtml =
        '<button class="chapter-dl-btn" title="Download chapter" data-chapter-dl="' +
        escapeAttr(ch.chapter_id) +
        '">\u2B07</button>';
    } else if (ch.status === "error") {
      actionHtml =
        '<button class="chapter-retry-btn" title="Retry download" data-chapter-retry="' +
        escapeAttr(ch.chapter_id) +
        '">\u21BB</button>';
    } else if (ch.status === "downloaded") {
      actionHtml =
        '<button class="chapter-read-btn" title="Read chapter" data-chapter-read="' +
        escapeAttr(ch.chapter_id) +
        '">\u25B6</button>';
    }

    var progressInfo = "";
    if (ch.status === "downloading" && ch.pages > 0) {
      var dPct =
        ch.pages > 0
          ? Math.round(((ch.downloaded_pages || 0) / ch.pages) * 100)
          : 0;
      progressInfo =
        '<span class="chapter-dl-progress">' + dPct + "%</span>";
    } else if (ch.status === "partial" && ch.pages > 0) {
      var partialPct =
        ch.pages > 0
          ? Math.round(((ch.downloaded_pages || 0) / ch.pages) * 100)
          : 0;
      progressInfo =
        '<span class="chapter-dl-progress chapter-dl-partial">' + partialPct + "%</span>";
    }

    var currentBadge = "";
    if (isCurrent) {
      currentBadge = '<span class="chapter-current-badge">Current</span>';
    }

    var completedBadge = "";
    if (ch.completed && !isCurrent) {
      completedBadge = '<span class="chapter-completed-badge">Read</span>';
    }

    return (
      '<div class="' + rowClass + '" data-chapter-id="' +
      escapeAttr(ch.chapter_id) +
      '">' +
      '<span class="' +
      statusClass +
      '" title="' +
      escapeAttr(ch.status || "not_downloaded") +
      '">' +
      statusIcon +
      "</span>" +
      '<span class="chapter-num">' +
      escapeHtml(chapterNum) +
      "</span>" +
      '<span class="chapter-title-text">' +
      escapeHtml(chapterTitle) +
      "</span>" +
      '<span class="chapter-lang">' +
      escapeHtml(ch.language || "en") +
      "</span>" +
      currentBadge +
      completedBadge +
      progressInfo +
      '<span class="chapter-actions">' +
      actionHtml +
      "</span>" +
      "</div>"
    );
  }

  function getChapterStatusIcon(status) {
    switch (status) {
      case "downloaded":
        return "\u2713";
      case "downloading":
        return "\u2B6E";
      case "queued":
        return "\u25CB";
      case "error":
        return "\u2717";
      case "partial":
        return "\u25D0";
      case "cancelled":
        return "\u2298";
      default:
        return "\u25CB";
    }
  }

  /* ============================================================
     EVENT HANDLERS — Chapter List Click
     ============================================================ */

  if (chapterListEl) {
    chapterListEl.addEventListener("click", function (e) {
      var dlBtn = e.target.closest("[data-chapter-dl]");
      if (dlBtn) {
        e.preventDefault();
        e.stopPropagation();
        downloadChapter(dlBtn.dataset.chapterDl);
        return;
      }

      var retryBtn = e.target.closest("[data-chapter-retry]");
      if (retryBtn) {
        e.preventDefault();
        e.stopPropagation();
        retryChapter(retryBtn.dataset.chapterRetry);
        return;
      }

      // BUG FIX: use data-chapter-read attribute, not chapterId
      var readBtn = e.target.closest("[data-chapter-read]");
      if (readBtn) {
        e.preventDefault();
        e.stopPropagation();
        var chId = readBtn.dataset.chapterRead;  // FIXED: was readBtn.dataset.chapterId
        window.location.href = "/reader?comic=" + encodeURIComponent(comicId) + "&chapter_id=" + encodeURIComponent(chId);
        return;
      }

      var row = e.target.closest(".chapter-row");
      if (row) {
        var chId = row.dataset.chapterId;
        if (chId) {
          window.location.href = "/reader?comic=" + encodeURIComponent(comicId) + "&chapter_id=" + encodeURIComponent(chId);
        }
      }
    });
  }

  function downloadChapter(chapterId) {
    API.post(
      "/library/" + encodeURIComponent(comicId) + "/chapters/" + encodeURIComponent(chapterId) + "/download",
      {}
    )
      .then(function () {
        showToast("Chapter download started.", "success");
        startPolling();
      })
      .catch(function (err) {
        showToast("Failed to start download: " + (err.detail || err.message), "error");
      });
  }

  function retryChapter(chapterId) {
    API.post(
      "/downloads/" + encodeURIComponent(comicId) + "/chapters/" + encodeURIComponent(chapterId) + "/retry",
      {}
    )
      .then(function () {
        showToast("Chapter retry started.", "success");
        startPolling();
      })
      .catch(function (err) {
        showToast("Failed to retry: " + (err.detail || err.message), "error");
      });
  }

  function updateActionButtons() {
    if (!comicData) return;

    var chapters = comicData.chapters || [];
    var hasMissing = false;
    var hasFailed = false;

    for (var i = 0; i < chapters.length; i++) {
      if (chapters[i].status === "not_downloaded") hasMissing = true;
      if (chapters[i].status === "error") hasFailed = true;
    }

    if (btnDownloadMissing) btnDownloadMissing.hidden = !hasMissing;
    if (btnRetryFailed) btnRetryFailed.hidden = !hasFailed;

    var isDownloaded = comicData.downloaded_count > 0;
    if (btnRead) {
      btnRead.hidden = !isDownloaded;
      // Phase 17.9: Show "Continue Reading" if there's saved progress
      var progress = comicData.reading_progress || comicData.progress;
      if (progress && progress.chapter_id) {
        btnRead.innerHTML = "<span>&#x25B6;</span> Continue Reading";
      } else {
        btnRead.innerHTML = "<span>&#x25B6;</span> Read";
      }
    }
  }

  function onRead() {
    if (comicId) {
      var progress = comicData && (comicData.reading_progress || comicData.progress);
      var chId = progress && progress.chapter_id;
      var url = "/reader?comic=" + encodeURIComponent(comicId);
      if (chId) {
        url += "&chapter_id=" + encodeURIComponent(chId);
      }
      window.location.href = url;
    }
  }

  function onDownloadMissing() {
    API.post("/library/" + encodeURIComponent(comicId) + "/download", {})
      .then(function () {
        showToast("Download started.", "success");
        startPolling();
      })
      .catch(function (err) {
        showToast("Failed to start download: " + (err.detail || err.message), "error");
      });
  }

  function onRetryFailed() {
    if (!comicData) return;
    var chapters = comicData.chapters || [];
    var failedChapters = [];
    for (var i = 0; i < chapters.length; i++) {
      if (chapters[i].status === "error") {
        failedChapters.push(chapters[i]);
      }
    }

    if (failedChapters.length === 0) {
      showToast("No failed chapters to retry.", "info");
      return;
    }

    var count = 0;
    var successCount = 0;
    var total = failedChapters.length;

    failedChapters.forEach(function (ch) {
      API.post(
        "/downloads/" + encodeURIComponent(comicId) + "/chapters/" + encodeURIComponent(ch.chapter_id) + "/retry",
        {}
      )
        .then(function () {
          count++;
          successCount++;
          if (count === total) {
            if (successCount === total) {
              showToast("Retrying " + total + " failed chapter(s).", "success");
            } else {
              showToast("Retrying " + successCount + "/" + total + " chapters. Some failed.", "warning");
            }
            startPolling();
          }
        })
        .catch(function (err) {
          count++;
          if (count === total) {
            if (successCount === total) {
              showToast("Retrying " + total + " failed chapter(s).", "success");
            } else if (successCount > 0) {
              showToast("Retrying " + successCount + "/" + total + " chapters. Some failed.", "warning");
            } else {
              showToast("All retries failed. Please try again later.", "error");
            }
            startPolling();
          }
        });
    });
  }

  function onRefresh() {
    showToast("Refreshing metadata...", "info");
    API.post("/library/" + encodeURIComponent(comicId) + "/refresh", {})
      .then(function (data) {
        showToast("Metadata refreshed.", "success");
        comicData = data;
        allChapters = data.chapters || [];
        applyFilters();
        renderDetail();
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

  function onDelete() {
    var title = (comicData && comicData.title) || comicId;
    if (!confirm('Delete "' + title + '" and all its downloaded chapters? This cannot be undone.')) {
      return;
    }

    API.del("/library/" + encodeURIComponent(comicId))
      .then(function () {
        window.location.href = "/";
      })
      .catch(function (err) {
        showToast("Failed to delete: " + (err.detail || err.message), "error");
      });
  }

  function startPolling() {
    if (_pollTimer) return;
    _pollTimer = setInterval(function () {
      pollStatus();
    }, 3000);
  }

  function stopPolling() {
    if (_pollTimer) {
      clearInterval(_pollTimer);
      _pollTimer = null;
    }
  }

  function pollStatus() {
    API.get("/downloads/" + encodeURIComponent(comicId) + "/status")
      .then(function (status) {
        updateChapterStatuses(status);
        applyFilters();
        renderChapters();

        if (
          status.status === "complete" ||
          status.status === "error" ||
          status.status === "partial"
        ) {
          stopPolling();
          loadDetail();
        }
      })
      .catch(function () {
        stopPolling();
      });
  }

  function updateChapterStatuses(status) {
    if (!comicData) return;
    var chapters = comicData.chapters || [];

    for (var i = 0; i < chapters.length; i++) {
      var ch = chapters[i];
      if (ch.chapter_id === status.current_chapter_id) {
        ch.status = status.state || status.status || ch.status;
      }
    }
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

  function showLoading(show) {
    if (loadingEl) loadingEl.hidden = !show;
  }

  function showError(msg) {
    if (errorEl) {
      errorEl.hidden = false;
    }
    if (errorMsg) {
      errorMsg.textContent = msg;
    }
  }

  function hideError() {
    if (errorEl) {
      errorEl.hidden = true;
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
