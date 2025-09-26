/* app.js - Main application JavaScript module */

// Prevent transitions on initial page load
document.documentElement.classList.add('no-transition');
window.addEventListener('load', () => {
    document.documentElement.classList.remove('no-transition');
});

// ===== Application Modules ===== //

/**
 * Theme Manager Module
 * Handles theme toggling and persistence
 */
const ThemeManager = (() => {
    const STORAGE_KEY = 'theme-preference';
    const DEFAULT_THEME = 'light';
    
    const init = () => {
        const savedTheme = localStorage.getItem(STORAGE_KEY) || DEFAULT_THEME;
        setTheme(savedTheme);
        
        // Bind theme toggle buttons
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', toggleTheme);
        }
        
        // Listen for system theme changes
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addEventListener('change', handleSystemThemeChange);
    };
    
    const setTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(STORAGE_KEY, theme);
        updateThemeIcon(theme);
    };
    
    const getTheme = () => {
        return document.documentElement.getAttribute('data-theme') || DEFAULT_THEME;
    };
    
    const toggleTheme = () => {
        const currentTheme = getTheme();
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    };
    
    const updateThemeIcon = (theme) => {
        const themeIcon = document.getElementById('theme-icon');
        if (themeIcon) {
            themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
        }
    };
    
    const handleSystemThemeChange = (e) => {
        if (!localStorage.getItem(STORAGE_KEY)) {
            setTheme(e.matches ? 'dark' : 'light');
        }
    };
    
    return {
        init,
        setTheme,
        getTheme,
        toggleTheme
    };
})();

/**
 * Navigation Manager Module
 * Handles mobile navigation and sidebar toggling
 */
const NavigationManager = (() => {
    let isOpen = false;
    
    const init = () => {
        bindMenuToggle();
        bindOverlayClick();
        bindEscapeKey();
        bindNavigationLinks();
        bindSectionToggles();
        handleResize();
        
        window.addEventListener('resize', handleResize);
    };
    
    const bindMenuToggle = () => {
        const menuBtn = document.querySelector('.header__menu-btn');
        const drawerToggle = document.getElementById('__drawer');
        
        if (menuBtn) {
            menuBtn.addEventListener('click', toggleSidebar);
        }
        
        if (drawerToggle) {
            drawerToggle.addEventListener('change', (e) => {
                if (e.target.checked) {
                    openSidebar();
                } else {
                    closeSidebar();
                }
            });
        }
    };
    
    const bindOverlayClick = () => {
        const overlay = document.querySelector('.overlay');
        if (overlay) {
            overlay.addEventListener('click', closeSidebar);
        }
    };
    
    const bindEscapeKey = () => {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && isOpen) {
                closeSidebar();
            }
        });
    };
    
    const toggleSidebar = () => {
        if (isOpen) {
            closeSidebar();
        } else {
            openSidebar();
        }
    };
    
    const openSidebar = () => {
        const sidebar = document.querySelector('.sidebar');
        const overlay = document.querySelector('.overlay');
        const drawerToggle = document.getElementById('__drawer');
        
        if (sidebar) sidebar.classList.add('sidebar--open');
        if (overlay) overlay.classList.add('overlay--visible');
        if (drawerToggle) drawerToggle.checked = true;
        
        document.body.style.overflow = 'hidden';
        isOpen = true;
    };
    
    const closeSidebar = () => {
        const sidebar = document.querySelector('.sidebar');
        const overlay = document.querySelector('.overlay');
        const drawerToggle = document.getElementById('__drawer');
        
        if (sidebar) sidebar.classList.remove('sidebar--open');
        if (overlay) overlay.classList.remove('overlay--visible');
        if (drawerToggle) drawerToggle.checked = false;
        
        document.body.style.overflow = '';
        isOpen = false;
    };
    
    const bindNavigationLinks = () => {
        const navLinks = document.querySelectorAll('.md-nav__link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                // Handle active state
                const currentActive = document.querySelector('.md-nav__link--active');
                if (currentActive && currentActive !== link) {
                    currentActive.classList.remove('md-nav__link--active');
                }
                
                // Don't add active class to section headers or hash links
                if (!link.closest('.md-nav__item--section') && !link.getAttribute('href').startsWith('#')) {
                    link.classList.add('md-nav__link--active');
                }
                
                // Close mobile menu if open
                if (window.innerWidth < 768 && isOpen) {
                    closeSidebar();
                }
            });
        });
    };
    
    const bindSectionToggles = () => {
        const sectionToggles = document.querySelectorAll('.md-nav__item--section .md-nav__link');
        sectionToggles.forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                // Only handle clicks on section headers, not sub-links
                if (toggle.classList.contains('md-nav__link--index')) {
                    e.preventDefault();
                    const checkbox = toggle.closest('.md-nav__item--section').querySelector('.md-nav__toggle');
                    if (checkbox) {
                        checkbox.checked = !checkbox.checked;
                        
                        // Animate the arrow
                        const arrow = toggle.querySelector('.md-nav__icon--expand');
                        if (arrow) {
                            arrow.style.transform = checkbox.checked ? 'rotate(90deg)' : 'rotate(0deg)';
                        }
                    }
                }
            });
        });
    };

    const handleResize = () => {
        if (window.innerWidth >= 768 && isOpen) {
            closeSidebar();
        }
    };
    
    return {
        init,
        openSidebar,
        closeSidebar,
        toggleSidebar
    };
})();

/**
 * Search Manager Module
 * Handles search functionality and modal
 */
const SearchManager = (() => {
    let searchData = [];
    let isOpen = false;
    
    const init = () => {
        bindSearchButtons();
        bindSearchModal();
        bindKeyboardShortcuts();
        loadSearchData();
    };
    
    const bindSearchButtons = () => {
        const searchButtons = document.querySelectorAll('[data-md-search-button]');
        searchButtons.forEach(btn => {
            btn.addEventListener('click', openSearch);
        });
    };
    
    const bindSearchModal = () => {
        const modal = document.querySelector('.search-modal');
        const input = document.querySelector('.search-modal__input');
        
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    closeSearch();
                }
            });
        }
        
        if (input) {
            input.addEventListener('input', handleSearchInput);
            input.addEventListener('keydown', handleSearchKeydown);
        }
    };
    
    const bindKeyboardShortcuts = () => {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K to open search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                openSearch();
            }
            
            // Escape to close search
            if (e.key === 'Escape' && isOpen) {
                closeSearch();
            }
        });
    };
    
    const openSearch = () => {
        const modal = document.querySelector('.search-modal');
        const input = document.querySelector('.search-modal__input');
        
        if (modal) {
            modal.showModal();
            isOpen = true;
        }
        
        if (input) {
            input.focus();
        }
        
        document.body.style.overflow = 'hidden';
    };
    
    const closeSearch = () => {
        const modal = document.querySelector('.search-modal');
        
        if (modal) {
            modal.close();
            isOpen = false;
        }
        
        document.body.style.overflow = '';
    };
    
    const handleSearchInput = (e) => {
        const query = e.target.value.trim();
        if (query.length > 0) {
            performSearch(query);
        } else {
            clearResults();
        }
    };
    
    const handleSearchKeydown = (e) => {
        const results = Array.from(document.querySelectorAll('.search-result'));
        if (results.length === 0) return;
        const currentIndex = results.findIndex(el => el.classList.contains('is-active'));

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            const nextIndex = currentIndex < 0 ? 0 : Math.min(currentIndex + 1, results.length - 1);
            results.forEach(el => el.classList.remove('is-active'));
            results[nextIndex].classList.add('is-active');
            results[nextIndex].scrollIntoView({ block: 'nearest' });
        }

        if (e.key === 'ArrowUp') {
            e.preventDefault();
            const prevIndex = currentIndex <= 0 ? 0 : currentIndex - 1;
            results.forEach(el => el.classList.remove('is-active'));
            results[prevIndex].classList.add('is-active');
            results[prevIndex].scrollIntoView({ block: 'nearest' });
        }

        if (e.key === 'Enter') {
            const active = results[currentIndex >= 0 ? currentIndex : 0];
            if (active) active.click();
        }
    };
    
    const performSearch = async (query) => {
        try {
            // Try API search first
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=10`);
            if (response.ok) {
                const data = await response.json();
                const apiResults = data.results?.map(module => ({
                    title: module.name,
                    content: module.description || 'No description available',
                    url: `#module-${module.id}`,
                    path: module.path,
                    type: module.type,
                    complexity: module.complexity
                })) || [];
                displayResults(apiResults);
                return;
            }
        } catch (error) {
            console.error('API search failed:', error);
            displayResults([{
                title: 'Search Error',
                content: `Search functionality is unavailable: ${error.message}`,
                url: '',
                type: 'error'
            }]);
            return;
        }
        
        // If no search data available, show error
        if (!searchData || searchData.length === 0) {
            displayResults([{
                title: 'No Search Index',
                content: 'Search index not available. Generate documentation first.',
                url: '',
                type: 'error'
            }]);
            return;
        }
        
        // Local search
        const results = searchData.filter(item => 
            item.title.toLowerCase().includes(query.toLowerCase()) ||
            item.content.toLowerCase().includes(query.toLowerCase())
        ).slice(0, 10);
        
        displayResults(results);
    };
    
    const displayResults = (results) => {
        const container = document.querySelector('.search-modal__results');
        if (!container) return;
        
        container.innerHTML = '';
        
        if (results.length === 0) {
            container.innerHTML = `
                <div class="search-modal__empty">
                    <div class="search-modal__empty-icon">🔍</div>
                    <p>No results found</p>
                    <small>Try different keywords or check your spelling</small>
                </div>
            `;
            return;
        }
        
        results.forEach((result, index) => {
            const resultElement = document.createElement('div');
            resultElement.className = 'search-result';
            resultElement.innerHTML = `
                <div class="search-result__title">${result.title}</div>
                <div class="search-result__description">${result.content}</div>
                ${result.path ? `<div class="search-result__path">${result.path}</div>` : ''}
                ${result.type ? `<span class="search-result__type">${result.type.toUpperCase()}</span>` : ''}
                ${result.complexity ? `<span class="search-result__complexity complexity-${result.complexity}">${result.complexity.toUpperCase()}</span>` : ''}
            `;
            
            resultElement.addEventListener('click', () => {
                if (result.url) {
                    window.location.href = result.url;
                } else if (result.path) {
                    // Navigate to module
                    window.RepositoryDataManager?.navigateToModule(result.path);
                }
                closeSearch();
            });

            resultElement.addEventListener('mouseenter', () => {
                document.querySelectorAll('.search-result.is-active').forEach(el => el.classList.remove('is-active'));
                resultElement.classList.add('is-active');
            });
            
            container.appendChild(resultElement);
        });
    };
    
    const clearResults = () => {
        const container = document.querySelector('.search-modal__results');
        if (container) {
            container.innerHTML = '';
        }
    };
    
    const loadSearchData = async () => {
        try {
            const response = await fetch('/search/search_index.json');
            if (response.ok) {
                searchData = await response.json();
            }
        } catch (error) {
            console.error('Failed to load search data:', error);
            // Show error to user instead of silently failing
            const searchModal = document.querySelector('.search-modal__results');
            if (searchModal) {
                searchModal.innerHTML = `
                    <div class="search-modal__empty">
                        <div class="search-modal__empty-icon">❌</div>
                        <p>Search unavailable</p>
                        <small>Error: ${error.message}</small>
                    </div>
                `;
            }
        }
    };
    
    return {
        init,
        openSearch,
        closeSearch
    };
})();

/**
 * Table of Contents Manager Module
 * Handles TOC highlighting and smooth scrolling
 */
const TOCManager = (() => {
    let headings = [];
    let tocLinks = [];
    
    const init = () => {
        tocElement = document.querySelector('.md-nav--secondary, .toc');
        if (!tocElement) {
            console.log('📋 No TOC found');
            return;
        }
        
        findHeadings();
        bindTOCLinks();
        bindScrollSpy();
        setupAutoHide();
        
        if (headings.length > 0) {
            updateActiveLink();
        }
        
        console.log('📋 TOC Manager initialized with auto-hide');
    };
    
    const setupAutoHide = () => {
        // Add auto-hide class to TOC
        tocElement.classList.add('toc-auto-hide');
        
        // Add toggle button
        addToggleButton();
        
        // Bind hover events
        bindHoverEvents();
    };
    
    const addToggleButton = () => {
        const existing = document.querySelector('.toc-toggle-btn');
        if (existing) return;
        
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'toc-toggle-btn';
        toggleBtn.innerHTML = '📋';
        toggleBtn.title = 'Toggle Table of Contents';
        toggleBtn.setAttribute('aria-label', 'Toggle Table of Contents');
        
        toggleBtn.addEventListener('click', toggleTOC);
        
        // Insert before TOC or append to sidebar
        const sidebar = tocElement.closest('.md-sidebar--secondary');
        if (sidebar) {
            sidebar.appendChild(toggleBtn);
        }
    };
    
    const bindHoverEvents = () => {
        const tocContainer = tocElement.closest('.md-sidebar--secondary');
        if (!tocContainer) return;
        
        tocContainer.addEventListener('mouseenter', () => {
            clearTimeout(autoHideTimer);
            showTOC();
        });
        
        tocContainer.addEventListener('mouseleave', () => {
            autoHideTimer = setTimeout(() => {
                if (window.scrollY > 300) {
                    hideTOC();
                }
            }, 2000);
        });
    };
    
    const findHeadings = () => {
        headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'))
            .filter(h => h.id)
            .map(h => ({
                element: h,
                id: h.id,
                offsetTop: h.offsetTop
            }));
    };
    
    const bindTOCLinks = () => {
        tocLinks = Array.from(document.querySelectorAll('.toc__link'));
        tocLinks.forEach(link => {
            link.addEventListener('click', handleTOCClick);
        });
    };
    
    const bindScrollSpy = () => {
        let ticking = false;
        
        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(() => {
                    updateActiveLink();
                    handleAutoHide();
                    ticking = false;
                });
                ticking = true;
            }
        });
    };
    
    let lastScrollY = 0;
    let isVisible = false;
    
    const handleAutoHide = () => {
        if (!tocElement) return;
        
        const currentScrollY = window.scrollY;
        const scrollDirection = currentScrollY > lastScrollY ? 'down' : 'up';
        
        // Auto-hide logic
        if (scrollDirection === 'down' && currentScrollY > 300) {
            hideTOC();
        } else if (scrollDirection === 'up') {
            showTOC();
        }
        
        lastScrollY = currentScrollY;
    };
    
    const showTOC = () => {
        if (!tocElement || isVisible) return;
        
        tocElement.style.transform = 'translateX(0)';
        tocElement.style.opacity = '1';
        isVisible = true;
        
        const toggleBtn = document.querySelector('.toc-toggle-btn');
        if (toggleBtn) {
            toggleBtn.style.transform = 'translateX(0)';
        }
    };
    
    const hideTOC = () => {
        if (!tocElement || !isVisible) return;
        
        tocElement.style.transform = 'translateX(100%)';
        tocElement.style.opacity = '0.3';
        isVisible = false;
        
        const toggleBtn = document.querySelector('.toc-toggle-btn');
        if (toggleBtn) {
            toggleBtn.style.transform = 'translateX(-40px)';
        }
    };
    
    const toggleTOC = () => {
        if (isVisible) {
            hideTOC();
        } else {
            showTOC();
        }
    };
    
    const handleTOCClick = (e) => {
        e.preventDefault();
        const href = e.target.getAttribute('href');
        const targetId = href.substring(1);
        const targetElement = document.getElementById(targetId);
        
        if (targetElement) {
            targetElement.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    };
    
    const updateActiveLink = () => {
        const scrollTop = window.pageYOffset;
        const windowHeight = window.innerHeight;
        
        let activeId = null;
        
        // Find the current heading
        for (let i = headings.length - 1; i >= 0; i--) {
            const heading = headings[i];
            if (scrollTop >= heading.offsetTop - 100) {
                activeId = heading.id;
                break;
            }
        }
        
        // Update TOC links
        tocLinks.forEach(link => {
            const href = link.getAttribute('href');
            const isActive = href === `#${activeId}`;
            
            link.classList.toggle('toc__link--active', isActive);
        });
    };
    
    return {
        init
    };
})();

/**
 * Copy to Clipboard Manager
 * Handles code block copy functionality
 */
const ClipboardManager = (() => {
    const init = () => {
        bindCopyButtons();
    };
    
    const bindCopyButtons = () => {
        const copyButtons = document.querySelectorAll('.code-block__copy');
        copyButtons.forEach(btn => {
            btn.addEventListener('click', handleCopyClick);
        });
    };
    
    const handleCopyClick = async (e) => {
        const button = e.currentTarget;
        const codeBlock = button.closest('.code-block');
        const code = codeBlock.querySelector('pre code') || codeBlock.querySelector('pre');
        
        if (!code) return;
        
        try {
            await navigator.clipboard.writeText(code.textContent);
            showCopyFeedback(button);
        } catch (error) {
            console.error('Failed to copy code:', error);
        }
    };
    
    const showCopyFeedback = (button) => {
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        button.classList.add('copied');
        
        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('copied');
        }, 2000);
    };
    
    return {
        init
    };
})();

// ===== Application Initialization ===== //

/**
 * Initialize all application modules when DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();
    NavigationManager.init();
    SearchManager.init();
    TOCManager.init();
    ClipboardManager.init();
    
    // Add any additional initialization here
    console.log('📚 Documentation app initialized');
});

// Export modules for external use if needed
window.DocApp = {
    ThemeManager,
    NavigationManager,
    SearchManager,
    TOCManager,
    ClipboardManager
};
