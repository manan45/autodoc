// MkDocs Material inspired JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all features
    initThemeToggle();
    initMobileNavigation();
    initModuleExpansion();
    initSearch();
    initCopyCode();
    initScrollEffects();
    initNavigationToggle();
    initNavigationHighlight();
    console.log('📚 Documentation loaded successfully!');
});

/* Theme Toggle */
function initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    const html = document.documentElement;
    
    // Get saved theme or default to light
    const savedTheme = localStorage.getItem('theme') || 'light';
    html.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function(e) {
            e.preventDefault();
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
            
            // Add animation effect
            this.style.transform = 'rotate(360deg)';
            setTimeout(() => {
                this.style.transform = '';
            }, 300);
        });
    }
}

function updateThemeIcon(theme) {
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
        if (theme === 'dark') {
            themeIcon.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 8a4 4 0 0 0-4 4 4 4 0 0 0 4 4 4 4 0 0 0 4-4 4 4 0 0 0-4-4m0 10a6 6 0 0 1-6-6 6 6 0 0 1 6-6 6 6 0 0 1 6 6 6 6 0 0 1-6 6m8-9.31V4h-4.69L12 .69 8.69 4H4v4.69L.69 12 4 15.31V20h4.69L12 23.31 15.31 20H20v-4.69L23.31 12 20 8.69Z"/></svg>';
        } else {
            themeIcon.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M17.75 4.09L15.22 6.03L16.13 9.09L13.5 7.28L10.87 9.09L11.78 6.03L9.25 4.09L12.44 4L13.5 1L14.56 4L17.75 4.09M21.25 11L19.61 12.25L20.2 14.23L18.5 13.06L16.8 14.23L17.39 12.25L15.75 11L17.81 10.95L18.5 9L19.19 10.95L21.25 11M18.97 15.95C19.8 15.87 20.69 17.05 20.16 17.8C19.84 18.25 19.5 18.67 19.08 19.07C15.17 23 8.84 23 4.94 19.07C1.03 15.17 1.03 8.83 4.94 4.93C5.34 4.53 5.76 4.17 6.21 3.85C6.96 3.32 8.14 4.21 8.06 5.04C7.79 7.9 8.75 10.87 10.95 13.06C13.14 15.26 16.1 16.22 18.97 15.95M17.33 17.97C14.5 17.81 11.7 16.64 9.53 14.5C7.36 12.31 6.2 9.5 6.04 6.68C3.23 9.82 3.34 14.4 6.35 17.41C9.37 20.43 14 20.54 17.33 17.97Z"/></svg>';
        }
    }
}

/* Mobile Navigation */
function initMobileNavigation() {
    const drawerToggle = document.getElementById('__drawer');
    const searchToggle = document.getElementById('__search');
    const overlay = document.querySelector('.md-overlay');
    
    if (overlay) {
        overlay.addEventListener('click', function() {
            if (drawerToggle) drawerToggle.checked = false;
            if (searchToggle) searchToggle.checked = false;
        });
    }
    
    // Close drawer when clicking on navigation links on mobile
    document.querySelectorAll('.md-nav__link').forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 960) {
                if (drawerToggle) drawerToggle.checked = false;
            }
        });
    });
}

/* Module Expansion */
function initModuleExpansion() {
    document.querySelectorAll('.module-item').forEach(moduleItem => {
        moduleItem.addEventListener('click', function(e) {
            // Don't expand if clicking on links inside
            if (e.target.tagName === 'A' || e.target.closest('a')) {
                return;
            }
            
            e.stopPropagation();
            
            // Add visual feedback
            this.style.transform = 'scale(0.99)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
            
            // Toggle expanded state
            const wasExpanded = this.classList.contains('expanded');
            this.classList.toggle('expanded');
            
            // Handle module details
            const details = this.querySelector('.module-details');
            const expandIcon = this.querySelector('.expand-icon');
            
            if (details) {
                if (wasExpanded) {
                    details.classList.remove('expanded');
                    setTimeout(() => {
                        details.style.display = 'none';
                    }, 250);
                } else {
                    details.style.display = 'block';
                    setTimeout(() => {
                        details.classList.add('expanded');
                    }, 10);
                }
            }
            
            // Animate expand icon
            if (expandIcon) {
                expandIcon.textContent = wasExpanded ? 'expand_more' : 'expand_less';
                expandIcon.style.transform = wasExpanded ? 'rotate(0deg)' : 'rotate(180deg)';
            }
            
            // Smooth scroll to module if expanding
            if (!wasExpanded) {
                setTimeout(() => {
                    const rect = this.getBoundingClientRect();
                    if (rect.top < 100) {
                        this.scrollIntoView({ 
                            behavior: 'smooth', 
                            block: 'start',
                            inline: 'nearest' 
                        });
                    }
                }, 300);
            }
        });
        
        // Keyboard support
        moduleItem.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    });
}

/* Search Functionality */
function initSearch() {
    // Local module search
    const moduleSearchInput = document.getElementById('module-search');
    if (moduleSearchInput) {
        let searchTimeout;
        
        moduleSearchInput.addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase().trim();
            
            // Debounce search
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                filterModules(query);
            }, 150);
        });
        
        // Clear search on escape
        moduleSearchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                filterModules('');
                this.blur();
            }
        });
    }
    
    // Global search functionality
    const globalSearchInput = document.querySelector('.md-search__input');
    const searchButton = document.querySelector('.md-search__button');
    const searchToggle = document.getElementById('__search');
    
    if (searchButton && searchToggle) {
        searchButton.addEventListener('click', function() {
            searchToggle.checked = !searchToggle.checked;
            if (searchToggle.checked && globalSearchInput) {
                setTimeout(() => globalSearchInput.focus(), 100);
            }
        });
    }
    
    if (globalSearchInput) {
        globalSearchInput.addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase().trim();
            performGlobalSearch(query);
        });
        
        globalSearchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                if (searchToggle) searchToggle.checked = false;
            }
        });
    }
}

function filterModules(query) {
    const modules = document.querySelectorAll('.module-item');
    let visibleCount = 0;
    
    modules.forEach(module => {
        const title = module.querySelector('h4').textContent.toLowerCase();
        const docstring = module.querySelector('.docstring');
        const docText = docstring ? docstring.textContent.toLowerCase() : '';
        const path = module.querySelector('code').textContent.toLowerCase();
        
        const matches = !query || 
                       title.includes(query) || 
                       docText.includes(query) || 
                       path.includes(query);
        
        if (matches) {
            module.style.display = '';
            module.style.opacity = '1';
            visibleCount++;
        } else {
            module.style.display = 'none';
            module.style.opacity = '0.5';
        }
    });
    
    // Show/hide no results message
    let noResultsMsg = document.querySelector('.no-results-message');
    if (query && visibleCount === 0) {
        if (!noResultsMsg) {
            noResultsMsg = document.createElement('div');
            noResultsMsg.className = 'no-results-message md-admonition md-admonition--info';
            noResultsMsg.innerHTML = `
                <p class="md-admonition__title">🔍 No Results</p>
                <p>No modules found matching "<strong>${query}</strong>". Try adjusting your search terms.</p>
            `;
            document.querySelector('.module-list').appendChild(noResultsMsg);
        }
        noResultsMsg.style.display = 'block';
    } else if (noResultsMsg) {
        noResultsMsg.style.display = 'none';
    }
}

function performGlobalSearch(query) {
    if (!query) {
        document.getElementById('search-results').innerHTML = '';
        return;
    }
    
    // Simple client-side search across current page content
    const results = [];
    const content = document.querySelector('.md-content__inner');
    
    if (content) {
        const textNodes = getTextNodes(content);
        textNodes.forEach(node => {
            if (node.textContent.toLowerCase().includes(query)) {
                const parent = node.parentElement;
                if (parent && !results.find(r => r.element === parent)) {
                    results.push({
                        element: parent,
                        text: truncateText(node.textContent, query, 100),
                        title: getElementTitle(parent)
                    });
                }
            }
        });
    }
    
    displaySearchResults(results, query);
}

function getTextNodes(element) {
    const textNodes = [];
    const walker = document.createTreeWalker(
        element,
        NodeFilter.SHOW_TEXT,
        null,
        false
    );
    
    let node;
    while (node = walker.nextNode()) {
        if (node.textContent.trim().length > 0) {
            textNodes.push(node);
        }
    }
    
    return textNodes;
}

function getElementTitle(element) {
    const heading = element.closest('section')?.querySelector('h1, h2, h3, h4, h5, h6') ||
                   element.querySelector('h1, h2, h3, h4, h5, h6') ||
                   document.querySelector('h1');
    return heading ? heading.textContent : 'Documentation';
}

function truncateText(text, query, length) {
    const index = text.toLowerCase().indexOf(query.toLowerCase());
    if (index === -1) return text.substring(0, length) + '...';
    
    const start = Math.max(0, index - length / 2);
    const end = Math.min(text.length, start + length);
    
    return (start > 0 ? '...' : '') + 
           text.substring(start, end) + 
           (end < text.length ? '...' : '');
}

function displaySearchResults(results, query) {
    const searchResults = document.getElementById('search-results');
    if (!searchResults) return;
    
    if (results.length === 0) {
        searchResults.innerHTML = `
            <div class="md-search-result__meta">
                No results for "<strong>${query}</strong>"
            </div>
        `;
        return;
    }
    
    const resultsHTML = results.map(result => `
        <div class="md-search-result__item">
            <h3 class="md-search-result__title">${result.title}</h3>
            <p class="md-search-result__text">${highlightQuery(result.text, query)}</p>
        </div>
    `).join('');
    
    searchResults.innerHTML = `
        <div class="md-search-result__meta">
            ${results.length} result${results.length === 1 ? '' : 's'} for "<strong>${query}</strong>"
        </div>
        ${resultsHTML}
    `;
}

function highlightQuery(text, query) {
    const regex = new RegExp(`(${query})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

/* Copy Code Functionality */
function initCopyCode() {
    document.querySelectorAll('pre code').forEach(block => {
        const button = document.createElement('button');
        button.className = 'md-clipboard md-icon';
        button.title = 'Copy to clipboard';
        button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M19 21H8V7h11m0-2H8a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2m-3-4H4a2 2 0 0 0-2 2v14h2V3h12V1Z"/></svg>';
        
        button.addEventListener('click', async function(e) {
            e.stopPropagation();
            
            try {
                await navigator.clipboard.writeText(block.textContent);
                this.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M21 7L9 19l-5.5-5.5 1.41-1.41L9 16.17 19.59 5.59 21 7Z"/></svg>';
                this.style.color = 'var(--md-accent-fg-color)';
                
                setTimeout(() => {
                    this.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M19 21H8V7h11m0-2H8a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2m-3-4H4a2 2 0 0 0-2 2v14h2V3h12V1Z"/></svg>';
                    this.style.color = '';
                }, 2000);
            } catch (err) {
                console.error('Failed to copy code:', err);
            }
        });
        
        const pre = block.closest('pre');
        if (pre && !pre.querySelector('.md-clipboard')) {
            pre.style.position = 'relative';
            pre.appendChild(button);
        }
    });
}

/* Scroll Effects */
function initScrollEffects() {
    // Add scroll-to-top functionality
    const scrollBtn = createScrollToTopButton();
    let ticking = false;
    
    function updateScrollState() {
        const scrolled = window.pageYOffset > 100;
        scrollBtn.classList.toggle('md-top--visible', scrolled);
        ticking = false;
    }
    
    window.addEventListener('scroll', function() {
        if (!ticking) {
            requestAnimationFrame(updateScrollState);
            ticking = true;
        }
    });
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

function createScrollToTopButton() {
    const button = document.createElement('button');
    button.className = 'md-top';
    button.title = 'Back to top';
    button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M13 20h-2V8l-5.5 5.5-1.42-1.42L12 4.16l7.92 7.92-1.42 1.42L13 8v12Z"/></svg>';
    
    // Styles
    Object.assign(button.style, {
        position: 'fixed',
        bottom: '1rem',
        right: '1rem',
        zIndex: '2',
        width: '2.5rem',
        height: '2.5rem',
        padding: '0',
        color: 'var(--md-primary-bg-color)',
        backgroundColor: 'var(--md-accent-fg-color)',
        border: '0',
        borderRadius: '50%',
        boxShadow: 'var(--md-shadow-z2)',
        cursor: 'pointer',
        transform: 'scale(0)',
        transition: 'transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.25s',
        opacity: '0'
    });
    
    button.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    button.addEventListener('mouseenter', function() {
        this.style.transform = this.classList.contains('md-top--visible') ? 'scale(1.1)' : 'scale(0)';
    });
    
    button.addEventListener('mouseleave', function() {
        this.style.transform = this.classList.contains('md-top--visible') ? 'scale(1)' : 'scale(0)';
    });
    
    document.body.appendChild(button);
    return button;
}

// Utility function to add visible class to scroll-to-top button
document.addEventListener('DOMContentLoaded', function() {
    const style = document.createElement('style');
    style.textContent = `
        .md-top--visible {
            transform: scale(1) !important;
            opacity: 1 !important;
        }
        
        .md-clipboard {
            position: absolute !important;
            top: 0.5rem !important;
            right: 0.5rem !important;
            width: 1.5rem !important;
            height: 1.5rem !important;
            padding: 0 !important;
            color: var(--md-default-fg-color--light) !important;
            background: transparent !important;
            border: 0 !important;
            border-radius: 0.1rem !important;
            cursor: pointer !important;
            transition: color var(--md-transition-duration) !important;
            opacity: 0.7 !important;
        }
        
        .md-clipboard:hover {
            opacity: 1 !important;
            color: var(--md-accent-fg-color) !important;
        }
        
        .md-clipboard svg {
            width: 100% !important;
            height: 100% !important;
            fill: currentColor !important;
        }
        
        @media (max-width: 60em) {
            .md-clipboard {
                display: none !important;
            }
        }
    `;
    document.head.appendChild(style);
});

// Enhanced keyboard navigation
document.addEventListener('keydown', function(e) {
    // Escape key handling
    if (e.key === 'Escape') {
        const searchToggle = document.getElementById('__search');
        const drawerToggle = document.getElementById('__drawer');
        
        if (searchToggle && searchToggle.checked) {
            searchToggle.checked = false;
        } else if (drawerToggle && drawerToggle.checked) {
            drawerToggle.checked = false;
        }
    }
    
    // Search shortcut (Ctrl/Cmd + K)
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchToggle = document.getElementById('__search');
        const searchInput = document.querySelector('.md-search__input');
        
        if (searchToggle && searchInput) {
            searchToggle.checked = true;
            setTimeout(() => searchInput.focus(), 100);
        }
    }
});

/* Enhanced Navigation Functions */
function initNavigationToggle() {
    // Handle collapsible navigation sections
    const navToggles = document.querySelectorAll('.md-nav__toggle');
    
    navToggles.forEach(toggle => {
        const targetId = toggle.getAttribute('data-md-toggle');
        const targetNav = toggle.nextElementSibling?.nextElementSibling;
        
        // Auto-expand current section
        const isCurrentSection = toggle.checked;
        if (isCurrentSection && targetNav) {
            targetNav.style.maxHeight = targetNav.scrollHeight + 'px';
        }
        
        toggle.addEventListener('change', function() {
            if (targetNav) {
                if (this.checked) {
                    // Expand
                    targetNav.style.maxHeight = targetNav.scrollHeight + 'px';
                    targetNav.style.opacity = '1';
                } else {
                    // Collapse
                    targetNav.style.maxHeight = '0';
                    targetNav.style.opacity = '0';
                }
            }
        });
    });
}

function initNavigationHighlight() {
    // Highlight current page in navigation
    const currentPath = window.location.pathname.split('/').pop() || 'index.html';
    const navLinks = document.querySelectorAll('.md-nav__link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && href.includes(currentPath)) {
            link.classList.add('md-nav__link--active');
            
            // Auto-expand parent section if nested
            const parentSection = link.closest('.md-nav[data-md-level="1"]');
            if (parentSection) {
                const parentToggle = parentSection.previousElementSibling?.previousElementSibling;
                if (parentToggle && parentToggle.type === 'checkbox') {
                    parentToggle.checked = true;
                    parentSection.style.maxHeight = parentSection.scrollHeight + 'px';
                }
            }
        }
    });
}

function initSidebarStats() {
    // Animate stats numbers on load
    const statsNumbers = document.querySelectorAll('.md-nav__stats-number');
    
    statsNumbers.forEach(stat => {
        const finalValue = parseInt(stat.textContent);
        let currentValue = 0;
        const increment = Math.ceil(finalValue / 30);
        
        const counter = setInterval(() => {
            currentValue += increment;
            if (currentValue >= finalValue) {
                currentValue = finalValue;
                clearInterval(counter);
            }
            stat.textContent = currentValue;
        }, 50);
    });
}