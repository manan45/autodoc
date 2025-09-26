/**
 * Module Renderer - Module cards, grids, and UI components
 */
const ModuleRenderer = (() => {

    const renderAllModulesPage = (data) => {
        console.log('🔄 renderAllModulesPage called with data:', data);
        console.log('📍 Current URL:', window.location.href);
        console.log('📄 Current page title:', document.title);
        
        const statsEl = document.querySelector('#all-modules-stats');
        const gridEl = document.getElementById('all-modules-grid');
        const searchEl = document.getElementById('all-modules-search');
        const countEl = document.getElementById('all-modules-count');
        
        console.log('📊 DOM elements found:', {
            statsEl: !!statsEl,
            gridEl: !!gridEl,
            searchEl: !!searchEl,
            countEl: !!countEl
        });
        
        if (!statsEl && !gridEl) {
            console.log('ℹ️ All Modules page elements not found - skipping (this is normal on other pages)');
            return;
        }

        // Check if RepositoryDataManager is available
        if (typeof RepositoryDataManager === 'undefined') {
            console.error('❌ RepositoryDataManager not available');
            return;
        }

        const modules = RepositoryDataManager.dedupeModules(data.modules || []);
        console.log(`📋 All Modules page: ${modules.length} total modules`, modules.slice(0, 3));
        
        const totalFunctions = modules.reduce((s, m) => s + (m.stats?.functions || m.functions?.length || 0), 0);
        const totalClasses = modules.reduce((s, m) => s + (m.stats?.classes || m.classes?.length || 0), 0);
        const totalLines = modules.reduce((s, m) => s + (m.stats?.lines || m.lines_of_code || 0), 0);
        const documentedCount = modules.filter(m => (m.description || '').trim().length > 0).length;
        
        // naive complexity estimate from available stats
        const complexities = modules.map(m => (m.stats?.functions || 0) + (m.stats?.classes || 0) * 2);
        const avgComplexity = complexities.length > 0 ? complexities.reduce((a, b) => a + b, 0) / complexities.length : 0;
        const highComplexity = complexities.filter(x => x > 15).length;

        const set = (key, val) => {
            const el = statsEl?.querySelector(`[data-stat="${key}"] .stat-number`);
            if (el) el.textContent = val;
        };
        set('avgComplexity', avgComplexity.toFixed(1));
        set('highComplexity', highComplexity);
        set('documented', documentedCount);
        set('totalLines', totalLines);

        // Render modules grid with pagination
        if (gridEl) {
            let filteredModules = modules;
            let currentPage = 0;
            const densityValue = document.getElementById('density-select')?.value || 'normal';
            const pageSize = densityValue === 'compact' ? 20 : densityValue === 'detailed' ? 8 : 12;
            
            const renderPage = () => {
                const startIdx = currentPage * pageSize;
                const endIdx = startIdx + pageSize;
                const pageModules = filteredModules.slice(startIdx, endIdx);
                
                gridEl.innerHTML = '';
                pageModules.forEach(module => {
                    const card = createModuleDetailCard(module);
                    gridEl.appendChild(card);
                });
                
                const loadMoreBtn = document.getElementById('load-more-btn');
                if (loadMoreBtn) {
                    loadMoreBtn.style.display = endIdx >= filteredModules.length ? 'none' : 'block';
                    loadMoreBtn.onclick = () => {
                        currentPage++;
                        renderPage();
                    };
                }
                
                if (countEl) {
                    countEl.textContent = `Showing ${Math.min(endIdx, filteredModules.length)} of ${filteredModules.length} modules`;
                }
            };

            // Search functionality
            if (searchEl) {
                searchEl.oninput = (e) => {
                    const query = e.target.value.toLowerCase();
                    filteredModules = modules.filter(m => 
                        (m.name || '').toLowerCase().includes(query) ||
                        (m.path || '').toLowerCase().includes(query) ||
                        (m.description || '').toLowerCase().includes(query)
                    );
                    currentPage = 0;
                    renderPage();
                };
            }

            // Density selector
            const densitySelect = document.getElementById('density-select');
            if (densitySelect) {
                densitySelect.onchange = () => {
                    currentPage = 0;
                    renderPage();
                };
            }

            renderPage();
        }
    };

    const createModuleDetailCard = (module, isArchitecture = false) => {
        const card = document.createElement('div');
        card.className = 'module-detail-card';
        
        const stats = module.stats || {};
        const functions = module.functions || [];
        const classes = module.classes || [];
        
        // Create class diagram if classes exist
        let classDiagram = '';
        if (classes.length > 0) {
            classDiagram = `<div class="class-diagram">
                <h5>Class Structure</h5>
                <div class="mermaid-small">${createClassDiagram(module)}</div>
            </div>`;
        }
        
        // Function signatures
        const functionSignatures = functions.slice(0, 5).map(func => {
            return `<div class="function-signature">
                <code>${formatFunctionSignature(func)}</code>
            </div>`;
        }).join('');
        
        card.innerHTML = `
            <div class="card-header">
                <h4>${module.name || 'Unnamed Module'}</h4>
                <div class="module-path">${module.path || ''}</div>
            </div>
            
            <div class="card-content">
                <p class="module-description">${module.description || 'No description available'}</p>
                
                <div class="module-stats">
                    <span class="stat-badge">📊 ${stats.functions || functions.length || 0} functions</span>
                    <span class="stat-badge">🏗️ ${stats.classes || classes.length || 0} classes</span>
                    <span class="stat-badge">📝 ${stats.lines || module.lines_of_code || 0} lines</span>
                </div>
                
                ${classDiagram}
                
                ${functionSignatures ? `<div class="function-signatures">
                    <h5>Key Functions</h5>
                    ${functionSignatures}
                    ${functions.length > 5 ? `<small>... and ${functions.length - 5} more</small>` : ''}
                </div>` : ''}
            </div>
            
            <div class="card-actions">
                <button class="action-btn" onclick="ModuleRenderer.showModuleModal('${module.path}')">
                    📖 View Details
                </button>
            </div>
        `;
        
        return card;
    };

    const createClassDiagram = (module) => {
        const classes = module.classes || [];
        const functions = module.functions || [];
        
        if (classes.length === 0) return '';
        
        const classNodes = classes.slice(0, 3).map((cls, i) => {
            const methods = functions.filter(f => f.class === cls.name).slice(0, 3);
            const methodStr = methods.map(m => `+${m.name}()`).join('\\n');
            return `class Class${i+1} {
                ${methodStr}
            }`;
        }).join('\n    ');
        
        return `classDiagram
    ${classNodes}`;
    };

    const formatFunctionSignature = (func) => {
        if (typeof func === 'string') return func;
        
        const name = func.name || 'function';
        const params = func.parameters || func.args || [];
        const paramStr = Array.isArray(params) ? params.map(p => {
            if (typeof p === 'string') return p;
            return p.name ? `${p.name}: ${p.type || 'any'}` : p;
        }).join(', ') : '';
        
        return `${name}(${paramStr})`;
    };

    const showModuleModal = async (modulePath) => {
        const module = RepositoryDataManager.getModuleByPath(modulePath);
        if (!module) return;

        // Show loading state
        showLoadingModal(module.name || 'Module Details');
        
        // Use enhanced Cursor + local similarity search
        const similar = await RepositoryDataManager.findSimilarModules(module, 3);
        const stats = module.stats || {};
        const functions = module.functions || [];
        const classes = module.classes || [];
        const imports = module.imports || [];
        
        // Get Cursor integration status
        const cursorStatus = RepositoryDataManager.getCursorStatus();

        const modalContent = `
            <div class="modal-overlay" onclick="ModuleRenderer.closeModal()">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <div class="modal-header">
                        <h3>${module.name || 'Module Details'}</h3>
                        <div class="cursor-status">
                            ${cursorStatus.available ? '🎯 Cursor Enhanced' : '🏠 Local Analysis'}
                        </div>
                        <button class="close-btn" onclick="ModuleRenderer.closeModal()">×</button>
                    </div>
                    
                    <div class="modal-body">
                        <div class="module-info">
                            <p><strong>Path:</strong> <code>${module.path}</code></p>
                            <p><strong>Description:</strong> ${module.description || 'No description available'}</p>
                            ${cursorStatus.available ? `
                                <p><small>🔍 Analysis powered by Cursor's vector database for enhanced semantic understanding</small></p>
                            ` : ''}
                        </div>
                        
                        <div class="module-summary">
                            <h4>📊 About this module</h4>
                            <p>This module contains <strong>${functions.length} functions</strong> and <strong>${classes.length} classes</strong> 
                            across <strong>${stats.lines || module.lines_of_code || 0} lines</strong> of code.</p>
                            
                            ${imports.length > 0 ? `
                                <p><strong>Top imports:</strong> ${imports.slice(0, 3).join(', ')}</p>
                            ` : ''}
                            
                            ${similar.length > 0 ? `
                                <div class="similar-modules">
                                    <p><strong>Similar modules ${cursorStatus.available ? '(Cursor AI)' : '(Local)'}:</strong></p>
                                    <div class="similar-grid">
                                        ${similar.map(s => `
                                            <div class="similar-item" onclick="ModuleRenderer.showModuleModal('${s.path}')">
                                                <strong>${s.name || 'Module'}</strong>
                                                ${s.similarity ? `<small>(${(s.similarity * 100).toFixed(1)}% similar)</small>` : ''}
                                                ${s.source ? `<span class="source-badge">${s.source}</span>` : ''}
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                        
                        ${functions.length > 0 ? `
                            <div class="functions-list">
                                <h4>🔧 Functions</h4>
                                <div class="function-grid">
                                    ${functions.slice(0, 6).map(func => `
                                        <div class="function-item">
                                            <code>${formatFunctionSignature(func)}</code>
                                        </div>
                                    `).join('')}
                                    ${functions.length > 6 ? `<p><small>... and ${functions.length - 6} more functions</small></p>` : ''}
                                </div>
                            </div>
                        ` : ''}
                        
                        ${classes.length > 0 ? `
                            <div class="classes-list">
                                <h4>🏗️ Classes</h4>
                                <div class="class-grid">
                                    ${classes.slice(0, 4).map(cls => `
                                        <div class="class-item">
                                            <strong>${cls.name || cls}</strong>
                                        </div>
                                    `).join('')}
                                    ${classes.length > 4 ? `<p><small>... and ${classes.length - 4} more classes</small></p>` : ''}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;

        // Replace loading modal with actual content
        const existingModal = document.querySelector('.modal-overlay');
        if (existingModal) existingModal.remove();
        
        document.body.insertAdjacentHTML('beforeend', modalContent);
    };

    const showLoadingModal = (title) => {
        const loadingContent = `
            <div class="modal-overlay" onclick="ModuleRenderer.closeModal()">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <div class="modal-header">
                        <h3>${title}</h3>
                        <button class="close-btn" onclick="ModuleRenderer.closeModal()">×</button>
                    </div>
                    <div class="modal-body">
                        <div class="loading-state">
                            <div class="spinner"></div>
                            <p>🔍 Analyzing module with Cursor AI...</p>
                            <p><small>Searching for similar modules and generating insights</small></p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', loadingContent);
    };

    const closeModal = () => {
        const modal = document.querySelector('.modal-overlay');
        if (modal) modal.remove();
    };

    const createModuleCard = (module) => {
        const card = document.createElement('div');
        card.className = 'getting-started-card module-card';
        
        const stats = module.stats || {};
        const complexity = stats.functions + (stats.classes * 2);
        const complexityClass = complexity > 15 ? 'high' : complexity > 5 ? 'medium' : 'low';
        
        card.innerHTML = `
            <div class="card-icon">📦</div>
            <h3>${module.name || 'Module'}</h3>
            <p>${module.description || 'No description available'}</p>
            <div class="module-stats">
                <div class="stat-item">
                    <span class="stat-number">${stats.functions || 0}</span>
                    <span class="stat-label">Functions</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${stats.classes || 0}</span>
                    <span class="stat-label">Classes</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${stats.lines || 0}</span>
                    <span class="stat-label">Lines</span>
                </div>
            </div>
            <div class="complexity-indicator complexity-${complexityClass}">
                ${complexityClass.charAt(0).toUpperCase() + complexityClass.slice(1)} Complexity
            </div>
        `;
        
        card.onclick = () => showModuleModal(module.path);
        
        return card;
    };

    const renderOverviewTopModules = (modules) => {
        const container = document.getElementById('overview-modules');
        if (!container) return;
        container.innerHTML = '';
        // Overview: Show most important/central modules
        const unique = RepositoryDataManager.dedupeModules(modules)
            .filter(m => (m.description || '').trim().length > 0)
            .filter(m => m.type !== 'test' && m.type !== 'utility') // Exclude tests/utils
            .sort((a, b) => {
                const scoreA = (a.stats?.functions || 0) + (a.stats?.classes || 0) * 3 + (a.stats?.lines || 0) / 100;
                const scoreB = (b.stats?.functions || 0) + (b.stats?.classes || 0) * 3 + (b.stats?.lines || 0) / 100;
                return scoreB - scoreA;
            })
            .slice(0, 6);
        unique.forEach(m => container.appendChild(createModuleCard(m)));
    };

    const renderComponentsGrid = (modules) => {
        const container = document.getElementById('components-grid');
        if (!container) {
            console.log('ℹ️ Components grid not found - skipping (this is normal on other pages)');
            return;
        }
        
        console.log('🧩 Rendering components grid with', modules.length, 'modules');
        container.innerHTML = '';
        
        // Components: Show modules that look like reusable components
        const items = RepositoryDataManager.dedupeModules(modules)
            .filter(m => {
                const path = (m.path || '').toLowerCase();
                const name = (m.name || '').toLowerCase();
                const hasClasses = (m.stats?.classes || m.classes?.length || 0) > 0;
                const hasFunctions = (m.stats?.functions || m.functions?.length || 0) > 2;
                
                // Component-like patterns
                const isComponent = /component|widget|element|ui|view|render|display/.test(path + name);
                const isService = /service|manager|handler|processor|controller|api/.test(path + name);
                const isUtility = /util|helper|tool|lib|common/.test(path + name) && hasFunctions;
                
                return (isComponent || isService || isUtility) && (hasClasses || hasFunctions);
            })
            .sort((a, b) => {
                const aScore = (a.stats?.functions || 0) + (a.stats?.classes || 0) * 2;
                const bScore = (b.stats?.functions || 0) + (b.stats?.classes || 0) * 2;
                return bScore - aScore;
            })
            .slice(0, 20); // Limit to top 20 components
            
        console.log('🧩 Found', items.length, 'components to display');
        items.forEach(m => container.appendChild(createModuleDetailCard(m)));
    };

    const renderModulesStructure = (modules) => {
        const container = document.getElementById('modules-structure');
        if (!container) return;
        container.innerHTML = '';

        // Modules Structure: Show architectural/structural modules only
        const topLevel = RepositoryDataManager.dedupeModules(modules)
            .filter(m => !m.path || m.path.split('/').length <= 2)
            .filter(m => m.type !== 'test' && m.type !== 'utility')
            .sort((a, b) => (b.stats?.classes || 0) - (a.stats?.classes || 0)); // Class-heavy modules first
        topLevel.slice(0, 12).forEach(m => {
            container.appendChild(createModuleCard(m));
        });
    };

    const renderApiPage = (data) => {
        // Placeholder for API-specific rendering
        console.log('🔌 API page rendering (placeholder)');
    };

    return {
        renderAllModulesPage,
        createModuleDetailCard,
        createModuleCard,
        showModuleModal,
        closeModal,
        renderOverviewTopModules,
        renderComponentsGrid,
        renderModulesStructure,
        renderApiPage,
        formatFunctionSignature,
        createClassDiagram
    };
})();

// Listen for data loaded event
document.addEventListener('repositoryDataLoaded', (event) => {
    const data = event.detail;
    
    // Render module-related UI components
    ModuleRenderer.renderAllModulesPage(data);
    ModuleRenderer.renderOverviewTopModules(data.modules || []);
    ModuleRenderer.renderComponentsGrid(data.modules || []);
    ModuleRenderer.renderModulesStructure(data.modules || []);
    ModuleRenderer.renderApiPage(data);
});

// Export for global access
window.ModuleRenderer = ModuleRenderer;
