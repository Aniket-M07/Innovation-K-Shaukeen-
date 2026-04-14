/**
 * Campus Search Engine - Interactive UI Components
 * Handles search, autocomplete, loading states, and dynamic rendering
 */

// ===== STATE MANAGEMENT =====
const state = {
	isSearching: false,
	currentQuery: '',
	autocompleteTimer: null,
	activeQuery: '',
};

// ===== DOM ELEMENTS =====
const elements = {
	searchForm: null,
	searchInput: null,
	suggestionsContainer: null,
	inlineResultsSection: null,
	inlineResultsContent: null,
	inlineResultsCount: null,
	uploadForm: null,
	recentToggle: null,
	recentDropdown: null,
	themeToggle: null,
	recentlyViewedList: null,
	aiSuggestionsList: null,
	galleryModal: null,
	galleryModalTitle: null,
	galleryModalDesc: null,
	galleryModalEmoji: null,
	galleryModalClose: null,
};

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', () => {
	initializeElements();
	setupEventListeners();
	setupThemeToggle();
	renderRecentlyViewed();
	setupScrollEffects();
	console.log('Campus Search Engine initialized');
});

/**
 * Initialize DOM element references
 */
function initializeElements() {
	elements.searchInput = document.getElementById('query');
	elements.suggestionsContainer = document.getElementById('suggestions');
	elements.inlineResultsSection = document.getElementById('inline-results-section');
	elements.inlineResultsContent = document.getElementById('inline-results-content');
	elements.inlineResultsCount = document.getElementById('inline-results-count');
	elements.searchForm = document.querySelector('#search-section form');
	elements.uploadForm = document.querySelector('#upload-section form');
	elements.recentToggle = document.getElementById('recent-toggle');
	elements.recentDropdown = document.getElementById('recent-dropdown');
	elements.themeToggle = document.getElementById('theme-toggle');
	elements.recentlyViewedList = document.getElementById('recently-viewed-list');
	elements.aiSuggestionsList = document.getElementById('ai-suggestions-list');
	elements.galleryModal = document.getElementById('gallery-modal');
	elements.galleryModalTitle = document.getElementById('gallery-modal-title');
	elements.galleryModalDesc = document.getElementById('gallery-modal-desc');
	elements.galleryModalEmoji = document.getElementById('gallery-modal-emoji');
	elements.galleryModalClose = document.getElementById('gallery-modal-close');
}

// ===== EVENT LISTENERS =====
function setupEventListeners() {
	// Autocomplete on search input
	if (elements.searchInput) {
		elements.searchInput.addEventListener('input', handleSearchInput);
		elements.searchInput.addEventListener('keydown', handleKeyNavigation);
	}

	// Voice search and clear button
	const voiceButton = document.getElementById('voice-search');
	const clearButton = document.getElementById('clear-search');
	if (voiceButton) voiceButton.addEventListener('click', handleVoiceSearch);
	if (clearButton) clearButton.addEventListener('click', handleClearSearch);
	if (elements.recentToggle) elements.recentToggle.addEventListener('click', toggleRecentDropdown);

	// Click handler for autocomplete suggestions
	if (elements.suggestionsContainer) {
		elements.suggestionsContainer.addEventListener('click', handleSuggestionClick);
	}

	if (elements.themeToggle) {
		elements.themeToggle.addEventListener('click', toggleTheme);
	}

	// Close suggestions when clicking outside
	document.addEventListener('click', (event) => {
		if (!event.target.closest('.autocomplete')) {
			clearSuggestions();
		}
		if (!event.target.closest('.recent-dropdown-wrap') && elements.recentDropdown && elements.recentToggle) {
			elements.recentDropdown.hidden = true;
			elements.recentToggle.setAttribute('aria-expanded', 'false');
		}
	});

	// Search form submission with loading indicator
	if (elements.searchForm) {
		elements.searchForm.addEventListener('submit', handleSearchSubmit);
	}

	// Upload form submission
	if (elements.uploadForm) {
		elements.uploadForm.addEventListener('submit', handleUploadSubmit);
	}

	// Quick search links (recent + trending) should search inline without refresh.
	document.addEventListener('click', (event) => {
		const link = event.target.closest('.quick-search-link');
		if (!link) return;
		event.preventDefault();
		const query = (link.dataset.query || '').trim();
		if (!query || !elements.searchInput) return;
		elements.searchInput.value = query;
		elements.searchInput.focus();
		handleSearchSubmit(new Event('submit'));
	});

	document.addEventListener('click', (event) => {
		const chip = event.target.closest('.filter-chip');
		if (!chip) return;
		event.preventDefault();
		const filterType = chip.dataset.filter;
		const filterValue = chip.dataset.value;
		if (filterType === 'category') {
			const categoryFilter = document.getElementById('category-filter');
			if (categoryFilter) categoryFilter.value = filterValue;
			document.querySelectorAll('.filter-chip[data-filter="category"]').forEach(item => item.classList.remove('active'));
			chip.classList.add('active');
		}
	});

	document.addEventListener('click', (event) => {
		const helpBtn = event.target.closest('#feedback-help-button');
		if (!helpBtn) return;
		showNotification('Need help? Email support@university.edu or use AI chat in bottom corner.', 'info');
	});

	if (elements.galleryModalClose) {
		elements.galleryModalClose.addEventListener('click', closeGalleryModal);
	}

	document.addEventListener('click', (event) => {
		const galleryCard = event.target.closest('.gallery-item');
		if (galleryCard) {
			openGalleryModal(galleryCard);
			return;
		}
		if (event.target.closest('[data-close-gallery="1"]')) {
			closeGalleryModal();
		}
	});
}

function openGalleryModal(card) {
	if (!elements.galleryModal || !elements.galleryModalTitle || !elements.galleryModalDesc || !elements.galleryModalEmoji) return;
	const title = card.dataset.galleryTitle || 'Campus View';
	const desc = card.dataset.galleryDesc || 'Explore this campus space.';
	const emoji = card.dataset.galleryEmoji || '🏫';

	elements.galleryModalTitle.textContent = title;
	elements.galleryModalDesc.textContent = desc;
	elements.galleryModalEmoji.textContent = emoji;
	elements.galleryModal.hidden = false;
	elements.galleryModal.setAttribute('aria-hidden', 'false');
	document.body.style.overflow = 'hidden';
}

function closeGalleryModal() {
	if (!elements.galleryModal) return;
	elements.galleryModal.hidden = true;
	elements.galleryModal.setAttribute('aria-hidden', 'true');
	document.body.style.overflow = '';
}

function setupThemeToggle() {
	const savedTheme = localStorage.getItem('campus_theme') || 'light';
	document.documentElement.setAttribute('data-theme', savedTheme);
	if (elements.themeToggle) {
		elements.themeToggle.textContent = savedTheme === 'dark' ? 'Light mode' : 'Dark mode';
	}
}

function toggleTheme() {
	const current = document.documentElement.getAttribute('data-theme') || 'light';
	const next = current === 'dark' ? 'light' : 'dark';
	document.documentElement.setAttribute('data-theme', next);
	localStorage.setItem('campus_theme', next);
	if (elements.themeToggle) {
		elements.themeToggle.textContent = next === 'dark' ? 'Light mode' : 'Dark mode';
	}
}

function toggleRecentDropdown() {
	if (!elements.recentDropdown || !elements.recentToggle) return;
	const willOpen = elements.recentDropdown.hidden;
	elements.recentDropdown.hidden = !willOpen;
	elements.recentToggle.setAttribute('aria-expanded', String(willOpen));
}

// ===== AUTOCOMPLETE FUNCTIONALITY =====
/**
 * Handle search input changes and trigger autocomplete
 */
function handleSearchInput() {
	clearTimeout(state.autocompleteTimer);

	const value = elements.searchInput.value.trim();
	state.currentQuery = value;

	if (!value) {
		clearSuggestions();
		return;
	}

	// Debounce autocomplete requests
	state.autocompleteTimer = setTimeout(async () => {
		await fetchAutocomplete(value);
	}, 250);
}

/**
 * Simulate voice search input and update query field
 */
function handleVoiceSearch() {
	const simulated = prompt('Simulated voice input:', 'Find faculty contact');
	if (!simulated) return;
	if (elements.searchInput) {
		elements.searchInput.value = simulated;
		elements.searchInput.focus();
		elements.searchInput.dispatchEvent(new Event('input', { bubbles: true }));
	}
}

/**
 * Clear the search input and suggestions
 */
function handleClearSearch() {
	if (elements.searchInput) {
		elements.searchInput.value = '';
		clearSuggestions();
		elements.searchInput.focus();
	}
}

/**
 * Fetch autocomplete suggestions from backend
 */
async function fetchAutocomplete(query) {
	try {
		const response = await fetch(`/autocomplete?q=${encodeURIComponent(query)}`);

		if (!response.ok) {
			throw new Error('Autocomplete request failed');
		}

		const data = await response.json();

		if (!data.suggestions || data.suggestions.length === 0) {
			clearSuggestions();
			return;
		}

		renderSuggestions(data.suggestions);
	} catch (error) {
		console.error('Autocomplete error:', error);
		clearSuggestions();
	}
}

/**
 * Render autocomplete suggestions
 */
function renderSuggestions(suggestions) {
	if (!elements.suggestionsContainer) return;

	elements.suggestionsContainer.innerHTML = suggestions
		.map((item, index) => `
			<button 
				type="button" 
				data-term="${escapeHtml(item.term)}"
				data-index="${index}"
				class="suggestion-item"
			>
				${escapeHtml(item.term)}
				${item.frequency ? `<span class="frequency">(${item.frequency})</span>` : ''}
			</button>
		`)
		.join('');

	elements.suggestionsContainer.hidden = false;
}

/**
 * Clear autocomplete suggestions
 */
function clearSuggestions() {
	if (elements.suggestionsContainer) {
		elements.suggestionsContainer.innerHTML = '';
		elements.suggestionsContainer.hidden = true;
	}
}

/**
 * Handle suggestion click
 */
function handleSuggestionClick(event) {
	const button = event.target.closest('button');
	if (!button?.dataset?.term) return;

	elements.searchInput.value = button.dataset.term;
	clearSuggestions();
	elements.searchInput.focus();
}

/**
 * Handle keyboard navigation in suggestions
 */
function handleKeyNavigation(event) {
	if (!elements.suggestionsContainer || elements.suggestionsContainer.hidden) return;

	const suggestions = elements.suggestionsContainer.querySelectorAll('button');
	if (suggestions.length === 0) return;

	const currentIndex = Array.from(suggestions).findIndex(btn =>
		btn === document.activeElement
	);

	switch (event.key) {
		case 'ArrowDown':
			event.preventDefault();
			if (currentIndex < suggestions.length - 1) {
				suggestions[currentIndex + 1].focus();
			} else {
				suggestions[0].focus();
			}
			break;

		case 'ArrowUp':
			event.preventDefault();
			if (currentIndex > 0) {
				suggestions[currentIndex - 1].focus();
			} else {
				elements.searchInput.focus();
			}
			break;

		case 'Escape':
			clearSuggestions();
			elements.searchInput.focus();
			break;

		case 'Enter':
			if (document.activeElement.classList.contains('suggestion-item')) {
				event.preventDefault();
				document.activeElement.click();
			}
			break;
	}
}

// ===== SEARCH FUNCTIONALITY =====
/**
 * Handle search form submission
 */
async function handleSearchSubmit(event) {
	event.preventDefault();

	const query = elements.searchInput.value.trim();
	if (!query) {
		showNotification('Please enter a search query', 'warning');
		return;
	}

	// Save local search history for quick access across sections
	const localHistory = JSON.parse(localStorage.getItem('campus_recent_searches') || '[]');
	const dedup = localHistory.filter(item => item.toLowerCase() !== query.toLowerCase());
	dedup.unshift(query);
	localStorage.setItem('campus_recent_searches', JSON.stringify(dedup.slice(0, 20)));

	showLoadingIndicator();
	clearSuggestions();
	state.activeQuery = query;

	try {
		const payload = await performSearch(query);
		renderResults(payload);
		trackSearchAnalytics(query);
	} catch (error) {
		console.error('Search error:', error);
		showNotification('Search failed. Please try again.', 'error');
	} finally {
		hideLoadingIndicator();
	}
}

/**
 * Perform search request to backend and return JSON payload
 */
async function performSearch(query) {
	const params = new URLSearchParams({ q: query });
	const categoryFilter = document.getElementById('category-filter');
	const departmentFilter = document.getElementById('department-filter');
	const serviceTypeFilter = document.getElementById('service-type-filter');
	const audienceFilter = document.getElementById('audience-filter');
	if (categoryFilter?.value) {
		params.set('category', categoryFilter.value);
	}
	if (departmentFilter?.value) {
		params.set('department', departmentFilter.value);
	}
	if (serviceTypeFilter?.value) {
		params.set('service_type', serviceTypeFilter.value);
	}
	if (audienceFilter?.value) {
		params.set('audience', audienceFilter.value);
	}

	const response = await fetch(`/api/search?${params.toString()}`, {
		headers: { 'Accept': 'application/json' },
	});

	if (!response.ok) {
		throw new Error('Search request failed');
	}

	return response.json();
}

/**
 * Render search results dynamically
 */
function renderResults(payload) {
	if (!elements.inlineResultsContent) return;

	const groupedResults = payload?.grouped_results || {};
	const resultItems = payload?.results || [];
	const resultCount = payload?.count || 0;

	if (elements.inlineResultsCount) {
		elements.inlineResultsCount.textContent = resultCount > 0
			? `${resultCount} result${resultCount === 1 ? '' : 's'} found`
			: 'No results found';
	}

	if (!resultItems.length) {
		elements.inlineResultsContent.innerHTML = `
			<div class="inline-results-empty">
				<p><strong>No results found.</strong></p>
				<p>Try broader keywords like <em>library</em>, <em>IT support</em>, or <em>scholarship</em>.</p>
			</div>
		`;
		return;
	}

	const groupedHtml = Object.entries(groupedResults)
		.map(([category, items]) => `
			<div class="result-group">
				<h3>${escapeHtml(category)}</h3>
				<div class="results-grid">
					${items.map(item => createResultCard(item, state.activeQuery)).join('')}
				</div>
			</div>
		`)
		.join('');

	elements.inlineResultsContent.innerHTML = groupedHtml || `
		<div class="results-grid">
			${resultItems.map(result => createResultCard(result, state.activeQuery)).join('')}
		</div>
	`;

	if (elements.aiSuggestionsList && Array.isArray(payload?.ai_suggested_resources)) {
		elements.aiSuggestionsList.innerHTML = payload.ai_suggested_resources
			.map(item => `<li>${escapeHtml(item)}</li>`)
			.join('');
	}

	// Add fade-in animation
	const cards = elements.inlineResultsContent.querySelectorAll('.result-card');
	cards.forEach((card, index) => {
		card.style.opacity = '0';
		card.style.transform = 'translateY(20px)';
		setTimeout(() => {
			card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
			card.style.opacity = '1';
			card.style.transform = 'translateY(0)';
		}, index * 50);
	});
}

/**
 * Create HTML for a result card
 */
function createResultCard(result, query = '') {
	const title = highlightMatches(escapeHtml(result.title || 'Untitled'), query);
	const snippet = highlightMatches(escapeHtml(result.snippet || 'No preview available.'), query);
	const filename = escapeHtml(result.filename || '');
	const score = result.score || 0;
	const department = escapeHtml(result.department || 'General');
	const serviceType = escapeHtml(result.service_type || 'Information');
	const audience = escapeHtml(result.audience || 'All');
	const favorite = isFavorite(filename) ? 'active' : '';

	return `
		<div class="result-card">
			<div class="result-top-row">
				<button type="button" class="favorite-btn ${favorite}" data-favorite="${filename}" aria-label="Toggle favorite">★</button>
			</div>
			<div class="result-title">${title}</div>
			<div class="result-snippet">${snippet}</div>
			<div class="result-meta">
				<small>📁 ${filename}</small>
				<span class="badge">${department}</span>
				<span class="badge">${serviceType}</span>
				<span class="badge">${audience}</span>
				<span class="badge">Score: ${score}</span>
			</div>
			<div class="result-actions">
				<a href="/files/${encodeURIComponent(filename)}" target="_blank" class="resource-link" data-title="${escapeHtml(result.title || '')}" data-file="${filename}">Open</a>
				<a href="/files/${encodeURIComponent(filename)}?download=1" class="resource-link" data-title="${escapeHtml(result.title || '')}" data-file="${filename}">Download</a>
			</div>
		</div>
	`;
}

function highlightMatches(text, query) {
	if (!query) return text;
	const tokens = query.trim().split(/\s+/).filter(Boolean).map(token => token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
	if (!tokens.length) return text;
	const regex = new RegExp(`(${tokens.join('|')})`, 'ig');
	return text.replace(regex, '<mark>$1</mark>');
}

function getFavorites() {
	return JSON.parse(localStorage.getItem('campus_favorites') || '[]');
}

function isFavorite(filename) {
	return getFavorites().includes(filename);
}

function toggleFavorite(filename) {
	if (!filename) return;
	const favorites = getFavorites();
	const index = favorites.indexOf(filename);
	if (index >= 0) {
		favorites.splice(index, 1);
	} else {
		favorites.push(filename);
	}
	localStorage.setItem('campus_favorites', JSON.stringify(favorites));
}

function addRecentlyViewed(title, filename) {
	if (!filename) return;
	const list = JSON.parse(localStorage.getItem('campus_recently_viewed') || '[]');
	const deduped = list.filter(item => item.filename !== filename);
	deduped.unshift({ title, filename });
	localStorage.setItem('campus_recently_viewed', JSON.stringify(deduped.slice(0, 8)));
	renderRecentlyViewed();
}

function renderRecentlyViewed() {
	if (!elements.recentlyViewedList) return;
	const list = JSON.parse(localStorage.getItem('campus_recently_viewed') || '[]');
	if (!list.length) {
		elements.recentlyViewedList.innerHTML = '<li class="empty">No recently viewed resources yet.</li>';
		return;
	}
	elements.recentlyViewedList.innerHTML = list
		.map(item => `<li><a href="/files/${encodeURIComponent(item.filename)}" class="resource-link" data-title="${escapeHtml(item.title || item.filename)}" data-file="${escapeHtml(item.filename)}">${escapeHtml(item.title || item.filename)}</a></li>`)
		.join('');
}

async function trackSearchAnalytics(query) {
	try {
		await fetch('/api/search-analytics', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ query }),
		});
	} catch (error) {
		console.debug('Analytics hook failed silently', error);
	}
}

// ===== UPLOAD FUNCTIONALITY =====
/**
 * Handle upload form submission
 */
function handleUploadSubmit(event) {
	const fileInput = elements.uploadForm.querySelector('input[type="file"]');

	if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
		event.preventDefault();
		showNotification('Please select a file to upload', 'warning');
		return;
	}

	const file = fileInput.files[0];
	const validExtensions = ['pdf', 'txt'];
	const fileExtension = file.name.split('.').pop().toLowerCase();

	if (!validExtensions.includes(fileExtension)) {
		event.preventDefault();
		showNotification('Only PDF and TXT files are supported', 'error');
		return;
	}

	// Show uploading indicator
	const submitButton = elements.uploadForm.querySelector('button[type="submit"]');
	if (submitButton) {
		submitButton.disabled = true;
		submitButton.textContent = '⏳ Uploading...';
	}

	showNotification(`Uploading ${file.name}...`, 'info');
}

// ===== LOADING INDICATOR =====
/**
 * Show loading indicator
 */
function showLoadingIndicator() {
	state.isSearching = true;

	if (elements.inlineResultsSection) {
		elements.inlineResultsSection.classList.add('loading');
	}

	// Disable search button
	const searchButton = elements.searchForm?.querySelector('button[type="submit"]');
	if (searchButton) {
		searchButton.disabled = true;
		searchButton.innerHTML = '⏳ Searching...';
	}

	if (elements.inlineResultsCount) {
		elements.inlineResultsCount.textContent = 'Searching...';
	}

	// Show spinner in inline results area
	if (elements.inlineResultsContent) {
		elements.inlineResultsContent.innerHTML = `
			<div style="text-align: center; padding: 1.75rem 0.5rem;">
				<div class="spinner"></div>
				<p style="color: #718096; margin-top: 1rem;">Searching documents...</p>
			</div>
		`;
	}
}

/**
 * Hide loading indicator
 */
function hideLoadingIndicator() {
	state.isSearching = false;

	if (elements.inlineResultsSection) {
		elements.inlineResultsSection.classList.remove('loading');
	}

	// Enable search button
	const searchButton = elements.searchForm?.querySelector('button[type="submit"]');
	if (searchButton) {
		searchButton.disabled = false;
		searchButton.innerHTML = 'Search';
	}
}

/**
 * Scroll to search section (triggered by nav search icon)
 */
window.scrollToSearch = function () {
	const searchSection = document.getElementById('search-section');
	if (searchSection) {
		searchSection.scrollIntoView({ behavior: 'smooth' });
		setTimeout(() => {
			if (elements.searchInput) {
				elements.searchInput.focus();
			}
		}, 500);
	}
};

/**
 * Setup scroll effects (sticky nav, etc.)
 */
function setupScrollEffects() {
	let lastScrollTop = 0;
	const nav = document.querySelector('nav');

	window.addEventListener('scroll', () => {
		const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

		// Add shadow to nav when scrolled
		if (nav) {
			if (scrollTop > 50) {
				nav.classList.add('scrolled');
			} else {
				nav.classList.remove('scrolled');
			}
		}

		lastScrollTop = scrollTop;
	});
}

// ===== NOTIFICATION SYSTEM =====
/**
 * Show notification to user
 */
function showNotification(message, type = 'info') {
	const notification = document.createElement('div');
	notification.className = `notification notification-${type}`;
	notification.textContent = message;

	// Add styles inline for simplicity
	Object.assign(notification.style, {
		position: 'fixed',
		top: '20px',
		right: '20px',
		padding: '1rem 1.5rem',
		borderRadius: '8px',
		background: type === 'error' ? '#f56565' :
			type === 'warning' ? '#ed8936' :
				type === 'success' ? '#48bb78' : '#667eea',
		color: 'white',
		fontWeight: '600',
		boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
		zIndex: '10000',
		animation: 'slideInRight 0.3s ease',
		maxWidth: '300px',
	});

	document.body.appendChild(notification);

	// Auto remove after 3 seconds
	setTimeout(() => {
		notification.style.animation = 'slideOutRight 0.3s ease';
		setTimeout(() => notification.remove(), 300);
	}, 3000);
}

// ===== UTILITY FUNCTIONS =====
/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
	const map = {
		'&': '&amp;',
		'<': '&lt;',
		'>': '&gt;',
		'"': '&quot;',
		"'": '&#039;',
	};
	return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * Debounce function for performance
 */
function debounce(func, wait) {
	let timeout;
	return function executedFunction(...args) {
		const later = () => {
			clearTimeout(timeout);
			func(...args);
		};
		clearTimeout(timeout);
		timeout = setTimeout(later, wait);
	};
}

// ===== KEYBOARD SHORTCUTS =====
document.addEventListener('keydown', (event) => {
	if (event.key === 'Escape' && elements.galleryModal && !elements.galleryModal.hidden) {
		closeGalleryModal();
		return;
	}

	// Ctrl/Cmd + K to focus search
	if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
		event.preventDefault();
		if (elements.searchInput) {
			elements.searchInput.focus();
			elements.searchInput.select();
		}
	}
});

document.addEventListener('click', (event) => {
	const favoriteButton = event.target.closest('.favorite-btn');
	if (favoriteButton) {
		const filename = favoriteButton.dataset.favorite || '';
		toggleFavorite(filename);
		favoriteButton.classList.toggle('active', isFavorite(filename));
		return;
	}

	const resourceLink = event.target.closest('.resource-link');
	if (resourceLink) {
		addRecentlyViewed(resourceLink.dataset.title || '', resourceLink.dataset.file || '');
	}
});

// ===== EXPORT FOR TESTING =====
if (typeof module !== 'undefined' && module.exports) {
	module.exports = {
		state,
		escapeHtml,
		debounce,
	};
}
