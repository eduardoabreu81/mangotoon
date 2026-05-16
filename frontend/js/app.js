// ComicLib Frontend - Main Application Logic

const API_BASE = '/api';

// State
let library = [];
let currentComic = null;
let currentChapter = 0;
let currentPage = 0;
let totalPages = 0;

// DOM Elements
const libraryGrid = document.getElementById('library-grid');
const loadingEl = document.getElementById('loading');
const emptyState = document.getElementById('empty-state');
const searchInput = document.getElementById('search');
const filterSite = document.getElementById('filter-site');

// Modal
const addModal = document.getElementById('add-modal');
const urlInput = document.getElementById('url-input');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  loadLibrary();
  setupEventListeners();
});

function setupEventListeners() {
  // Search
  searchInput?.addEventListener('input', filterLibrary);

  // Filter by site
  filterSite?.addEventListener('change', filterLibrary);

  // Add comic form
  document.getElementById('add-form')?.addEventListener('submit', handleAddComic);
}

async function loadLibrary() {
  try {
    showLoading(true);
    const res = await fetch(`${API_BASE}/library`);
    if (!res.ok) throw new Error('Failed to load library');
    library = await res.json();
    renderLibrary();
  } catch (err) {
    console.error('Error loading library:', err);
  } finally {
    showLoading(false);
  }
}

function showLoading(show) {
  if (loadingEl) loadingEl.style.display = show ? 'flex' : 'none';
}

function renderLibrary() {
  if (!libraryGrid) return;

  if (library.length === 0) {
    libraryGrid.innerHTML = '';
    if (emptyState) emptyState.style.display = 'block';
    return;
  }

  if (emptyState) emptyState.style.display = 'none';

  libraryGrid.innerHTML = library.map(comic => `
    <div class="comic-card" onclick="openReader('${comic.id}')">
      ${comic.cover_url
        ? `<img class="comic-cover" src="${comic.cover_url}" alt="${comic.title}">`
        : `<div class="comic-cover-placeholder">📚</div>`
      }
      <div class="comic-info">
        <div class="comic-title">${escapeHtml(comic.title)}</div>
        <div class="comic-meta">
          <span>${comic.source_site}</span>
          <span class="status-badge status-${comic.status}">${comic.status}</span>
        </div>
        ${comic.total_chapters > 0 ? `
          <div class="comic-progress">
            <div class="comic-progress-bar" style="width: ${(comic.downloaded_chapters?.length / comic.total_chapters * 100) || 0}%"></div>
          </div>
        ` : ''}
      </div>
    </div>
  `).join('');
}

function filterLibrary() {
  const query = searchInput?.value.toLowerCase() || '';
  const site = filterSite?.value || '';

  const filtered = library.filter(comic => {
    const matchTitle = comic.title.toLowerCase().includes(query);
    const matchSite = !site || comic.source_site === site;
    return matchTitle && matchSite;
  });

  // Re-render with filtered (we need to temporarily swap library)
  const originalLibrary = library;
  library = filtered;
  renderLibrary();
  library = originalLibrary;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Modal functions
function showAddModal() {
  if (addModal) addModal.classList.add('active');
}

function hideAddModal() {
  if (addModal) {
    addModal.classList.remove('active');
    if (urlInput) urlInput.value = '';
  }
}

async function handleAddComic(e) {
  e.preventDefault();
  if (!urlInput) return;

  const url = urlInput.value.trim();
  if (!url) return;

  try {
    const res = await fetch(`${API_BASE}/library/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });

    if (!res.ok) throw new Error('Failed to add comic');

    const data = await res.json();
    hideAddModal();
    loadLibrary();

    // If we're in reader mode, we could redirect
    if (currentComic) {
      // Refresh
    }
  } catch (err) {
    console.error('Error adding comic:', err);
    alert('Erro ao adicionar quadrinho');
  }
}

// Reader functions
let readerWindow = null;

function openReader(comicId) {
  readerWindow = window.open(`reader.html?comic=${comicId}`, '_blank');
}

async function loadComicInReader(comicId) {
  try {
    const res = await fetch(`${API_BASE}/library/${comicId}`);
    if (!res.ok) throw new Error('Comic not found');
    currentComic = await res.json();

    // Get chapters
    const chapters = currentComic.chapters || [];

    if (chapters.length === 0) {
      alert('Nenhum capítulo disponível');
      return;
    }

    // Load last reading position or start from beginning
    const progress = await fetch(`${API_BASE}/reader/${comicId}/progress`).then(r => r.json()).catch(() => ({}));
    currentChapter = progress.last_chapter || (chapters[0]?.number || 1);
    currentPage = progress.last_page || 1;

    // Update UI
    updateReaderUI();
    loadPage();

  } catch (err) {
    console.error('Error loading comic:', err);
    alert('Erro ao carregar quadrinho');
  }
}

function updateReaderUI() {
  const titleEl = document.getElementById('reader-title');
  const pageEl = document.getElementById('page-indicator');
  const chapterSelect = document.getElementById('chapter-select');

  if (titleEl && currentComic) {
    titleEl.textContent = currentComic.title;
  }

  if (pageEl) {
    pageEl.textContent = `${currentPage} / ${totalPages}`;
  }

  // Populate chapter select
  if (chapterSelect && currentComic?.chapters) {
    chapterSelect.innerHTML = currentComic.chapters.map(ch =>
      `<option value="${ch.number}" ${ch.number === currentChapter ? 'selected' : ''}>Capítulo ${ch.number} - ${ch.title}</option>`
    ).join('');
  }
}

function loadPage() {
  const img = document.getElementById('page-image');
  if (!img || !currentComic) return;

  img.src = `${API_BASE}/reader/${currentComic.id}/${currentChapter}/${currentPage}`;
  img.onload = () => {
    const pageEl = document.getElementById('page-indicator');
    if (pageEl) pageEl.textContent = `${currentPage} / ${totalPages}`;
  };
}

function navigatePage(direction) {
  const newPage = currentPage + direction;
  if (newPage < 1 || newPage > totalPages) return;

  currentPage = newPage;
  loadPage();
  saveProgress();
}

function goToChapter(chapterNum) {
  currentChapter = parseFloat(chapterNum);
  currentPage = 1;
  loadPage();
  saveProgress();
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

// Keyboard navigation
document.addEventListener('keydown', (e) => {
  if (readerWindow && readerWindow.document) {
    // Handled in reader window
  }

  switch(e.key) {
    case 'ArrowLeft':
      navigatePage(-1);
      break;
    case 'ArrowRight':
      navigatePage(1);
      break;
    case 'f':
    case 'F':
      toggleFullscreen();
      break;
    case 'Escape':
      if (readerWindow) readerWindow.close();
      break;
  }
});

// Touch/Swipe support
let touchStartX = 0;

document.addEventListener('touchstart', (e) => {
  touchStartX = e.touches[0].clientX;
});

document.addEventListener('touchend', (e) => {
  const touchEndX = e.changedTouches[0].clientX;
  const diff = touchStartX - touchEndX;

  if (Math.abs(diff) > 50) {
    if (diff > 0) {
      navigatePage(1); // Swipe left = next page
    } else {
      navigatePage(-1); // Swipe right = prev page
    }
  }
});