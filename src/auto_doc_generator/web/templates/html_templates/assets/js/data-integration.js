/* data-integration.js - Legacy repository data integration (DEPRECATED) */
// NOTE: This file is being phased out in favor of modular architecture
// New functionality should be added to the respective modules:
// - core-data-manager.js - Data loading and vector operations
// - statistics-manager.js - Statistics calculations
// - module-renderer.js - Module UI components  
// - architecture-diagrams.js - Diagram generation

/**
 * @deprecated Use RepositoryDataManager from core-data-manager.js instead
 * Legacy Repository Data Manager for backward compatibility
 */
const LegacyRepositoryDataManager = (() => {
    let repositoryData = {};
    let vectorIndex = null;

    const init = async () => {
        console.warn('⚠️ Using deprecated data-integration.js - consider migrating to modular architecture');
        try {
            await loadRepositoryData();
            await buildVectorIndex();
            bindModuleInteractions();
            console.log('📊 Legacy repository data integration initialized');
        } catch (error) {
            console.warn('Repository data integration failed:', error);
        }
    };
    
    const loadRepositoryData = async () => {
        try {
            // Try to load repository analysis data
            const response = await fetch('/api/repository-data');
            repositoryData = await response.json();
            console.log('📁 Repository data loaded:', repositoryData.modules?.length || 0, 'modules');
            
            // Trigger event for new modular system
            document.dispatchEvent(new CustomEvent('repositoryDataLoaded', { 
                detail: repositoryData 
            }));
            
        } catch (error) {
            console.warn('Failed to load repository data, using fallback:', error);
            repositoryData = { modules: [], totalFiles: 0, totalFunctions: 0, totalClasses: 0 };
        }
    };
    
    
    const generateSimpleEmbedding = (text) => {
        // Simple text-to-vector embedding (in production, use proper embeddings)
        const words = text.toLowerCase().split(/\W+/).filter(w => w.length > 2);
        const embedding = new Array(50).fill(0);
        
        words.forEach((word, index) => {
            const hash = simpleHash(word);
            embedding[hash % 50] += 1 / (index + 1);
        });
        
        // Normalize
        const magnitude = Math.sqrt(embedding.reduce((sum, val) => sum + val * val, 0));
        return embedding.map(val => magnitude > 0 ? val / magnitude : 0);
    };
    
    const simpleHash = (str) => {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return Math.abs(hash);
    };
    
    const buildVectorIndex = async () => {
        if (!repositoryData.modules) return;
        
        // Create a simple vector index for similarity search
        vectorIndex = {
            modules: repositoryData.modules,
            search: (query, limit = 5) => {
                const queryEmbedding = generateSimpleEmbedding(query);
                const similarities = repositoryData.modules.map(module => ({
                    module,
                    similarity: cosineSimilarity(queryEmbedding, module.embedding)
                }));
                
                return similarities
                    .sort((a, b) => b.similarity - a.similarity)
                    .slice(0, limit)
                    .map(item => item.module);
            }
        };
        
        console.log('🔍 Vector index built with', repositoryData.modules.length, 'modules');
    };
    
    const cosineSimilarity = (vecA, vecB) => {
        if (vecA.length !== vecB.length) return 0;
        
        let dotProduct = 0;
        let normA = 0;
        let normB = 0;
        
        for (let i = 0; i < vecA.length; i++) {
            dotProduct += vecA[i] * vecB[i];
            normA += vecA[i] * vecA[i];
            normB += vecB[i] * vecB[i];
        }
        
        const magnitude = Math.sqrt(normA) * Math.sqrt(normB);
        return magnitude > 0 ? dotProduct / magnitude : 0;
    };
    
    const bindModuleInteractions = () => {
        // Enhance module cards with repository data
        const moduleCards = document.querySelectorAll('.module-card, .getting-started-card');
        
        // If we have real repository data, replace the cards with actual modules
        if (repositoryData.modules && repositoryData.modules.length > 0) {
            replaceModuleCards(repositoryData.modules);
        } else {
            // Enhance existing cards with available data
            moduleCards.forEach((card, index) => {
                const module = repositoryData.modules?.[index];
                if (module) {
                    enhanceModuleCard(card, module);
                }
            });
        }
        
        // Add click handlers for navigation to code
        document.addEventListener('click', (e) => {
            const moduleLink = e.target.closest('[data-module-path]');
            if (moduleLink) {
                e.preventDefault();
                navigateToModule(moduleLink.dataset.modulePath);
            }
        });
    };
    
    const replaceModuleCards = (modules) => {
        const modulesContainer = document.querySelector('.stats-grid, .module-grid, .getting-started-grid');
        if (!modulesContainer) return;
        
        // Clear existing cards
        modulesContainer.innerHTML = '';
        
        // Create new cards from repository data
        modules
            .filter(m => (m.description || '').trim().length > 0)
            .slice(0, 12)
            .forEach(module => {
                const card = createModuleCard(module);
                modulesContainer.appendChild(card);
            });
        
        console.log(`🔄 Replaced module cards with ${modules.length} real modules`);
    };
    
    const createModuleCard = (module) => {
        if (!module || !(module.description || '').trim()) return document.createDocumentFragment();
        const card = document.createElement('div');
        card.className = 'module-card';
        card.setAttribute('data-module-path', module.path);
        card.setAttribute('data-module-type', module.type);
        card.setAttribute('data-complexity', module.complexity);
        
        card.innerHTML = `
            <div class="card-header">
                <h3>${module.name}</h3>
                <div class="complexity-indicator complexity-${module.complexity}">
                    ${module.complexity.toUpperCase()}
                </div>
            </div>
            <div class="card-content">
                <p class="module-description">${module.description}</p>
                <div class="module-path">
                    <code>${module.path}</code>
                </div>
                <div class="module-stats">
                    <div class="stat-item">
                        <span class="stat-value">${module.stats.functions || 0}</span>
                        <span class="stat-label">Functions</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">${module.stats.classes || 0}</span>
                        <span class="stat-label">Classes</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value">${module.stats.lines || 0}</span>
                        <span class="stat-label">Lines</span>
                    </div>
                </div>
            </div>
        `;
        
        // Hover tooltip disabled
        
        return card;
    };
    
    const enhanceModuleCard = (card, module) => {
        // Add module path data attribute
        card.setAttribute('data-module-path', module.path);
        card.setAttribute('data-module-type', module.type);
        card.setAttribute('data-complexity', module.complexity);
        
        // Add complexity indicator
        if (!card.querySelector('.complexity-indicator')) {
            const complexityBadge = document.createElement('div');
            complexityBadge.className = `complexity-indicator complexity-${module.complexity}`;
            complexityBadge.textContent = module.complexity.toUpperCase();
            complexityBadge.title = `Code complexity: ${module.complexity}`;
            
            const header = card.querySelector('h3, h4, .card__title');
            if (header) {
                header.appendChild(complexityBadge);
            }
        }

        // Add module type badge (CLASS/INTERFACE/MODEL/EMBEDDING/etc.)
        if (!card.querySelector('.module-type-badge')) {
            const typeBadge = document.createElement('span');
            typeBadge.className = 'module-type-badge';
            typeBadge.textContent = (module.type || 'module').toUpperCase();
            const header = card.querySelector('h3, h4, .card__title');
            if (header) header.appendChild(typeBadge);
        }
        
        // Remove code-link/action injection for cleaner UI
        
        // Hover tooltip disabled
    };
    
    
    const navigateToModule = (modulePath) => {
        // In a real implementation, this would open the code in an IDE or code viewer
        console.log('🔍 Navigating to module:', modulePath);
        
        // For now, show a modal with module information
        showModuleModal(modulePath);
    };
    
    const showModuleModal = (modulePath) => {
        const module = repositoryData.modules?.find(m => m.path === modulePath);
        if (!module) return;

        // Build a concise, DB-backed explanation using current index data
        const fCount = module.stats?.functions || module.functions?.length || 0;
        const cCount = module.stats?.classes || module.classes?.length || 0;
        const lCount = module.stats?.lines || module.lines_of_code || 0;
        const sampleImports = (module.imports || []).slice(0, 5).join(', ');
        const similar = (vectorIndex ? vectorIndex.search(module.name, 5) : [])
            .filter(m => (m.path !== module.path))
            .slice(0, 3)
            .map(m => `${m.name} (${m.path})`)
            .join(', ');
        const aboutText = `This ${module.type || 'module'} defines ${fCount} functions and ${cCount} classes across ${lCount} lines. ${sampleImports ? 'It relies on: ' + sampleImports + '. ' : ''}${similar ? 'Similar components in the codebase: ' + similar + '.' : ''}`;

        const modal = document.createElement('div');
        modal.className = 'module-modal';
        modal.innerHTML = `
            <div class="modal-backdrop"></div>
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${module.name}</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="module-info">
                        <p><strong>Type:</strong> ${module.type}</p>
                        <p><strong>Path:</strong> ${module.path}</p>
                        <p><strong>Complexity:</strong> ${module.complexity}</p>
                        <p><strong>Description:</strong> ${module.description}</p>
                    </div>
                    <div class="module-stats">
                        <h4>Statistics</h4>
                        ${Object.entries(module.stats).map(([key, value]) => 
                            `<div class="stat-row">
                                <span class="stat-label">${key}:</span>
                                <span class="stat-value">${value}</span>
                            </div>`
                        ).join('')}
                    </div>
                    <div class="module-about">
                        <h4>About this module</h4>
                        <p>${aboutText}</p>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Bind close handlers
        modal.querySelector('.modal-close').addEventListener('click', () => modal.remove());
        modal.querySelector('.modal-backdrop').addEventListener('click', () => modal.remove());
        
        // ESC key to close
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                modal.remove();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
    };
    
    const openInEditor = (modulePath) => {
        // Integration with Cursor/VS Code
        if (window.vscode) {
            // VS Code extension API
            window.vscode.postMessage({
                command: 'openFile',
                path: modulePath
            });
        } else {
            // Fallback: open in new tab or show file content
            window.open(`/code/${modulePath}`, '_blank');
        }
    };
    
    const findSimilar = (moduleName) => {
        if (!vectorIndex) return;
        
        const similar = vectorIndex.search(moduleName, 5);
        console.log('🔍 Similar modules to', moduleName, ':', similar.map(m => m.name));
        
        // Show similar modules in UI
        showSimilarModules(similar);
    };
    
    const showSimilarModules = (modules) => {
        // Implementation to show similar modules in a sidebar or modal
        console.log('Similar modules:', modules);
    };
    
    const searchModules = (query) => {
        if (!vectorIndex) return [];
        return vectorIndex.search(query);
    };
    
    const getModuleByPath = (path) => {
        return repositoryData.modules?.find(m => m.path === path);
    };
        
    const getRepositoryStats = () => {
        return {
            totalModules: repositoryData.modules?.length || 0,
            totalFiles: repositoryData.totalFiles || 0,
            totalFunctions: repositoryData.totalFunctions || 0,
            totalClasses: repositoryData.totalClasses || 0,
            lastUpdated: repositoryData.lastUpdated
        };
    };
    
    // Public API
    return {
        init,
        searchModules,
        getModuleByPath,
        getRepositoryStats,
        openInEditor,
        findSimilar,
        navigateToModule
    };
})();

// Initialize legacy system (will be removed in future version)
document.addEventListener('DOMContentLoaded', () => {
    // Only init legacy if new system is not available
    if (!window.RepositoryDataManager) {
        LegacyRepositoryDataManager.init();
    }
});

// Export legacy for backward compatibility
window.LegacyRepositoryDataManager = LegacyRepositoryDataManager;

// Architecture rendering functions moved to architecture-diagrams.js
