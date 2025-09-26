/**
 * Core Data Manager - Repository data loading and caching
 */
const RepositoryDataManager = (() => {
    let repositoryData = {};
    let vectorIndex = null;

    const init = async () => {
        console.log('🚀 Initializing Repository Data Manager');
        try {
            const response = await fetch('/api/repository-data');
            repositoryData = await response.json();
            
            console.log('📊 Repository data loaded:', {
                modules: repositoryData.modules?.length || 0,
                totalFunctions: repositoryData.totalFunctions || 0,
                totalClasses: repositoryData.totalClasses || 0
            });
            
            // Build vector index for similarity search
            buildVectorIndex(repositoryData.modules || []);
            
            // Notify other modules that data is ready
            document.dispatchEvent(new CustomEvent('repositoryDataLoaded', { 
                detail: repositoryData 
            }));
            
        } catch (error) {
            console.error('Failed to load repository data:', error);
            document.dispatchEvent(new CustomEvent('repositoryDataLoadFailed', { 
                detail: { error: error.message || 'Repository data unavailable' }
            }));
        }
    };

    const buildVectorIndex = async (modules) => {
        console.log('🔍 Building hybrid vector index (Cursor + Local)');
        vectorIndex = new Map();
        
        // Try to use AI editor's vector database first
        const aiEditorDB = await initializeAIEditorDB();
        
        for (let idx = 0; idx < modules.length; idx++) {
            const module = modules[idx];
            const text = `${module.name || ''} ${module.description || ''} ${module.path || ''}`;
            
            let embedding = null;
            
            // Try AI editor's vector embedding first
            if (aiEditorDB) {
                try {
                    embedding = await getAIEditorEmbedding(module, text, aiEditorDB);
                    console.log(`📊 Using ${aiEditorDB.editor || 'AI'} embedding for ${module.name}`);
                } catch (error) {
                    console.warn(`⚠️ AI editor embedding failed for ${module.name}:`, error);
                }
            }
            
            // Fallback to local embedding if Cursor fails
            if (!embedding) {
                embedding = generateLocalEmbedding(text);
                console.log(`🏠 Using local embedding for ${module.name}`);
            }
            
            vectorIndex.set(idx, { 
                module, 
                embedding, 
                source: embedding.source || 'local',
                metadata: {
                    functions: module.functions?.length || 0,
                    classes: module.classes?.length || 0,
                    complexity: calculateComplexity(module),
                    lastModified: module.lastModified || Date.now()
                }
            });
        }
        
        console.log(`📈 Hybrid vector index built with ${vectorIndex.size} entries`);
    };

    const initializeAIEditorDB = async () => {
        try {
            // Check for various AI editor environments
            const editors = [
                { name: 'cursor', obj: window.cursor, api: '/cursor/api' },
                { name: 'copilot', obj: window.vscode?.copilot, api: '/copilot/api' },
                { name: 'codewhisperer', obj: window.aws?.codewhisperer, api: '/aws/api' },
                { name: 'tabnine', obj: window.tabnine, api: '/tabnine/api' }
            ];
            
            // Check window objects first
            for (const editor of editors) {
                if (typeof window !== 'undefined' && editor.obj) {
                    console.log(`🎯 ${editor.name} environment detected`);
                    return { 
                        editor: editor.name, 
                        type: 'window', 
                        obj: editor.obj.vectorDB || editor.obj.ai || editor.obj 
                    };
                }
            }
            
            // Check API endpoints
            for (const editor of editors) {
                try {
                    const response = await fetch(`${editor.api}/health`, { 
                        method: 'HEAD',
                        timeout: 1000 
                    });
                    if (response.ok) {
                        console.log(`🔗 ${editor.name} API endpoint available`);
                        return { 
                            editor: editor.name, 
                            type: 'api', 
                            endpoint: `${editor.api}/vector-search` 
                        };
                    }
                } catch (error) {
                    // Continue to next editor
                }
            }
        } catch (error) {
            console.log('ℹ️ No AI editor detected, using local analysis only');
        }
        return null;
    };

    const getAIEditorEmbedding = async (module, text, editorDB) => {
        // Try different AI editor integration methods
        
        // Method 1: Direct API via window object
        if (window.cursor?.vectorDB?.embed) {
            return await window.cursor.vectorDB.embed(text, {
                type: 'code_module',
                metadata: {
                    path: module.path,
                    language: 'python',
                    functions: module.functions?.length || 0,
                    classes: module.classes?.length || 0
                }
            });
        }
        
        // Method 2: Cursor AI API
        if (window.cursor?.ai?.embed) {
            return await window.cursor.ai.embed(text, {
                model: 'code-embedding',
                context: 'repository_analysis'
            });
        }
        
        // Method 3: HTTP API - Disabled for static documentation
        // API calls are disabled for static documentation sites
        // Using local embedding instead
        
        // Fallback to local embedding
    };

    const generateLocalEmbedding = (text) => {
        // Enhanced local embedding with better semantic understanding
        const words = text.toLowerCase().split(/\s+/);
        const embedding = new Array(128).fill(0); // Larger dimension
        
        // Code-specific keywords get higher weights
        const codeKeywords = {
            'function': 3, 'class': 3, 'method': 2, 'api': 2, 'service': 2,
            'analyzer': 2, 'generator': 2, 'processor': 2, 'handler': 2,
            'model': 2, 'pipeline': 2, 'workflow': 2, 'interface': 2,
            'component': 2, 'module': 1.5, 'utility': 1, 'helper': 1
        };
        
        words.forEach((word, wordIdx) => {
            const weight = codeKeywords[word] || 1;
            let hash = 0;
            
            for (let i = 0; i < word.length; i++) {
                const char = word.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash;
            }
            
            // Multiple hash functions for better distribution
            const indices = [
                Math.abs(hash) % embedding.length,
                Math.abs(hash * 31) % embedding.length,
                Math.abs(hash * 17 + wordIdx) % embedding.length
            ];
            
            indices.forEach(index => {
                embedding[index] += weight;
            });
        });
        
        // Normalize
        const magnitude = Math.sqrt(embedding.reduce((sum, val) => sum + val * val, 0));
        const normalized = magnitude > 0 ? embedding.map(val => val / magnitude) : embedding;
        
        return { 
            vector: normalized, 
            source: 'local',
            confidence: 0.7 // Lower confidence than Cursor embeddings
        };
    };

    const calculateComplexity = (module) => {
        const functions = module.functions?.length || module.stats?.functions || 0;
        const classes = module.classes?.length || module.stats?.classes || 0;
        const lines = module.lines_of_code || module.stats?.lines || 0;
        
        return functions + (classes * 2) + (lines / 100);
    };

    const cosineSimilarity = (embeddingA, embeddingB) => {
        // Handle different embedding formats (Cursor vs Local)
        const vecA = embeddingA.vector || embeddingA;
        const vecB = embeddingB.vector || embeddingB;
        
        if (!vecA || !vecB || vecA.length !== vecB.length) {
            console.warn('⚠️ Embedding dimension mismatch or missing vectors');
            return 0;
        }
        
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

    const findSimilarModules = async (targetModule, limit = 5) => {
        if (!vectorIndex || !targetModule) return [];
        
        console.log(`🔍 Finding similar modules for: ${targetModule.name}`);
        
        // Try Cursor's semantic search first
        const cursorResults = await findSimilarWithCursor(targetModule, limit);
        if (cursorResults.length > 0) {
            console.log(`📊 Found ${cursorResults.length} similar modules using Cursor`);
            return cursorResults;
        }
        
        // Fallback to local vector search
        const targetText = `${targetModule.name || ''} ${targetModule.description || ''} ${targetModule.path || ''}`;
        const targetEmbedding = generateLocalEmbedding(targetText);
        
        const similarities = [];
        vectorIndex.forEach((entry, idx) => {
            if (entry.module === targetModule) return; // Skip self
            
            const similarity = cosineSimilarity(targetEmbedding, entry.embedding);
            const confidence = entry.embedding.confidence || 0.7;
            const adjustedSimilarity = similarity * confidence;
            
            if (adjustedSimilarity > 0.1) {
                similarities.push({ 
                    module: entry.module, 
                    similarity: adjustedSimilarity,
                    source: entry.source,
                    confidence: confidence
                });
            }
        });
        
        const results = similarities
            .sort((a, b) => b.similarity - a.similarity)
            .slice(0, limit)
            .map(item => ({
                ...item.module,
                similarity: item.similarity,
                source: item.source
            }));
            
        console.log(`🏠 Found ${results.length} similar modules using local vectors`);
        return results;
    };

    const findSimilarWithCursor = async (targetModule, limit = 5) => {
        try {
            // Method 1: Direct Cursor semantic search
            if (window.cursor?.vectorDB?.search) {
                const results = await window.cursor.vectorDB.search({
                    query: `${targetModule.name} ${targetModule.description}`,
                    type: 'code_module',
                    limit: limit,
                    filters: {
                        exclude_path: targetModule.path,
                        repository: window.location.origin
                    }
                });
                
                return results.map(r => ({
                    ...r.metadata,
                    similarity: r.score,
                    source: 'cursor'
                }));
            }
            
            // Method 2: Cursor AI similarity
            if (window.cursor?.ai?.findSimilar) {
                const results = await window.cursor.ai.findSimilar(targetModule.path, {
                    type: 'semantic',
                    context: 'repository_analysis',
                    limit: limit
                });
                
                return results.map(r => ({
                    name: r.name,
                    path: r.path,
                    description: r.description,
                    similarity: r.confidence,
                    source: 'cursor'
                }));
            }
            
            // Method 3: HTTP API - Disabled for static documentation
            // API calls are disabled for static documentation sites
            // Using local vector search instead
            
        } catch (error) {
            console.warn('⚠️ Cursor similarity search failed:', error);
        }
        
        return [];
    };

    const enhancedSemanticSearch = async (query, options = {}) => {
        const {
            limit = 10,
            type = 'general',
            includeCode = false,
            filters = {}
        } = options;
        
        console.log(`🔍 Enhanced semantic search: "${query}"`);
        
        // Try Cursor's advanced search first
        if (window.cursor?.vectorDB?.semanticSearch) {
            try {
                const results = await window.cursor.vectorDB.semanticSearch({
                    query: query,
                    type: type,
                    limit: limit,
                    includeCode: includeCode,
                    filters: filters
                });
                
                console.log(`📊 Cursor semantic search found ${results.length} results`);
                return results.map(r => ({
                    ...r,
                    source: 'cursor',
                    relevance: r.score || r.relevance
                }));
            } catch (error) {
                console.warn('⚠️ Cursor semantic search failed:', error);
            }
        }
        
        // Fallback to local search
        const queryEmbedding = generateLocalEmbedding(query);
        const results = [];
        
        vectorIndex.forEach((entry, idx) => {
            const similarity = cosineSimilarity(queryEmbedding, entry.embedding);
            if (similarity > 0.2) {
                results.push({
                    module: entry.module,
                    similarity: similarity,
                    source: 'local',
                    relevance: similarity * (entry.embedding.confidence || 0.7)
                });
            }
        });
        
        const sortedResults = results
            .sort((a, b) => b.relevance - a.relevance)
            .slice(0, limit);
            
        console.log(`🏠 Local semantic search found ${sortedResults.length} results`);
        return sortedResults;
    };

    const getRepositoryData = () => repositoryData;
    const getVectorIndex = () => vectorIndex;
    const getModuleByPath = (path) => repositoryData.modules?.find(m => m.path === path);

    // Utility functions
    const dedupeModules = (modules) => {
        const seen = new Set();
        return modules.filter(m => {
            const key = `${m.name || 'unnamed'}-${m.path || 'nopath'}`;
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        });
    };

    const cssSafe = (str) => (str || '').replace(/[^a-zA-Z0-9]/g, '_');

    return {
        init,
        getRepositoryData,
        getVectorIndex,
        getModuleByPath,
        findSimilarModules,
        enhancedSemanticSearch,
        dedupeModules,
        cssSafe,
        // Cursor integration status
        getCursorStatus: () => ({
            available: !!window.cursor,
            vectorDB: !!window.cursor?.vectorDB,
            ai: !!window.cursor?.ai
        })
    };
})();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    RepositoryDataManager.init();
});

// Export for global access
window.RepositoryDataManager = RepositoryDataManager;
