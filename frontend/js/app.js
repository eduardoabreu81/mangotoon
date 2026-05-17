// MangoToon Frontend - Application Shell

(function () {
  "use strict";

  var library = [];
  var filtered = [];

  var statusEl = document.getElementById("api-status");
  var gridEl = document.getElementById("library-grid");
  var emptyEl = document.getElementById("empty-library");
  var loadingEl = document.getElementById("library-loading");
  var searchEl = document.getElementById("library-search");
  var addBtn = document.getElementById("btn-add");

  var sortEl = document.getElementById("library-sort");
  var addModal = document.getElementById("add-modal");
  var addForm = document.getElementById("add-form");
  var addCancel = document.getElementById("add-cancel");
  var addUrl = document.getElementById("add-url");
  var addSourceDetected = document.getElementById("add-source-detected");

  document.addEventListener("DOMContentLoaded", function () {
    init();
  });

  function init() {
    searchEl && searchEl.addEventListener("input", onSearch);
    sortEl && sortEl.addEventListener("change", onSort);
    addBtn && addBtn.addEventListener("click", openAddModal);
    addCancel && addCancel.addEventListener("click", closeAddModal);
    addForm && addForm.addEventListener("submit", onAddSubmit);
    addUrl && addUrl.addEventListener("input", detectSource);
    updateApiStatus();
    loadLibrary();
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
        filtered = library.slice();
        renderGrid();
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

  function renderGrid() {
    if (!gridEl) return;

    if (filtered.length === 0) {
      gridEl.innerHTML = "";
      showEmpty();
      return;
    }

    hideEmpty();

    gridEl.innerHTML = filtered
      .map(function (comic) {
        return renderCard(comic);
      })
      .join("");
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

  function onSearch() {
    var query = (searchEl.value || "").toLowerCase().trim();
    if (!query) {
      filtered = library.slice();
    } else {
      filtered = library.filter(function (comic) {
        return (comic.title || "").toLowerCase().indexOf(query) !== -1;
      });
    }
    renderGrid();
  }

  function onSort() {
    var sortBy = sortEl.value;
    var sorted = filtered.slice();
    switch (sortBy) {
      case "title":
        sorted.sort(function (a, b) {
          return (a.title || "").localeCompare(b.title || "");
        });
        break;
      case "read":
        sorted.sort(function (a, b) {
          var aTime = a.progress ? new Date(a.progress.updated_at).getTime() : 0;
          var bTime = b.progress ? new Date(b.progress.updated_at).getTime() : 0;
          return bTime - aTime;
        });
        break;
      case "progress":
        sorted.sort(function (a, b) {
          var aPct = a.chapter_count > 0 ? (a.downloaded_count / a.chapter_count) : 0;
          var bPct = b.chapter_count > 0 ? (b.downloaded_count / b.chapter_count) : 0;
          return bPct - aPct;
        });
        break;
      case "added":
      default:
        sorted.sort(function (a, b) {
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        });
        break;
    }
    filtered = sorted;
    renderGrid();
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

  function showAddError(msg) {
    var errEl = document.getElementById("add-error");
    if (!errEl) return;
    errEl.textContent = msg;
    errEl.hidden = !msg;
  }

  gridEl &&
    gridEl.addEventListener("click", function (e) {
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
          console.log("Open comic:", comicId);
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
        onSearch();
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
