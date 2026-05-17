// MangoToon Reader

(function () {
  "use strict";

  var comicId = null;
  var readerData = null;
  var chapters = [];
  var currentChapterIdx = 0;
  var currentPage = 1;
  var totalPages = 0;
  var uiVisible = true;
  var saveTimer = null;
  var autoHideTimer = null;
  var zoomLevel = 100;
  var fitMode = 0; // 0=fit-screen, 1=fit-width, 2=fit-height, 3=original

  document.addEventListener("DOMContentLoaded", function () {
    init();
  });

  function init() {
    var params = new URLSearchParams(window.location.search);
    comicId = params.get("comic");

    if (!comicId) {
      showError("No manga selected.");
      return;
    }

    loadReaderData();
    setupControls();
    setupAutoHide();
  }

  function loadReaderData() {
    showLoading(true);
    hideError();

    API.get("/reader/" + encodeURIComponent(comicId) + "/data")
      .then(function (data) {
        readerData = data;
        chapters = data.chapters || [];

        if (chapters.length === 0) {
          showError("No downloaded chapters available.");
          return;
        }

        var progress = data.progress;
        if (progress && progress.chapter_id) {
          var foundIdx = -1;
          for (var i = 0; i < chapters.length; i++) {
            if (chapters[i].chapter_id === progress.chapter_id) {
              foundIdx = i;
              break;
            }
          }
          currentChapterIdx = foundIdx >= 0 ? foundIdx : 0;
          currentPage = progress.page || 1;
        }

        document.title = "MangoToon — " + (data.title || "Reader");
        renderChapterSelect();
        showChapter(currentChapterIdx, currentPage);
      })
      .catch(function () {
        showError("Failed to load reader data.");
      })
      .finally(function () {
        showLoading(false);
      });
  }

  function setupAutoHide() {
    var main = document.getElementById("reader-main");
    if (!main) return;

    main.addEventListener("mousemove", resetAutoHide);
    main.addEventListener("touchstart", resetAutoHide);
    resetAutoHide();
  }

  function resetAutoHide() {
    var top = document.getElementById("reader-top");
    var bottom = document.getElementById("reader-bottom");

    if (top) top.classList.remove("reader-hidden");
    if (bottom) bottom.classList.remove("reader-hidden");
    uiVisible = true;

    clearTimeout(autoHideTimer);
    autoHideTimer = setTimeout(function () {
      if (top) top.classList.add("reader-hidden");
      if (bottom) bottom.classList.add("reader-hidden");
      uiVisible = false;
    }, 3000);
  }

  function setupControls() {
    document.getElementById("zone-prev").addEventListener("click", function () {
      goToPage(currentPage - 1);
      resetAutoHide();
    });
    document.getElementById("zone-next").addEventListener("click", function () {
      goToPage(currentPage + 1);
      resetAutoHide();
    });
    document.getElementById("zone-center").addEventListener("click", function () {
      toggleUi();
    });

    document.getElementById("btn-prev-chapter").addEventListener("click", goToPrevChapter);
    document.getElementById("btn-next-chapter").addEventListener("click", goToNextChapter);

    document.getElementById("btn-zoom-out").addEventListener("click", zoomOut);
    document.getElementById("btn-zoom-in").addEventListener("click", zoomIn);
    document.getElementById("btn-zoom-reset").addEventListener("click", zoomReset);
    document.getElementById("btn-fit").addEventListener("click", cycleFitMode);
    document.getElementById("btn-fullscreen").addEventListener("click", toggleFullscreen);

    document.getElementById("btn-next-chapter-overlay").addEventListener("click", function () {
      hideChapterComplete();
      goToNextChapter();
    });

    document.addEventListener("keydown", function (e) {
      if (!chapters.length) return;
      switch (e.key) {
        case "ArrowRight":
        case "ArrowDown":
          e.preventDefault();
          goToPage(currentPage + 1);
          resetAutoHide();
          break;
        case "ArrowLeft":
        case "ArrowUp":
          e.preventDefault();
          goToPage(currentPage - 1);
          resetAutoHide();
          break;
        case "Home":
          e.preventDefault();
          currentPage = 1;
          loadPage();
          break;
        case "End":
          e.preventDefault();
          currentPage = totalPages || 1;
          loadPage();
          break;
        case "Escape":
          window.location.href = "/";
          break;
        case "f":
        case "F":
          toggleFullscreen();
          break;
        case "=":
        case "+":
          zoomIn();
          break;
        case "-":
          zoomOut();
          break;
        case "0":
          zoomReset();
          break;
        case "g":
        case "G":
          cycleFitMode();
          break;
      }
    });
  }

  function showChapter(idx, page) {
    currentChapterIdx = idx;
    var chapter = chapters[idx];
    if (!chapter) return;

    totalPages = chapter.pages || 0;
    currentPage = Math.max(1, Math.min(page || 1, totalPages || 1));

    document.getElementById("reader-title").textContent = readerData.title || "";
    var label = "Ch. " + (chapter.chapter_number || (idx + 1));
    if (chapter.title) label += " — " + chapter.title;
    document.getElementById("reader-chapter-label").textContent = label;

    var sel = document.getElementById("chapter-select");
    if (sel) sel.value = chapter.chapter_id;

    hideChapterComplete();
    loadPage();
  }

  function loadPage() {
    var chapter = chapters[currentChapterIdx];
    if (!chapter) return;

    var img = document.getElementById("reader-img");
    var loading = document.getElementById("reader-loading");

    img.hidden = true;
    loading.hidden = false;

    updatePageIndicator();
    updateProgressBar();

    var src =
      "/api/reader/" +
      encodeURIComponent(comicId) +
      "/" +
      encodeURIComponent(chapter.chapter_id) +
      "/" +
      currentPage;

    var newImg = new Image();
    newImg.onload = function () {
      img.src = src;
      img.hidden = false;
      loading.hidden = true;
      applyZoom();
      applyFitMode();
      scheduleSaveProgress();
      checkChapterComplete();
    };
    newImg.onerror = function () {
      loading.hidden = true;
      img.hidden = true;
      showError("Page " + currentPage + " could not be loaded.");
    };
    newImg.src = src;
  }

  function goToPage(page) {
    if (page < 1) {
      goToPrevChapter();
      return;
    }
    if (page > totalPages) {
      goToNextChapter();
      return;
    }
    currentPage = page;
    loadPage();
  }

  function goToPrevChapter() {
    if (currentChapterIdx > 0) {
      var prevChapter = chapters[currentChapterIdx - 1];
      showChapter(currentChapterIdx - 1, prevChapter.pages || 0);
    }
  }

  function goToNextChapter() {
    if (currentChapterIdx < chapters.length - 1) {
      showChapter(currentChapterIdx + 1, 1);
    }
  }

  function checkChapterComplete() {
    if (currentPage >= totalPages) {
      if (currentChapterIdx < chapters.length - 1) {
        showChapterComplete();
      } else {
        scheduleSaveProgress();
      }
    }
  }

  function showChapterComplete() {
    var overlay = document.getElementById("chapter-complete");
    if (!overlay) return;
    overlay.hidden = false;

    clearTimeout(autoHideTimer);
    setTimeout(function () {
      if (!overlay.hidden) {
        hideChapterComplete();
        goToNextChapter();
      }
    }, 4000);
  }

  function hideChapterComplete() {
    var overlay = document.getElementById("chapter-complete");
    if (overlay) overlay.hidden = true;
  }

  function scheduleSaveProgress() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(saveProgress, 800);
  }

  function saveProgress() {
    var chapter = chapters[currentChapterIdx];
    if (!chapter) return;
    var completed = currentPage >= totalPages;
    API.post("/reader/" + encodeURIComponent(comicId) + "/progress", {
      chapter_id: chapter.chapter_id,
      page: currentPage,
      total_pages: totalPages,
      completed: completed,
    }).catch(function (err) {
      console.warn("Progress save failed:", err);
    });
  }

  function renderChapterSelect() {
    var sel = document.getElementById("chapter-select");
    if (!sel) return;

    sel.innerHTML = chapters
      .map(function (ch, i) {
        var label = "Ch. " + (ch.chapter_number || i + 1);
        if (ch.title) label += " — " + ch.title;
        return (
          '<option value="' +
          escapeAttr(ch.chapter_id) +
          '">' +
          escapeHtml(label) +
          "</option>"
        );
      })
      .join("");

    sel.addEventListener("change", function () {
      var foundIdx = -1;
      for (var i = 0; i < chapters.length; i++) {
        if (chapters[i].chapter_id === sel.value) {
          foundIdx = i;
          break;
        }
      }
      if (foundIdx >= 0) showChapter(foundIdx, 1);
    });
  }

  function toggleUi() {
    uiVisible = !uiVisible;
    document.getElementById("reader-top").classList.toggle("reader-hidden", !uiVisible);
    document.getElementById("reader-bottom").classList.toggle("reader-hidden", !uiVisible);
    if (uiVisible) {
      resetAutoHide();
    } else {
      clearTimeout(autoHideTimer);
    }
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(function () {});
    } else {
      document.exitFullscreen().catch(function () {});
    }
  }

  function zoomIn() {
    zoomLevel = Math.min(300, zoomLevel + 25);
    applyZoom();
    updateZoomLabel();
  }

  function zoomOut() {
    zoomLevel = Math.max(25, zoomLevel - 25);
    applyZoom();
    updateZoomLabel();
  }

  function zoomReset() {
    zoomLevel = 100;
    applyZoom();
    updateZoomLabel();
  }

  function applyZoom() {
    var img = document.getElementById("reader-img");
    if (!img) return;
    img.style.transform = "scale(" + (zoomLevel / 100) + ")";
  }

  function updateZoomLabel() {
    var btn = document.getElementById("btn-zoom-reset");
    if (btn) btn.textContent = zoomLevel + "%";
  }

  function cycleFitMode() {
    fitMode = (fitMode + 1) % 4;
    applyFitMode();
  }

  function applyFitMode() {
    var img = document.getElementById("reader-img");
    if (!img) return;

    img.classList.remove("fit-width", "fit-height", "fit-original");

    switch (fitMode) {
      case 0:
        break;
      case 1:
        img.classList.add("fit-width");
        break;
      case 2:
        img.classList.add("fit-height");
        break;
      case 3:
        img.classList.add("fit-original");
        break;
    }

    var btn = document.getElementById("btn-fit");
    if (btn) {
      var labels = ["⊠", "↔", "↕", "1:1"];
      btn.textContent = labels[fitMode] || "⊠";
    }
  }

  function updatePageIndicator() {
    document.getElementById("reader-page-indicator").textContent =
      currentPage + " / " + totalPages;
  }

  function updateProgressBar() {
    var pct = totalPages > 0 ? (currentPage / totalPages) * 100 : 0;
    document.getElementById("reader-progress-fill").style.width = pct + "%";
  }

  function showLoading(show) {
    document.getElementById("reader-loading").hidden = !show;
  }

  function showError(msg) {
    document.getElementById("reader-loading").hidden = true;
    document.getElementById("reader-img").hidden = true;
    document.getElementById("reader-error-msg").textContent = msg;
    document.getElementById("reader-error").hidden = false;
  }

  function hideError() {
    document.getElementById("reader-error").hidden = true;
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
