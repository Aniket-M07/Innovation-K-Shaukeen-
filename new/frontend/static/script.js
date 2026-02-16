/**
 * Campus Search Engine - Interactive UI Components
 * Handles search, autocomplete, loading states, and dynamic rendering
 */

// ===== STATE MANAGEMENT =====
const state = {
	isSearching: false,
	currentQuery: '',
	autocompleteTimer: null,
};

// ===== DOM ELEMENTS =====
const elements = {
	searchForm: null,
	searchInput: null,
	prefixCheckbox: null,
	filenameCheckbox: null,
	suggestionsContainer: null,
	resultsSection: null,
	resultsGrid: null,
	uploadForm: null,
};

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', () => {
	initializeElements();
	setupEventListeners();
	setupScrollEffects();
	console.log('Campus Search Engine initialized');
});

/**
 * Initialize DOM element references
 */
function initializeElements() {
	elements.searchInput = document.getElementById('query');
	elements.suggestionsContainer = document.getElementById('suggestions');
	elements.resultsSection = document.getElementById('results-section');
	elements.searchForm = document.querySelector('#search-section form');
	elements.prefixCheckbox = document.querySelector('input[name="prefix"]');
	elements.filenameCheckbox = document.querySelector('input[name="filename"]');
	elements.uploadForm = document.querySelector('#upload-section form');
	elements.resultsGrid = document.querySelector('.results-grid');
}

// ===== EVENT LISTENERS =====
function setupEventListeners() {
	// Autocomplete on search input
	if (elements.searchInput) {
		elements.searchInput.addEventListener('input', handleSearchInput);
		elements.searchInput.addEventListener('keydown', handleKeyNavigation);
	}

	// Click handler for autocomplete suggestions
	if (elements.suggestionsContainer) {
		elements.suggestionsContainer.addEventListener('click', handleSuggestionClick);
	}

	// Close suggestions when clicking outside
	document.addEventListener('click', (event) => {
		if (!event.target.closest('.autocomplete')) {
			clearSuggestions();
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

	const isPrefixSearch = elements.prefixCheckbox?.checked || false;
	const isFilenameSearch = elements.filenameCheckbox?.checked || false;

	showLoadingIndicator();
	clearSuggestions();

	try {
		const results = await performSearch(query, isPrefixSearch, isFilenameSearch);
		renderResults(results);
		scrollToResults();
	} catch (error) {
		console.error('Search error:', error);
		showNotification('Search failed. Please try again.', 'error');
	} finally {
		hideLoadingIndicator();
	}
}

/**
 * Perform search request to backend
 */
async function performSearch(query, prefix, filename) {
	const params = new URLSearchParams({
		q: query,
		prefix: prefix ? '1' : '0',
		filename: filename ? '1' : '0',
	});

	const response = await fetch(`/search?${params.toString()}`);
	
	if (!response.ok) {
		throw new Error('Search request failed');
	}

	// Since the backend returns HTML, we need to parse it
	// For a pure AJAX solution, we'd need a JSON endpoint
	// For now, we'll reload the page which is what the form does anyway
	window.location.href = `/search?${params.toString()}`;
	
	// Return empty array since we're redirecting
	return [];
}

/**
 * Render search results dynamically
 */
function renderResults(results) {
	if (!elements.resultsGrid) return;

	if (!results || results.length === 0) {
		elements.resultsGrid.innerHTML = `
			<div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: #718096;">
				<p style="font-size: 1.2rem; margin-bottom: 0.5rem;">📭 No results found</p>
				<p>Try uploading documents or refining your search query.</p>
			</div>
		`;
		return;
	}

	elements.resultsGrid.innerHTML = results
		.map(result => createResultCard(result))
		.join('');

	// Add fade-in animation
	const cards = elements.resultsGrid.querySelectorAll('.result-card');
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
function createResultCard(result) {
	const title = escapeHtml(result.title || 'Untitled');
	const snippet = escapeHtml(result.snippet || 'No preview available.');
	const filename = escapeHtml(result.filename || '');
	const score = result.score || 0;

	return `
		<div class="result-card">
			<div class="result-title">${title}</div>
			<div class="result-snippet">${snippet}</div>
			<div class="result-meta">
				<small>📁 ${filename}</small>
				<span class="badge">Score: ${score}</span>
			</div>
			<div class="result-actions">
				<a href="/files/${encodeURIComponent(filename)}" target="_blank">Open</a>
				<a href="/files/${encodeURIComponent(filename)}?download=1">Download</a>
			</div>
		</div>
	`;
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

	// Add loading class to results section
	if (elements.resultsSection) {
		elements.resultsSection.classList.add('loading');
	}

	// Disable search button
	const searchButton = elements.searchForm?.querySelector('button[type="submit"]');
	if (searchButton) {
		searchButton.disabled = true;
		searchButton.innerHTML = '⏳ Searching...';
	}

	// Show spinner in results area
	if (elements.resultsGrid) {
		elements.resultsGrid.innerHTML = `
			<div style="grid-column: 1/-1; text-align: center; padding: 3rem;">
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

	// Remove loading class
	if (elements.resultsSection) {
		elements.resultsSection.classList.remove('loading');
	}

	// Enable search button
	const searchButton = elements.searchForm?.querySelector('button[type="submit"]');
	if (searchButton) {
		searchButton.disabled = false;
		searchButton.innerHTML = 'Search Documents';
	}
}

// ===== SCROLL FUNCTIONALITY =====
/**
 * Smooth scroll to results section
 */
function scrollToResults() {
	if (elements.resultsSection) {
		elements.resultsSection.scrollIntoView({ 
			behavior: 'smooth',
			block: 'start'
		});
	}
}

/**
 * Scroll to search section (triggered by nav search icon)
 */
window.scrollToSearch = function() {
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
	// Ctrl/Cmd + K to focus search
	if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
		event.preventDefault();
		if (elements.searchInput) {
			elements.searchInput.focus();
			elements.searchInput.select();
		}
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
