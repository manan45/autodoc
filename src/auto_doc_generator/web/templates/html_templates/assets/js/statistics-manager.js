/**
 * Statistics Manager - Page-specific statistics calculations and updates
 */
const StatisticsManager = (() => {

    const updateAllStatistics = (data) => {
        updateOverviewStats(data);
        updateModulesStats(data);
        updateComplexityStats(data);
        updateAIStats(data);
        updatePipelineStats(data);
        updateAPIStats(data);
        updateCodebaseStats(data);
        updateQualityMetrics(data);
        updateSidebarStats(data);
    };

    const updateOverviewStats = (data) => {
        const overviewStats = document.querySelector('#overview-stats');
        if (!overviewStats) return;
        
        const modulesList = data.modules || [];
        const totalFunctions = modulesList.reduce((sum, m) => sum + (m.stats?.functions || m.functions?.length || 0), 0);
        const totalClasses = modulesList.reduce((sum, m) => sum + (m.stats?.classes || m.classes?.length || 0), 0);
        
        const set = (key, val) => {
            const el = overviewStats.querySelector(`[data-stat="${key}"] .stat-number`);
            if (el) el.textContent = val;
        };
        set('modules', modulesList.length);
        set('files', modulesList.length);
        set('functions', totalFunctions);
        set('classes', totalClasses);
    };

    const updateModulesStats = (data) => {
        const modulesStats = document.querySelector('#modules-stats');
        if (!modulesStats) return;
        
        const modulesList = data.modules || [];
        const totalFunctions = modulesList.reduce((sum, m) => sum + (m.stats?.functions || 0), 0);
        const totalClasses = modulesList.reduce((sum, m) => sum + (m.stats?.classes || 0), 0);
        const totalLines = modulesList.reduce((sum, m) => sum + (m.stats?.lines || 0), 0);
        
        const set = (key, val) => {
            const el = modulesStats.querySelector(`[data-stat="${key}"] .stat-number`);
            if (el) el.textContent = val;
        };
        set('modules', modulesList.length);
        set('functions', totalFunctions);
        set('classes', totalClasses);
        set('lines', totalLines);
    };

    const updateComplexityStats = (data) => {
        const complexityStats = document.querySelector('#complexity-stats');
        if (!complexityStats) return;
        
        const modulesList = data.modules || [];
        const avgComplexity = modulesList.length > 0 
            ? modulesList.reduce((sum, m) => sum + ((m.stats?.functions || 0) + (m.stats?.classes || 0) * 2), 0) / modulesList.length
            : 0;
        const highComplexity = modulesList.filter(m => ((m.stats?.functions || 0) + (m.stats?.classes || 0) * 2) > 15).length;
        const documentedCount = modulesList.filter(m => (m.description || '').trim().length > 0).length;
        const totalLines = modulesList.reduce((sum, m) => sum + (m.stats?.lines || 0), 0);
        
        const set = (key, val) => {
            const el = complexityStats.querySelector(`[data-stat="${key}"] .stat-number`);
            if (el) el.textContent = val;
        };
        set('avgComplexity', avgComplexity.toFixed(1));
        set('highComplexity', highComplexity);
        set('documented', documentedCount);
        set('totalLines', totalLines);
        set('lowComplexity', modulesList.filter(m => ((m.stats?.functions || 0) + (m.stats?.classes || 0) * 2) < 5).length);
        set('mediumComplexity', modulesList.filter(m => {
            const complexity = (m.stats?.functions || 0) + (m.stats?.classes || 0) * 2;
            return complexity >= 5 && complexity <= 15;
        }).length);
    };

    const updateAIStats = (data) => {
        const aiStats = document.querySelector('#ai-stats');
        if (!aiStats) return;
        
        const modulesList = data.modules || [];
        const aiModules = modulesList.filter(m => /ai|model|ml|neural|embedding|llm|gpt/i.test(m.name || m.path || ''));
        const pipelines = modulesList.filter(m => /pipeline|workflow|process/i.test(m.name || m.path || ''));
        const analyzers = modulesList.filter(m => /analy[sz]er?|processor/i.test(m.name || m.path || ''));
        const generators = modulesList.filter(m => /generat|creat|build/i.test(m.name || m.path || ''));
        
        const set = (key, val) => {
            const el = aiStats.querySelector(`[data-stat="${key}"] .stat-number`);
            if (el) el.textContent = val;
        };
        set('models', aiModules.length);
        set('pipelines', pipelines.length);
        set('analyzers', analyzers.length);
        set('generators', generators.length);
    };

    const updatePipelineStats = (data) => {
        const pipelineStats = document.querySelector('#pipeline-stats');
        if (!pipelineStats) return;
        
        const modulesList = data.modules || [];
        const pipelines = modulesList.filter(m => /pipeline|workflow|process/i.test(m.name || m.path || ''));
        const stages = pipelines.reduce((sum, p) => sum + (p.stats?.functions || 0), 0);
        const processors = modulesList.filter(m => /process|transform|convert/i.test(m.name || m.path || ''));
        const workflows = modulesList.filter(m => /workflow|flow|chain/i.test(m.name || m.path || ''));
        
        const set = (key, val) => {
            const el = pipelineStats.querySelector(`[data-stat="${key}"] .stat-number`);
            if (el) el.textContent = val;
        };
        set('pipelines', pipelines.length);
        set('stages', stages);
        set('processors', processors.length);
        set('workflows', workflows.length);
    };

    const updateAPIStats = (data) => {
        const apiStats = document.querySelector('#api-stats');
        if (!apiStats) return;
        
        const modulesList = data.modules || [];
        const apiModules = modulesList.filter(m => /api|endpoint|router|server/i.test(m.name || m.path || ''));
        const endpoints = modulesList.reduce((sum, m) => {
            if (/api|server|endpoint/i.test(m.name || m.path || '')) {
                return sum + (m.stats?.functions || 0);
            }
            return sum;
        }, 0);
        const interfaces = modulesList.filter(m => /interface|contract|protocol/i.test(m.name || m.path || ''));
        const services = modulesList.filter(m => /service|handler|controller/i.test(m.name || m.path || ''));
        
        const set = (key, val) => {
            const el = apiStats.querySelector(`[data-stat="${key}"] .stat-number`);
            if (el) el.textContent = val;
        };
        set('endpoints', Math.min(endpoints, 50)); // Cap realistic number
        set('interfaces', interfaces.length);
        set('patterns', Math.ceil(apiModules.length / 2)); // Estimated patterns
        set('modules', apiModules.length);
        set('services', services.length);
    };

    const updateCodebaseStats = (data) => {
        const codebaseStats = document.querySelector('#codebase-stats');
        if (!codebaseStats) return;
        
        const modulesList = data.modules || [];
        const totalLines = modulesList.reduce((sum, m) => sum + (m.stats?.lines || 0), 0);
        const totalFunctions = modulesList.reduce((sum, m) => sum + (m.stats?.functions || 0), 0);
        const totalClasses = modulesList.reduce((sum, m) => sum + (m.stats?.classes || 0), 0);
        const packageCount = new Set(modulesList.map(m => m.path?.split('/')[0]).filter(Boolean)).size;
        
        const set = (key, val) => {
            const el = codebaseStats.querySelector(`[data-stat="${key}"] .stat-number`);
            if (el) el.textContent = val;
        };
        set('files', modulesList.length);
        set('lines', totalLines);
        set('functions', totalFunctions);
        set('packages', packageCount);
        set('modules', modulesList.length);
        set('classes', totalClasses);
    };

    const updateQualityMetrics = (data) => {
        const qualityStats = document.querySelector('#quality-stats');
        if (!qualityStats) return;
        
        const modulesList = data.modules || [];
        const documentedCount = modulesList.filter(m => (m.description || '').trim().length > 0).length;
        const docCoverage = modulesList.length > 0 ? ((documentedCount / modulesList.length) * 100).toFixed(1) : 0;
        const avgComplexity = modulesList.length > 0 
            ? modulesList.reduce((sum, m) => sum + ((m.stats?.functions || 0) + (m.stats?.classes || 0) * 2), 0) / modulesList.length
            : 0;
        const testFiles = modulesList.filter(m => /test|spec/i.test(m.name || m.path || '')).length;
        const testCoverage = modulesList.length > 0 ? Math.min((testFiles / modulesList.length) * 100, 100).toFixed(1) : 0;
        
        const set = (key, val) => {
            const el = qualityStats.querySelector(`[data-stat="${key}"] .stat-number`);
            if (el) el.textContent = val;
        };
        set('docCoverage', `${docCoverage}%`);
        set('testCoverage', `${testCoverage}%`);
        set('avgComplexity', avgComplexity.toFixed(1));
        set('codeSmells', Math.max(0, modulesList.length - documentedCount)); // Undocumented as code smells
        set('maintainability', docCoverage > 70 ? 'High' : docCoverage > 40 ? 'Medium' : 'Low');
        set('technical_debt', avgComplexity > 10 ? 'High' : avgComplexity > 5 ? 'Medium' : 'Low');
    };

    const updateSidebarStats = (data) => {
        // Update sidebar stats
        const statsElements = document.querySelectorAll('.md-nav__stats-number');
        const statsLabels = document.querySelectorAll('.md-nav__stats-label');
        
        if (statsElements.length >= 3) {
            statsElements[0].textContent = data.totalFiles || 0;
            statsElements[1].textContent = data.totalFunctions || 0;
            statsElements[2].textContent = data.totalClasses || 0;
        }
        
        // Update any stats cards on the page
        const statCards = document.querySelectorAll('.metric-card, .stats-widget .stat-value');
        statCards.forEach(card => {
            const label = card.closest('.metric-card')?.querySelector('.metric-label')?.textContent?.toLowerCase();
            if (label) {
                if (label.includes('file')) card.textContent = data.totalFiles || 0;
                if (label.includes('function')) card.textContent = data.totalFunctions || 0;
                if (label.includes('class')) card.textContent = data.totalClasses || 0;
                if (label.includes('module')) card.textContent = data.modules?.length || 0;
            }
        });

        // Update sidebar counts for Modules and Components
        const modulesCountEl = document.getElementById('sidebar-modules-count');
        const componentsCountEl = document.getElementById('sidebar-components-count');
        if (modulesCountEl || componentsCountEl) {
            const modulesList = RepositoryDataManager.dedupeModules(data.modules || []).filter(m => !m.path || m.path.split('/').length <= 2);
            const componentsList = RepositoryDataManager.dedupeModules(data.modules || []).filter(m => (m.description || '').trim().length > 0);
            if (modulesCountEl) modulesCountEl.textContent = `(${modulesList.length})`;
            if (componentsCountEl) componentsCountEl.textContent = `(${componentsList.length})`;
        }
    };

    return {
        updateAllStatistics,
        updateOverviewStats,
        updateModulesStats,
        updateComplexityStats,
        updateAIStats,
        updatePipelineStats,
        updateAPIStats,
        updateCodebaseStats,
        updateQualityMetrics,
        updateSidebarStats
    };
})();

// Listen for data loaded event
document.addEventListener('repositoryDataLoaded', (event) => {
    const data = event.detail;
    StatisticsManager.updateAllStatistics(data);
});

// Export for global access
window.StatisticsManager = StatisticsManager;
