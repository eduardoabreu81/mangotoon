// MangoToon History Page

(function () {
  "use strict";

  var historyItems = [];

  var loadingEl = document.getElementById("history-loading");
  var emptyEl = document.getElementById("history-empty");
  var errorEl = document.getElementById("history-error");
  var errorMsg = document.getElementById("history-error-msg");
  var gridEl = document.getElementById("history-grid");

  document.addEventListener("DOMContentLoaded", function () {
    loadHistory();
  });

  function loadHistory() {
    showLoading(true);
    hideEmpty();
    hideError();

    API.get("/history")
      .then(function (data) {
        historyItems = data.items || [];
        if (historyItems.length === 0) {
          showEmpty();
          return;
        }
        renderGrid();
      })
      .catch(function (err) {
        showError(
          err.detail || err.message || "Could not load reading history."
        );
      })
      .finally(function () {
        showLoading(false);
      });
  }

  function renderGrid() {
    if (!gridEl) return;

    hideEmpty();
    hideError();

    gridEl.innerHTML = historyItems
      .map(function (item) {
        return renderHistoryCard(item);
      })
      .join("");
  }

  function renderHistoryCard(item) {
    var coverHtml;
    if (item.cover_url) {
      coverHtml =
        '<img class="comic-cover" src="' +
        escapeAttr(item.cover_url) +
        '" alt="' +
        escapeHtml(item.title) +
        '" loading="lazy">';
    } else if (item.comic_id) {
      coverHtml =
        '<img class="comic-cover" src="/api/comics/' +
        escapeAttr(item.comic_id) +
        '/cover" alt="' +
        escapeHtml(item.title) +
        '" loading="lazy" onerror="this.style.display=\'none\';this.parentElement.querySelector(\'.comic-cover-placeholder\').style.display=\'flex\'">' +
        '<div class="comic-cover-placeholder" aria-hidden="true" style="display:none">' +
        escapeHtml((item.title || "?").charAt(0).toUpperCase()) +
        "</div>";
    } else {
      coverHtml =
        '<div class="comic-cover-placeholder" aria-hidden="true">' +
        escapeHtml((item.title || "?").charAt(0).toUpperCase()) +
        "</div>";
    }

    var chapterLabel = "";
    if (item.chapter_number) {
      chapterLabel = "Ch. " + escapeHtml(String(item.chapter_number));
    }
    if (item.page_number) {
      chapterLabel += chapterLabel
        ? " — Pg. " + item.page_number
        : "Pg. " + item.page_number;
    }

    var timeAgo = formatTimeAgo(item.last_read_at);

    return (
      '<article class="comic-card" data-comic-id="' +
      escapeAttr(item.comic_id) +
      '" data-continue-chapter="' +
      escapeAttr(item.chapter_id) +
      '" data-continue-page="' +
      escapeAttr(String(item.page_number || 1)) +
      '">' +
      coverHtml +
      '<div class="comic-info">' +
      '<h3 class="comic-title" title="' +
      escapeAttr(item.title) +
      '">' +
      escapeHtml(item.title) +
      "</h3>" +
      '<div class="comic-meta">' +
      '<span class="comic-source">' +
      escapeHtml(chapterLabel) +
      "</span>" +
      '<span class="comic-source">' +
      escapeHtml(timeAgo) +
      "</span>" +
      "</div>" +
      '<button class="card-continue" title="Continue reading" aria-label="Continue reading ' +
      escapeAttr(item.title) +
      '" data-continue="' +
      escapeAttr(item.comic_id) +
      '">Continue</button>' +
      "</div>" +
      "</article>"
    );
  }

  gridEl &&
    gridEl.addEventListener("click", function (e) {
      var continueBtn = e.target.closest("[data-continue]");
      if (continueBtn) {
        e.preventDefault();
        e.stopPropagation();
        var card = continueBtn.closest(".comic-card");
        var comicId = continueBtn.dataset.continue;
        var chapterId = card ? card.dataset.continueChapter : "";
        var page = card ? card.dataset.continuePage : "1";
        continueReading(comicId, chapterId, page);
        return;
      }

      var card = e.target.closest(".comic-card");
      if (card) {
        var comicId = card.dataset.comicId;
        var chapterId = card.dataset.continueChapter;
        var page = card.dataset.continuePage || "1";
        if (comicId) {
          continueReading(comicId, chapterId, page);
        }
      }
    });

  function continueReading(comicId, chapterId, page) {
    var url = "/reader?comic=" + encodeURIComponent(comicId);
    if (chapterId) {
      url += "&chapter_id=" + encodeURIComponent(chapterId);
    }
    window.location.href = url;
  }

  function formatTimeAgo(isoString) {
    if (!isoString) return "";

    try {
      var now = new Date();
      var then = new Date(isoString);
      if (isNaN(then.getTime())) return "";

      var diffMs = now - then;
      if (diffMs < 0) return "Just now";

      var seconds = Math.floor(diffMs / 1000);
      if (seconds < 60) return "Just now";

      var minutes = Math.floor(seconds / 60);
      if (minutes < 60) return minutes + " min ago";

      var hours = Math.floor(minutes / 60);
      if (hours < 24) return hours + "h ago";

      var days = Math.floor(hours / 24);
      if (days < 7) return days + "d ago";

      var weeks = Math.floor(days / 7);
      if (weeks < 4) return weeks + "w ago";

      var months = Math.floor(days / 30);
      return months + "mo ago";
    } catch (e) {
      return "";
    }
  }

  function showLoading(show) {
    if (loadingEl) loadingEl.hidden = !show;
  }

  function showEmpty() {
    if (emptyEl) emptyEl.hidden = false;
  }

  function hideEmpty() {
    if (emptyEl) emptyEl.hidden = true;
  }

  function showError(msg) {
    if (errorEl) {
      if (errorMsg) errorMsg.textContent = msg;
      errorEl.hidden = false;
    }
  }

  function hideError() {
    if (errorEl) errorEl.hidden = true;
  }

  function escapeHtml(str) {
    var div = document.createElement("div");
    div.textContent = str || "";
    return div.innerHTML;
  }

  function escapeAttr(str) {
    return String(str || "")
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/'/g, "&#39;");
  }
})();
