// MangoToon Reader
// Phase 17.8: Reader and Comic UX Overhaul

(function () {
  "use strict";

  var comicId = null;
  var readerData = null;
  var chapters = [];
  var chaptersAll = [];
  var currentChapterIdx = 0;
  var currentPage = 1;
  var totalPages = 0;
  var uiVisible = true;
  var saveTimer = null;
  var autoHideTimer = null;
  var zoomLevel = 100;
  var fitMode = 0; // 0=fit-screen, 1=fit-width, 2=fit-height, 3=original
  var drawerOpen = false;
  var drawerLoading = false;

  // Phase 17.8: Preload cache
  var preloadCache = {}; // src -> Image object
  var preloadQueue = [];
  var maxPreloadAhead = 3;
  var maxPreloadBehind = 1;

  // Phase 17.8: Reader mode (paged | vertical)
  var readerMode = "paged"; // default
  var modeToggleInitialized = false;

  // Progress save backoff
  var saveBackoffUntil = 0;
  var saveFailCount = 0;

  // Phase 17.8: Page load token to prevent race conditions
  var pageLoadToken = 0;
  var preloadTimer = null;

  document.addEventListener("DOMContentLoaded", function () {
    init();
  });

  function init() {
    var params = new URLSearchParams(window.location.search);
    comicId = params.get("comic");
    var urlChapterId = params.get("chapter_id");

    if (!comicId) {
      showError("No manga selected.");
      return;
    }

    // Phase 17.8: Load reader mode from localStorage
    var savedMode = localStorage.getItem("mangotoon_reader_mode");
    if (savedMode === "paged" || savedMode === "vertical") {
      readerMode = savedMode;
    }

    loadReaderData(urlChapterId);
    loadChapterList();
    setupControls();
    setupAutoHide();
    setupModeToggle();
  }

  /* ============================================================
     MODE TOGGLE (Phase 17.8)
     ============================================================ */

  function setupModeToggle() {
    if (modeToggleInitialized) return;
    modeToggleInitialized = true;

    var modeBtn = document.getElementById("btn-reader-mode");
    if (!modeBtn) return;

    updateModeButtonLabel(modeBtn);

    modeBtn.addEventListener("click", function () {
      readerMode = readerMode === "paged" ? "vertical" : "paged";
      localStorage.setItem("mangotoon_reader_mode", readerMode);
      updateModeButtonLabel(modeBtn);
      applyReaderMode();
    });
  }

  function updateModeButtonLabel(btn) {
    btn.textContent = readerMode === "paged" ? "\u25A6" : "\u25A1";
    btn.title = readerMode === "paged" ? "Switch to vertical mode" : "Switch to paged mode";
  }

  function applyReaderMode() {
    var main = document.getElementById("reader-main");
    var img = document.getElementById("reader-img");
    var verticalContainer = document.getElementById("reader-vertical-container");
    var zones = document.querySelectorAll(".reader-zone");
    var bottomBar = document.getElementById("reader-bottom");

    if (readerMode === "vertical") {
      // Hide paged elements
      if (img) img.hidden = true;
      zones.forEach(function (z) { z.hidden = true; });
      if (bottomBar) bottomBar.hidden = true;

      // Show vertical container
      if (!verticalContainer) {
        verticalContainer = document.createElement("div");
        verticalContainer.id = "reader-vertical-container";
        verticalContainer.className = "reader-vertical-container";
        main.appendChild(verticalContainer);
      }
      verticalContainer.hidden = false;

      renderVerticalMode();
    } else {
      // Hide vertical
      if (verticalContainer) verticalContainer.hidden = true;

      // Show paged elements
      zones.forEach(function (z) { z.hidden = false; });
      if (bottomBar) bottomBar.hidden = false;

      // Show current page
      if (img) {
        img.hidden = false;
        loadPage();
      }
    }
  }

  function renderVerticalMode() {
    var container = document.getElementById("reader-vertical-container");
    if (!container) return;

    var chapter = chapters[currentChapterIdx];
    if (!chapter) return;

    container.innerHTML = "";

    var pageCount = chapter.pages || 0;
    for (var i = 1; i <= pageCount; i++) {
      var wrapper = document.createElement("div");
      wrapper.className = "reader-vertical-page";
      wrapper.dataset.page = i;

      var img = document.createElement("img");
      img.className = "reader-vertical-img";
      img.alt = "Page " + i;
      img.dataset.page = i;
      img.dataset.src = buildPageSrc(i);
      img.loading = "lazy";

      // Loading placeholder
      var placeholder = document.createElement("div");
      placeholder.className = "reader-vertical-placeholder";
      placeholder.textContent = "Page " + i;

      wrapper.appendChild(placeholder);
      wrapper.appendChild(img);
      container.appendChild(wrapper);

      // Intersection observer for lazy loading + progress tracking
      observeVerticalPage(wrapper, img, placeholder);
    }

    // Preload first few images immediately
    for (var j = 1; j <= Math.min(3, pageCount); j++) {
      preloadVerticalPage(j);
    }
  }

  function observeVerticalPage(wrapper, img, placeholder) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          var pageNum = parseInt(img.dataset.page);
          img.src = img.dataset.src;
          img.onload = function () {
            placeholder.hidden = true;
            img.classList.add("loaded");
          };
          img.onerror = function () {
            placeholder.textContent = "Failed to load page " + pageNum;
            placeholder.classList.add("error");
          };

          // Update progress when page is visible
          currentPage = pageNum;
          updatePageIndicator();
          updateProgressBar();
          scheduleSaveProgress();

          // Preload next pages
          preloadVerticalRange(pageNum, 3);

          observer.unobserve(wrapper);
        }
      });
    }, { rootMargin: "200px" });

    observer.observe(wrapper);
  }

  function preloadVerticalPage(pageNum) {
    var src = buildPageSrc(pageNum);
    if (preloadCache[src]) return;

    var img = new Image();
    img.src = src;
    preloadCache[src] = img;
  }

  function preloadVerticalRange(fromPage, count) {
    for (var i = 0; i < count; i++) {
      var page = fromPage + i;
      if (page > totalPages) break;
      preloadVerticalPage(page);
    }
  }

  function buildPageSrc(pageNum) {
    var chapter = chapters[currentChapterIdx];
    if (!chapter) return "";
    return "/api/reader/" +
      encodeURIComponent(comicId) +
      "/" +
      encodeURIComponent(chapter.chapter_id) +
      "/" +
      pageNum;
  }

  /* ============================================================
     DATA LOADING
     ============================================================ */

  function loadReaderData(urlChapterId) {
    showDataLoading(true);
    hideError();

    API.get("/reader/" + encodeURIComponent(comicId) + "/data")
      .then(function (data) {
        readerData = data;
        chapters = data.chapters || [];

        if (chapters.length === 0) {
          showError("No downloaded chapters available.");
          return;
        }

        // Priority 1: chapter_id from URL query string
        var foundIdx = -1;
        if (urlChapterId) {
          for (var i = 0; i < chapters.length; i++) {
            if (chapters[i].chapter_id === urlChapterId) {
              foundIdx = i;
              break;
            }
          }
        }

        // Priority 2: saved reading progress
        if (foundIdx < 0) {
          var progress = data.progress;
          if (progress && progress.chapter_id) {
            for (var j = 0; j < chapters.length; j++) {
              if (chapters[j].chapter_id === progress.chapter_id) {
                foundIdx = j;
                break;
              }
            }
            if (foundIdx >= 0) {
              currentPage = progress.page || 1;
            }
          }
        }

        // Priority 3: first downloaded chapter
        currentChapterIdx = foundIdx >= 0 ? foundIdx : 0;
        if (foundIdx < 0) {
          currentPage = 1;
        }

        document.title = "MangoToon — " + (data.title || "Reader");
        renderChapterSelect();
        if (readerMode === "paged") {
          showChapter(currentChapterIdx, currentPage);
        } else {
          showChapter(currentChapterIdx, 1);
        }
      })
      .catch(function () {
        showError("Failed to load reader data.");
      })
      .finally(function () {
        showDataLoading(false);
      });
  }

  function loadChapterList() {
    API.get("/reader/" + encodeURIComponent(comicId))
      .then(function (data) {
        chaptersAll = data.chapters || [];
        renderChapterDrawer();
      })
      .catch(function () {
        showDrawerError("Failed to load chapter list.");
      });
  }

  /* ============================================================
     AUTO-HIDE UI
     ============================================================ */

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
      if (readerMode === "vertical") return; // Don't auto-hide in vertical mode
      if (top) top.classList.add("reader-hidden");
      if (bottom) bottom.classList.add("reader-hidden");
      uiVisible = false;
    }, 3000);
  }

  /* ============================================================
     CONTROLS SETUP
     ============================================================ */

  function setupControls() {
    document.getElementById("zone-prev").addEventListener("click", function () {
      if (readerMode !== "paged") return;
      goToPage(currentPage - 1);
      resetAutoHide();
    });
    document.getElementById("zone-next").addEventListener("click", function () {
      if (readerMode !== "paged") return;
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

    document.getElementById("btn-chapter-drawer").addEventListener("click", toggleChapterDrawer);
    document.getElementById("btn-drawer-close").addEventListener("click", closeChapterDrawer);
    document.getElementById("reader-drawer-overlay").addEventListener("click", closeChapterDrawer);

    document.getElementById("btn-next-chapter-overlay").addEventListener("click", function () {
      hideChapterComplete();
      goToNextChapter();
    });

    document.addEventListener("keydown", function (e) {
      if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA" || e.target.tagName === "SELECT") {
        return;
      }

      if (e.key === "c" || e.key === "C") {
        e.preventDefault();
        toggleChapterDrawer();
        return;
      }

      if (readerMode === "vertical") {
        // In vertical mode, only handle drawer and escape
        if (e.key === "Escape") {
          if (drawerOpen) {
            closeChapterDrawer();
          } else {
            window.location.href = "/";
          }
        }
        return;
      }

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
          if (drawerOpen) {
            closeChapterDrawer();
          } else {
            window.location.href = "/";
          }
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

  /* ============================================================
     CHAPTER / PAGE NAVIGATION
     ============================================================ */

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

    if (readerMode === "vertical") {
      renderVerticalMode();
      // Scroll to top
      var container = document.getElementById("reader-vertical-container");
      if (container) container.scrollTop = 0;
    } else {
      loadPage();
    }

    renderChapterDrawer();
  }

  /* ============================================================
     PAGE LOADING WITH PRELOAD (Phase 17.8)
     ============================================================ */

  function loadPage() {
    var chapter = chapters[currentChapterIdx];
    if (!chapter) return;

    var img = document.getElementById("reader-img");
    var loading = document.getElementById("reader-loading");
    var errorEl = document.getElementById("reader-error");

    // Increment token to invalidate old loads
    pageLoadToken++;
    var myToken = pageLoadToken;
    var loadStart = performance.now();

    img.hidden = true;
    loading.hidden = false;
    if (errorEl) errorEl.hidden = true;

    updatePageIndicator();
    updateProgressBar();

    var src = buildPageSrc(currentPage);

    console.debug("[reader] loadPage start | page=" + currentPage + " | src=" + src + " | token=" + myToken);

    // Check cache first
    if (preloadCache[src] && preloadCache[src].complete) {
      var cached = preloadCache[src];
      console.debug("[reader] cache hit | token=" + myToken + " | elapsed=" + (performance.now() - loadStart).toFixed(1) + "ms");
      renderLoadedImage(img, loading, errorEl, src, cached.naturalWidth, cached.naturalHeight, myToken, loadStart);
      return;
    }

    // Check if already loading
    if (preloadCache[src] && !preloadCache[src].complete) {
      console.debug("[reader] already loading | token=" + myToken + " | waiting...");
      var existingImg = preloadCache[src];
      existingImg.onload = function () {
        if (myToken !== pageLoadToken) {
          console.debug("[reader] stale load ignored | myToken=" + myToken + " | current=" + pageLoadToken);
          return;
        }
        renderLoadedImage(img, loading, errorEl, src, existingImg.naturalWidth, existingImg.naturalHeight, myToken, loadStart);
      };
      existingImg.onerror = function () {
        if (myToken !== pageLoadToken) return;
        renderLoadError(loading, img, "Page " + currentPage + " could not be loaded.");
      };
      return;
    }

    // Start new load
    var newImg = new Image();
    preloadCache[src] = newImg;

    newImg.onload = function () {
      if (myToken !== pageLoadToken) {
        console.debug("[reader] stale onload ignored | myToken=" + myToken + " | current=" + pageLoadToken);
        return;
      }
      renderLoadedImage(img, loading, errorEl, src, newImg.naturalWidth, newImg.naturalHeight, myToken, loadStart);
    };

    newImg.onerror = function () {
      if (myToken !== pageLoadToken) {
        console.debug("[reader] stale onerror ignored | myToken=" + myToken + " | current=" + pageLoadToken);
        return;
      }
      renderLoadError(loading, img, "Page " + currentPage + " could not be loaded.");
    };

    newImg.src = src;
  }

  function renderLoadedImage(img, loading, errorEl, src, naturalWidth, naturalHeight, token, loadStart) {
    var elapsed = performance.now() - loadStart;
    console.debug("[reader] loadPage end | token=" + token + " | elapsed=" + elapsed.toFixed(1) + "ms | dims=" + naturalWidth + "x" + naturalHeight);

    img.src = src;
    img.hidden = false;
    loading.hidden = true;
    if (errorEl) errorEl.hidden = true;
    applyZoom();
    applyFitMode();
    scheduleSaveProgress();
    checkChapterComplete();
    schedulePreload();
  }

  function renderLoadError(loading, img, msg) {
    loading.hidden = true;
    img.hidden = true;
    showPageError(msg);
  }

  function schedulePreload() {
    // Cancel any pending preload
    clearTimeout(preloadTimer);
    // Defer preload so it doesn't compete with manual navigation
    preloadTimer = setTimeout(preloadNeighbors, 100);
  }

  function preloadNeighbors() {
    // Preload ahead
    for (var i = 1; i <= maxPreloadAhead; i++) {
      var aheadPage = currentPage + i;
      if (aheadPage > totalPages) break;
      var aheadSrc = buildPageSrc(aheadPage);
      if (!preloadCache[aheadSrc]) {
        var img = new Image();
        img.src = aheadSrc;
        preloadCache[aheadSrc] = img;
      }
    }

    // Preload behind
    for (var j = 1; j <= maxPreloadBehind; j++) {
      var behindPage = currentPage - j;
      if (behindPage < 1) break;
      var behindSrc = buildPageSrc(behindPage);
      if (!preloadCache[behindSrc]) {
        var img2 = new Image();
        img2.src = behindSrc;
        preloadCache[behindSrc] = img2;
      }
    }

    // Preload next chapter first page
    if (currentChapterIdx < chapters.length - 1 && currentPage >= totalPages - 1) {
      var nextChapter = chapters[currentChapterIdx + 1];
      if (nextChapter && nextChapter.pages > 0) {
        var nextSrc = "/api/reader/" +
          encodeURIComponent(comicId) +
          "/" +
          encodeURIComponent(nextChapter.chapter_id) +
          "/1";
        if (!preloadCache[nextSrc]) {
          var nextImg = new Image();
          nextImg.src = nextSrc;
          preloadCache[nextSrc] = nextImg;
        }
      }
    }
  }

  function showPageError(msg) {
    var errorEl = document.getElementById("reader-error");
    var errorMsg = document.getElementById("reader-error-msg");
    if (errorEl) {
      errorEl.hidden = false;
      if (errorMsg) errorMsg.textContent = msg;
    }
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
    var now = Date.now();
    if (now < saveBackoffUntil) {
      return; // Skip save during backoff
    }

    var chapter = chapters[currentChapterIdx];
    if (!chapter) return;
    var completed = currentPage >= totalPages;
    API.post("/reader/" + encodeURIComponent(comicId) + "/progress", {
      chapter_id: chapter.chapter_id,
      page: currentPage,
      total_pages: totalPages,
      completed: completed,
    })
      .then(function () {
        saveFailCount = 0;
        saveBackoffUntil = 0;
      })
      .catch(function (err) {
        saveFailCount++;
        var backoffMs = Math.min(10000, saveFailCount * 2000);
        saveBackoffUntil = Date.now() + backoffMs;
        if (saveFailCount === 1 || saveFailCount % 5 === 0) {
          console.warn(
            "Progress save failed (backoff " + backoffMs + "ms):",
            err
          );
        }
      });
  }

  /* ============================================================
     CHAPTER SELECT
     ============================================================ */

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

  /* ============================================================
     CHAPTER DRAWER
     ============================================================ */

  function toggleChapterDrawer() {
    if (drawerOpen) {
      closeChapterDrawer();
    } else {
      openChapterDrawer();
    }
  }

  function openChapterDrawer() {
    drawerOpen = true;
    document.getElementById("reader-drawer-overlay").hidden = false;
    document.getElementById("reader-drawer").hidden = false;
    renderChapterDrawer();
  }

  function closeChapterDrawer() {
    drawerOpen = false;
    document.getElementById("reader-drawer-overlay").hidden = true;
    document.getElementById("reader-drawer").hidden = true;
  }

  function renderChapterDrawer() {
    if (!drawerOpen) return;

    var list = document.getElementById("reader-drawer-list");
    var errorEl = document.getElementById("reader-drawer-error");
    if (!list) return;

    if (chaptersAll.length === 0) {
      list.innerHTML =
        '<div class="reader-drawer-empty">No chapters available.</div>';
      errorEl.hidden = false;
      document.getElementById("reader-drawer-error-msg").textContent =
        "No chapters available.";
      return;
    }

    errorEl.hidden = true;

    var activeKey = "";
    var chapter = chapters[currentChapterIdx];
    if (chapter) {
      activeKey = chapter.chapter_id;
    }

    list.innerHTML = chaptersAll
      .map(function (ch) {
        var status = ch.status || "not_downloaded";
        var numLabel = ch.chapter_number || "?";
        var title = ch.title || "";
        var isActive = ch.chapter_id === activeKey;

        var actionsHtml = "";
        if (status === "not_downloaded") {
          actionsHtml =
            '<div class="reader-drawer-actions">' +
            '<button class="reader-drawer-dl-btn" title="Download" data-action="download" data-chapter-id="' +
            escapeAttr(ch.chapter_id) +
            '">\u2193</button>' +
            "</div>";
        } else if (status === "error" || status === "partial") {
          actionsHtml =
            '<div class="reader-drawer-actions">' +
            '<button class="reader-drawer-retry-btn" title="Retry" data-action="retry" data-chapter-id="' +
            escapeAttr(ch.chapter_id) +
            '">\u21BB</button>' +
            "</div>";
        } else if (status === "downloaded") {
          actionsHtml =
            '<div class="reader-drawer-actions">' +
            '<span class="reader-drawer-pages">' +
            (ch.pages || "?") +
            "p</span>" +
            "</div>";
        }

        var rowClass = "reader-drawer-chapter";
        if (isActive) {
          rowClass += " active";
        }
        if (status === "downloaded") {
          rowClass += " clickable";
        }

        return (
          '<div class="' +
          rowClass +
          '" data-chapter-id="' +
          escapeAttr(ch.chapter_id) +
          '" data-status="' +
          escapeAttr(status) +
          '">' +
          '<span class="reader-drawer-status ' +
          escapeAttr(status) +
          '"></span>' +
          '<span class="reader-drawer-chapter-num">Ch. ' +
          escapeHtml(String(numLabel)) +
          "</span>" +
          '<span class="reader-drawer-chapter-title">' +
          escapeHtml(title) +
          "</span>" +
          actionsHtml +
          "</div>"
        );
      })
      .join("");

    attachDrawerEvents();
  }

  function attachDrawerEvents() {
    var list = document.getElementById("reader-drawer-list");
    if (!list) return;

    var rows = list.querySelectorAll(".reader-drawer-chapter");
    for (var i = 0; i < rows.length; i++) {
      rows[i].addEventListener("click", function (e) {
        var target = e.target;
        if (target.tagName === "BUTTON") return;

        var row = target.closest(".reader-drawer-chapter");
        if (!row) return;

        var chapterId = row.getAttribute("data-chapter-id");
        var status = row.getAttribute("data-status");
        handleDrawerChapterClick(chapterId, status);
      });
    }

    var dlBtns = list.querySelectorAll('[data-action="download"]');
    for (var j = 0; j < dlBtns.length; j++) {
      dlBtns[j].addEventListener("click", function (e) {
        e.stopPropagation();
        var chapterId = this.getAttribute("data-chapter-id");
        downloadChapter(chapterId);
      });
    }

    var retryBtns = list.querySelectorAll('[data-action="retry"]');
    for (var k = 0; k < retryBtns.length; k++) {
      retryBtns[k].addEventListener("click", function (e) {
        e.stopPropagation();
        var chapterId = this.getAttribute("data-chapter-id");
        retryChapter(chapterId);
      });
    }
  }

  function handleDrawerChapterClick(chapterId, status) {
    if (status === "downloaded") {
      navigateToChapter(chapterId);
    } else if (status === "not_downloaded") {
      showToast("Chapter not downloaded. Click \u2193 to download.");
    } else if (status === "error") {
      showToast("Chapter download failed. Click \u21BB to retry.");
    } else if (status === "downloading") {
      showToast("Chapter is downloading...");
    } else if (status === "queued") {
      showToast("Chapter is queued for download.");
    }
  }

  function navigateToChapter(chapterId) {
    for (var i = 0; i < chapters.length; i++) {
      if (chapters[i].chapter_id === chapterId) {
        closeChapterDrawer();
        showChapter(i, 1);
        return;
      }
    }
    showToast("Chapter not yet downloaded.");
  }

  function downloadChapter(chapterId) {
    showToast("Starting download\u2026");

    API.post(
      "/library/" +
        encodeURIComponent(comicId) +
        "/chapters/" +
        encodeURIComponent(chapterId) +
        "/download"
    )
      .then(function () {
        showToast("Download started.");
        refreshChapterStatus(chapterId, "queued");
      })
      .catch(function () {
        showToast("Download failed.", true);
      });
  }

  function retryChapter(chapterId) {
    showToast("Retrying download\u2026");

    API.post(
      "/downloads/" +
        encodeURIComponent(comicId) +
        "/chapters/" +
        encodeURIComponent(chapterId) +
        "/retry"
    )
      .then(function () {
        showToast("Retry queued.");
        refreshChapterStatus(chapterId, "queued");
      })
      .catch(function () {
        showToast("Retry failed.", true);
      });
  }

  function refreshChapterStatus(chapterId, newStatus) {
    for (var i = 0; i < chaptersAll.length; i++) {
      if (chaptersAll[i].chapter_id === chapterId) {
        chaptersAll[i].status = newStatus;
        break;
      }
    }
    renderChapterDrawer();
  }

  function showDrawerError(msg) {
    var errorEl = document.getElementById("reader-drawer-error");
    if (errorEl) {
      errorEl.hidden = false;
      document.getElementById("reader-drawer-error-msg").textContent = msg;
    }
  }

  function showToast(msg, isError) {
    var toast = document.getElementById("reader-drawer-toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "reader-drawer-toast";
      toast.className = "reader-drawer-toast";
      toast.hidden = true;
      var drawer = document.getElementById("reader-drawer");
      if (drawer) drawer.appendChild(toast);
    }

    toast.textContent = msg;
    toast.className = "reader-drawer-toast";
    if (isError) {
      toast.classList.add("error");
    }
    toast.hidden = false;

    clearTimeout(toast._timer);
    toast._timer = setTimeout(function () {
      toast.hidden = true;
    }, 3000);
  }

  /* ============================================================
     UI TOGGLES
     ============================================================ */

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
      var labels = ["\u2296", "\u2194", "\u2195", "1:1"];
      btn.textContent = labels[fitMode] || "\u2296";
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

  function showDataLoading(show) {
    // Only show/hide the initial data loading overlay, not the page loading
    var overlay = document.getElementById("reader-data-loading");
    if (overlay) {
      overlay.hidden = !show;
    }
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
