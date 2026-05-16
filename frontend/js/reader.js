// ComicLib Reader Logic

const API_BASE = '/api';

// State
let currentComic = null;
let currentChapter = 1;
let currentPage = 1;
let totalPages = 1;
let zoomLevel = 100;

// DOM Elements
const pageImage = document.getElementById('page-image');
const pageIndicator = document.getElementById('page-indicator');
const chapterSelect = document.getElementById('chapter-select');
const readerTitle = document.getElementById('reader-title');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  const comicId = params.get('comic');

  if (comicId) {
    loadComic(comicId);
  } else {
    document.getElementById('reader-title').textContent = 'Erro: Comic não especificado';
  }

  setupKeyboardControls();
  setupSwipeControls();
});

async function loadComic(comicId) {
  try {
    // Load comic metadata
    const res = await fetch(`${API_BASE}/library/${comicId}`);
    if (!res.ok) throw new Error('Quadrinho não encontrado');
    currentComic = await res.json();

    readerTitle.textContent = currentComic.title;

    // Load reading progress
    let progress = { last_chapter: 1, last_page: 1 };
    try {
      const progressRes = await fetch(`${API_BASE}/reader/${comicId}/progress`);
      if (progressRes.ok) {
        progress = await progressRes.json();
      }
    } catch (e) {
      console.log('Could not load progress');
    }

    // Initialize chapter list
    populateChapters();

    // Set starting position
    currentChapter = progress.last_chapter || 1;
    currentPage = progress.last_page || 1;

    // Get total pages for this chapter
    await loadPageInfo();

    // Load first page
    loadPage();

  } catch (err) {
    console.error('Error loading comic:', err);
    readerTitle.textContent = 'Erro ao carregar';
  }
}

function populateChapters() {
  if (!currentComic || !currentComic.chapters) return;

  chapterSelect.innerHTML = currentComic.chapters.map(ch => {
    const chNum = typeof ch.number === 'string' ? parseFloat(ch.number) : ch.number;
    const selected = chNum === currentChapter ? 'selected' : '';
    return `<option value="${chNum}" ${selected}>Cap. ${chNum} - ${ch.title || ''}</option>`;
  }).join('');
}

async function loadPageInfo() {
  if (!currentComic) return;

  // Try to get chapter info
  const chapter = currentComic.chapters?.find(c => c.number === currentChapter);
  if (chapter && chapter.pages) {
    totalPages = chapter.pages.length;
  } else {
    // Try to detect from directory
    totalPages = await detectTotalPages();
  }

  updatePageIndicator();
}

async function detectTotalPages() {
  // Heuristic: try to detect how many pages exist
  // For now, return 20 as default
  return 20;
}

function loadPage() {
  if (!currentComic) return;

  pageImage.src = `${API_BASE}/reader/${currentComic.id}/${currentChapter}/${currentPage}`;
  pageImage.onload = () => {
    updatePageIndicator();
    saveProgress();
  };

  pageImage.onerror = () => {
    pageImage.alt = 'Página não encontrada';
  };
}

function updatePageIndicator() {
  pageIndicator.textContent = `${currentPage} / ${totalPages}`;
}

function navigatePage(direction) {
  const newPage = currentPage + direction;
  if (newPage < 1 || newPage > totalPages) return;

  currentPage = newPage;
  loadPage();
}

function goToChapter(chapterNum) {
  const ch = parseFloat(chapterNum);
  if (ch !== currentChapter) {
    currentChapter = ch;
    currentPage = 1;
    loadPageInfo();
    loadPage();
  }
}

async function saveProgress() {
  if (!currentComic) return;

  try {
    await fetch(`${API_BASE}/reader/${currentComic.id}/progress`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chapter: currentChapter,
        page: currentPage,
        completed: currentPage >= totalPages
      })
    });
  } catch (err) {
    console.error('Error saving progress:', err);
  }
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen();
  } else {
    document.exitFullscreen();
  }
}

function setupKeyboardControls() {
  document.addEventListener('keydown', (e) => {
    switch (e.key) {
      case 'ArrowLeft':
      case 'PageUp':
        navigatePage(-1);
        break;
      case 'ArrowRight':
      case 'PageDown':
      case ' ':
        navigatePage(1);
        break;
      case 'Home':
        currentPage = 1;
        loadPage();
        break;
      case 'End':
        currentPage = totalPages;
        loadPage();
        break;
      case 'f':
      case 'F':
        toggleFullscreen();
        break;
      case 'Escape':
        window.close();
        break;
    }
  });
}

// Swipe controls
let touchStartX = 0;
let touchStartY = 0;

document.addEventListener('touchstart', (e) => {
  touchStartX = e.touches[0].clientX;
  touchStartY = e.touches[0].clientY;
}, { passive: true });

document.addEventListener('touchend', (e) => {
  const touchEndX = e.changedTouches[0].clientX;
  const touchEndY = e.changedTouches[0].clientY;
  const diffX = touchStartX - touchEndX;
  const diffY = touchStartY - touchEndY;

  // Only handle horizontal swipes (not scrolls)
  if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
    if (diffX > 0) {
      navigatePage(1); // Swipe left = next page
    } else {
      navigatePage(-1); // Swipe right = previous page
    }
  }
}, { passive: true });

// Page slider
document.getElementById('page-slider')?.addEventListener('input', (e) => {
  const page = parseInt(e.target.value);
  if (page !== currentPage) {
    currentPage = page;
    loadPage();
  }
});