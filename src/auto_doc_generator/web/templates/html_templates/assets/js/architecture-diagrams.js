/* architecture-diagrams.js - Auto-generated architecture diagrams from repository analysis */

/**
 * Architecture Diagram Renderer
 * Generates dynamic Mermaid diagrams based on actual repository analysis
 */

const ArchitectureDiagrams = (() => {
    
    const renderRepositoryStructure = (modules) => {
        const container = document.getElementById('repo-structure-dynamic');
        if (!container) return;
        
        console.log('🏠 Rendering repository structure with', modules.length, 'modules');
        
        // Group modules by directory structure
        const dirStructure = {};
        modules.forEach(m => {
            if (!m.path) return;
            const parts = m.path.split('/');
            const rootDir = parts[0];
            if (!dirStructure[rootDir]) dirStructure[rootDir] = { count: 0, files: [] };
            dirStructure[rootDir].count++;
            dirStructure[rootDir].files.push(m.name || parts[parts.length - 1]);
        });
        
        const topDirs = Object.entries(dirStructure)
            .sort(([,a], [,b]) => b.count - a.count)
            .slice(0, 6);
        
        const cssSafe = (str) => str.replace(/[^a-zA-Z0-9]/g, '').substring(0, 15);
        
        const mermaidCode = `graph TD
    ROOT["🏠 Repository Root<br/>${modules.length} modules"]
    
    ${topDirs.map(([dir, info]) => {
        const safeId = cssSafe(dir);
        const displayName = dir.length > 12 ? dir.substring(0, 12) + '...' : dir;
        return `${safeId}["📁 ${displayName}<br/>${info.count} files"]`;
    }).join('\n    ')}
    
    ${topDirs.map(([dir]) => `ROOT --> ${cssSafe(dir)}`).join('\n    ')}
    
    classDef rootNode fill:#e3f2fd,stroke:#1976d2,stroke-width:3px,color:#000
    classDef dirNode fill:#f8f9fa,stroke:#6c757d,stroke-width:2px,color:#000
    
    class ROOT rootNode
    class ${topDirs.map(([dir]) => cssSafe(dir)).join(',')} dirNode`;
        
        renderMermaidDiagram(container, mermaidCode,
            `Repository structure showing ${topDirs.length} main directories with ${modules.length} total modules`,
            createRepositoryFallback(topDirs, modules.length)
        );
    };

    const renderEnterpriseArchitecture = (modules) => {
        const container = document.getElementById('enterprise-arch-dynamic');
        if (!container) return;
        
        console.log('🏢 Rendering enterprise architecture from', modules.length, 'modules');
        
        // Auto-detect module categories based on path patterns and names
        const categories = {
            routers: modules.filter(m => /router|route|endpoint/i.test(m.path || m.name || '')),
            utils: modules.filter(m => /util|helper|tool|lib/i.test(m.path || m.name || '')),
            apis: modules.filter(m => /api|server|service|elastic|search/i.test(m.path || m.name || '')),
            parsers: modules.filter(m => /parser|parse|rchilli|extract|process/i.test(m.path || m.name || '')),
            models: modules.filter(m => /model|schema|entity|data/i.test(m.path || m.name || '')),
            config: modules.filter(m => /config|setting|env/i.test(m.path || m.name || '')),
            tests: modules.filter(m => /test|spec/i.test(m.path || m.name || ''))
        };
        
        // Remove duplicates (a module might match multiple categories)
        const usedModules = new Set();
        Object.keys(categories).forEach(key => {
            categories[key] = categories[key].filter(m => {
                if (usedModules.has(m.path || m.name)) return false;
                usedModules.add(m.path || m.name);
                return true;
            });
        });
        
        console.log('📊 Auto-detected categories:', Object.fromEntries(
            Object.entries(categories).map(([k, v]) => [k, v.length])
        ));
            
        const safeName = (name) => {
            if (!name) return 'Module';
            return name
                .replace(/[^a-zA-Z0-9\s_-]/g, '')
                .replace(/([a-z])([A-Z])/g, '$1 $2')
                .replace(/_+/g, ' ')
                .trim()
                .substring(0, 20);
        };
        
        // Build dynamic subgraphs based on detected modules
        let subgraphs = [];
        let nodes = [];
        let connections = [];
        
        // API/Router Layer
        if (categories.routers.length > 0) {
            subgraphs.push(`subgraph API ["🔌 API Layer (${categories.routers.length} modules)"]`);
            categories.routers.slice(0, 3).forEach((m, i) => {
                const nodeId = `API${i+1}`;
                const nodeName = safeName(m.name || m.path?.split('/').pop() || 'Router');
                subgraphs.push(`        ${nodeId}["🔗 ${nodeName}"]`);
                nodes.push(nodeId);
            });
            subgraphs.push(`    end`);
        }
        
        // Processing Layer
        if (categories.parsers.length > 0 || categories.apis.length > 0) {
            const totalProc = categories.parsers.length + categories.apis.length;
            subgraphs.push(`subgraph PROC ["🧠 Processing (${totalProc} modules)"]`);
            
            categories.parsers.slice(0, 2).forEach((m, i) => {
                const nodeId = `PARSER${i+1}`;
                const nodeName = safeName(m.name || m.path?.split('/').pop() || 'Parser');
                subgraphs.push(`        ${nodeId}["📄 ${nodeName}"]`);
                nodes.push(nodeId);
            });
            
            categories.apis.slice(0, 2).forEach((m, i) => {
                const nodeId = `SERVICE${i+1}`;
                const nodeName = safeName(m.name || m.path?.split('/').pop() || 'Service');
                subgraphs.push(`        ${nodeId}["🔍 ${nodeName}"]`);
                nodes.push(nodeId);
            });
            
            subgraphs.push(`    end`);
        }
        
        // Utility Layer
        if (categories.utils.length > 0) {
            subgraphs.push(`subgraph UTIL ["🛠️ Utilities (${categories.utils.length} modules)"]`);
            categories.utils.slice(0, 3).forEach((m, i) => {
                const nodeId = `UTIL${i+1}`;
                const nodeName = safeName(m.name || m.path?.split('/').pop() || 'Utility');
                subgraphs.push(`        ${nodeId}["⚙️ ${nodeName}"]`);
                nodes.push(nodeId);
            });
            subgraphs.push(`    end`);
        }
        
        // Auto-generate connections based on common patterns
        if (nodes.length > 1) {
            for (let i = 0; i < nodes.length - 1; i++) {
                connections.push(`${nodes[i]} --> ${nodes[i + 1]}`);
            }
        }
        
        const mermaidCode = `graph TB
    ${subgraphs.join('\n    ')}
    
    ${connections.join('\n    ')}
    
    classDef ui fill:#e3f2fd,stroke:#1976d2,color:#000
    classDef api fill:#e8f5e8,stroke:#4caf50,color:#000
    classDef processing fill:#fff3e0,stroke:#ff9800,color:#000
    classDef utility fill:#f3e5f5,stroke:#7b1fa2,color:#000
    
    class ${categories.routers.slice(0,3).map((m,i) => `API${i+1}`).join(',')} api
    class ${categories.parsers.slice(0,2).map((m,i) => `PARSER${i+1}`).join(',')},${categories.apis.slice(0,2).map((m,i) => `SERVICE${i+1}`).join(',')} processing
    class ${categories.utils.slice(0,3).map((m,i) => `UTIL${i+1}`).join(',')} utility`;
            
        const totalModules = Object.values(categories).reduce((sum, cat) => sum + cat.length, 0);
        renderMermaidDiagram(container, mermaidCode,
            `Auto-generated Enterprise Architecture: ${totalModules} modules categorized into ${Object.keys(categories).filter(k => categories[k].length > 0).length} layers`,
            createEnterpriseFallback(categories.routers, categories.parsers, categories.apis, categories.utils)
        );
    };

    const renderLogicalArchitecture = (modules) => {
        const container = document.getElementById('logical-arch-dynamic');
        if (!container) return;
        
        console.log('🧠 Rendering logical architecture from', modules.length, 'modules');
        
        // Auto-detect data flow modules based on complexity and function count
        const dataFlowModules = modules
            .filter(m => (m.stats?.functions || 0) > 1) // Must have functions
            .sort((a, b) => {
                // Sort by importance: function count + class count + complexity
                const scoreA = (a.stats?.functions || 0) + (a.stats?.classes || 0) * 2;
                const scoreB = (b.stats?.functions || 0) + (b.stats?.classes || 0) * 2;
                return scoreB - scoreA;
            })
            .slice(0, 6); // Take top 6 most important modules
        
        console.log('📊 Data flow modules:', dataFlowModules.map(m => ({
            name: m.name,
            path: m.path,
            functions: m.stats?.functions || 0,
            classes: m.stats?.classes || 0
        })));
        
        const safeName = (name) => {
            if (!name) return 'Module';
            return name
                .replace(/[^a-zA-Z0-9\s_-]/g, '')
                .replace(/([a-z])([A-Z])/g, '$1 $2')
                .replace(/_+/g, ' ')
                .trim()
                .substring(0, 18);
        };
        
        if (dataFlowModules.length === 0) {
            container.innerHTML = createBasicFlowFallback();
            return;
        }
        
        // Build dynamic flowchart based on actual modules
        const flowNodes = dataFlowModules.map((m, i) => {
            const nodeId = `MOD${i + 1}`;
            const nodeName = safeName(m.name || m.path?.split('/').pop() || 'Module');
            const functionCount = m.stats?.functions || 0;
            return {
                id: nodeId,
                name: nodeName,
                label: `${nodeName}\\n(${functionCount} functions)`,
                module: m
            };
        });
        
        // Add input and output nodes
        const allNodes = [
            { id: 'INPUT', label: '📥 Input Data', name: 'Input' },
            ...flowNodes,
            { id: 'OUTPUT', label: '📤 Output Results', name: 'Output' }
        ];
        
        // Generate connections
        const connections = [];
        for (let i = 0; i < allNodes.length - 1; i++) {
            connections.push(`${allNodes[i].id} --> ${allNodes[i + 1].id}`);
        }
        
        const mermaidCode = `flowchart LR
    ${allNodes.map(n => `${n.id}["${n.label}"]`).join('\n    ')}
    
    ${connections.join('\n    ')}
    
    classDef inputNode fill:#e8f5e8,stroke:#4caf50,color:#000
    classDef moduleNode fill:#e3f2fd,stroke:#1976d2,color:#000
    classDef outputNode fill:#ffebee,stroke:#f44336,color:#000
    
    class INPUT inputNode
    class OUTPUT outputNode
    class ${flowNodes.map(n => n.id).join(',')} moduleNode`;
        
        renderMermaidDiagram(container, mermaidCode,
            `Auto-generated logical data flow through ${dataFlowModules.length} key processing modules`,
            createLogicalFallback(dataFlowModules, safeName)
        );
    };

    const renderPhysicalArchitecture = (modules) => {
        const container = document.getElementById('physical-arch-dynamic');
        if (!container) return;
        
        // Auto-detect deployment artifacts from actual modules
        const hasDocker = modules.some(m => m.path && /dockerfile|docker/i.test(m.path));
        const hasServer = modules.some(m => m.path && /server|app\.py|main\.py/i.test(m.path));
        const hasAPI = modules.some(m => m.path && /api|router|endpoint/i.test(m.path));
        const hasConfig = modules.some(m => m.path && /config|setting|env/i.test(m.path));
        const hasDatabase = modules.some(m => m.path && /db|database|connection/i.test(m.path));
        
        const mermaidCode = `graph TB
    subgraph "💻 Development Environment"
        DEV[🛠️ Local Development]
        ${hasConfig ? 'CONFIG[⚙️ Configuration Files]' : ''}
    end
    
    subgraph "🚀 Runtime Environment"
        ${hasServer ? 'SERVER[🖥️ Application Server]' : ''}
        ${hasAPI ? 'API[🔌 API Service]' : ''}
        ${hasDocker ? 'DOCKER[🐳 Docker Container]' : 'PYTHON[🐍 Python Runtime]'}
    end
    
    subgraph "📁 Storage Layer"
        ${hasDatabase ? 'DATABASE[💾 Database]' : ''}
        CACHE[💾 Cache Storage]
        FILES[📄 File Storage]
    end
    
    DEV --> ${hasDocker ? 'DOCKER' : 'PYTHON'}
    ${hasConfig ? 'CONFIG --> ' + (hasServer ? 'SERVER' : (hasAPI ? 'API' : 'PYTHON')) : ''}
    ${hasServer ? 'SERVER --> API' : ''}
    ${hasAPI ? 'API --> ' + (hasDatabase ? 'DATABASE' : 'CACHE') : (hasDocker ? 'DOCKER' : 'PYTHON') + ' --> CACHE'}
    ${hasDatabase ? 'DATABASE --> CACHE' : ''}
    CACHE --> FILES
    
    classDef dev fill:#e3f2fd,stroke:#1976d2
    classDef runtime fill:#e8f5e8,stroke:#4caf50
    classDef storage fill:#fff3e0,stroke:#ff9800
    
    class DEV,CONFIG dev
    class ${[hasServer ? 'SERVER' : '', hasAPI ? 'API' : '', hasDocker ? 'DOCKER' : 'PYTHON'].filter(Boolean).join(',')} runtime
    class ${[hasDatabase ? 'DATABASE' : '', 'CACHE', 'FILES'].filter(Boolean).join(',')} storage`;
        
        renderMermaidDiagram(container, mermaidCode,
            `Auto-detected physical deployment: ${hasDocker ? 'containerized' : 'native Python'} runtime with ${hasAPI ? 'API service' : 'direct'} architecture`,
            createPhysicalFallback(hasDocker, hasAPI, hasServer, hasConfig)
        );
    };

    const renderSystemComponents = (modules) => {
        const container = document.getElementById('system-components-dynamic');
        if (!container) return;
        
        console.log('🏗️ Rendering hierarchical system components from', modules.length, 'modules');
        
        // Create a more detailed hierarchical categorization
        const componentHierarchy = {
            presentation: {
                name: 'Presentation Layer',
                icon: '🎨',
                color: '#e3f2fd',
                stroke: '#1976d2',
                modules: modules.filter(m => {
                    const path = (m.path || '').toLowerCase();
                    const name = (m.name || '').toLowerCase();
                    return /ui|view|template|frontend|client|dashboard/i.test(path + name);
                })
            },
            
            application: {
                name: 'Application Layer',
                icon: '🚀',
                color: '#e8f5e8',
                stroke: '#4caf50',
                modules: modules.filter(m => {
                    const path = (m.path || '').toLowerCase();
                    const name = (m.name || '').toLowerCase();
                    return /service|api|server|router|endpoint|controller/i.test(path + name) && (m.stats?.functions || 0) > 2;
                })
            },
            
            business: {
                name: 'Business Logic',
                icon: '🧠',
                color: '#fff3e0',
                stroke: '#ff9800',
                modules: modules.filter(m => {
                    const path = (m.path || '').toLowerCase();
                    const name = (m.name || '').toLowerCase();
                    return /process|parse|analy|extract|transform|logic|rule|workflow/i.test(path + name) && (m.stats?.functions || 0) > 1;
                })
            },
            
            data: {
                name: 'Data Access Layer',
                icon: '💾',
                color: '#f3e5f5',
                stroke: '#7b1fa2',
                modules: modules.filter(m => {
                    const path = (m.path || '').toLowerCase();
                    const name = (m.name || '').toLowerCase();
                    return /model|schema|entity|data|db|database|repository|dao/i.test(path + name);
                })
            },
            
            infrastructure: {
                name: 'Infrastructure',
                icon: '🛠️',
                color: '#fce4ec',
                stroke: '#e91e63',
                modules: modules.filter(m => {
                    const path = (m.path || '').toLowerCase();
                    const name = (m.name || '').toLowerCase();
                    return /util|helper|tool|lib|common|config|setting|security|auth|log/i.test(path + name) && (m.stats?.functions || 0) > 0;
                })
            },
            
            core: {
                name: 'Core System',
                icon: '⚡',
                color: '#fff8e1',
                stroke: '#ffc107',
                modules: modules.filter(m => {
                    const path = (m.path || '').toLowerCase();
                    const name = (m.name || '').toLowerCase();
                    return /main|core|app|index|__init__|entry|bootstrap/i.test(path + name) && (m.stats?.functions || 0) > 0;
                })
            }
        };
        
        // Remove duplicates and ensure each module appears only once
        const usedModules = new Set();
        Object.keys(componentHierarchy).forEach(layerKey => {
            componentHierarchy[layerKey].modules = componentHierarchy[layerKey].modules.filter(m => {
                const moduleKey = m.path || m.name;
                if (usedModules.has(moduleKey)) return false;
                usedModules.add(moduleKey);
                return true;
            });
        });
        
        console.log('📊 Hierarchical system components:', Object.fromEntries(
            Object.entries(componentHierarchy).map(([k, v]) => [k, v.modules.length])
        ));
        
        const safeName = (name) => {
            if (!name) return 'Dir';
            return name
                .replace(/[^a-zA-Z0-9\s_-]/g, '')
                .replace(/([a-z])([A-Z])/g, '$1 $2')
                .replace(/_+/g, ' ')
                .trim()
                .substring(0, 15);
        };
        
        // Build hierarchical system component diagram
        let subgraphs = [];
        let nodes = [];
        let connections = [];
        
        // Generate subgraphs for each layer with actual modules
        Object.entries(componentHierarchy).forEach(([layerKey, layer]) => {
            if (layer.modules.length > 0) {
                const layerName = layer.name.toUpperCase().replace(/\s+/g, '');
                subgraphs.push(`subgraph ${layerName} ["${layer.icon} ${layer.name} (${layer.modules.length})"]`);
                
                // Add top modules from this layer
                layer.modules.slice(0, 4).forEach((m, i) => {
                    const nodeId = `${layerName}${i+1}`;
                    const nodeName = safeName(m.name || m.path?.split('/').pop() || 'Module');
                    const functionCount = m.stats?.functions || 0;
                    const complexity = functionCount > 5 ? 'High' : functionCount > 2 ? 'Med' : 'Low';
                    
                    subgraphs.push(`        ${nodeId}["${layer.icon} ${nodeName}\\n${functionCount}f/${complexity}"]`);
                    nodes.push({ id: nodeId, layer: layerKey, module: m });
                });
                
                subgraphs.push(`    end`);
            }
        });
        
        // Create hierarchical connections (top-down architecture)
        const layerOrder = ['presentation', 'application', 'business', 'data', 'infrastructure', 'core'];
        const layerNodes = {};
        
        // Group nodes by layer
        nodes.forEach(node => {
            if (!layerNodes[node.layer]) layerNodes[node.layer] = [];
            layerNodes[node.layer].push(node.id);
        });
        
        // Connect layers hierarchically
        for (let i = 0; i < layerOrder.length - 1; i++) {
            const currentLayer = layerOrder[i];
            const nextLayer = layerOrder[i + 1];
            
            if (layerNodes[currentLayer] && layerNodes[nextLayer]) {
                // Connect first node of current layer to first node of next layer
                connections.push(`${layerNodes[currentLayer][0]} --> ${layerNodes[nextLayer][0]}`);
                
                // Add some intra-layer connections for richness
                if (layerNodes[currentLayer].length > 1) {
                    connections.push(`${layerNodes[currentLayer][0]} --> ${layerNodes[currentLayer][1]}`);
                }
            }
        }
        
        // Add some cross-layer connections for complexity
        if (layerNodes.business && layerNodes.data) {
            connections.push(`${layerNodes.business[0]} --> ${layerNodes.data[0]}`);
        }
        if (layerNodes.application && layerNodes.infrastructure) {
            connections.push(`${layerNodes.application[0]} --> ${layerNodes.infrastructure[0]}`);
        }
        
        const mermaidCode = `graph TD
    ${subgraphs.join('\n    ')}
    
    ${connections.join('\n    ')}
    
    ${Object.entries(componentHierarchy).map(([layerKey, layer]) => {
        if (layer.modules.length > 0) {
            const layerName = layer.name.toUpperCase().replace(/\s+/g, '');
            const nodeIds = layer.modules.slice(0, 4).map((m, i) => `${layerName}${i+1}`).join(',');
            return `classDef ${layerKey} fill:${layer.color},stroke:${layer.stroke},stroke-width:2px,color:#000
    class ${nodeIds} ${layerKey}`;
        }
        return '';
    }).filter(Boolean).join('\n    ')}`;
        
        const totalComponents = Object.values(componentHierarchy).reduce((sum, layer) => sum + layer.modules.length, 0);
        const activeLayers = Object.keys(componentHierarchy).filter(k => componentHierarchy[k].modules.length > 0).length;
        
        renderMermaidDiagram(container, mermaidCode,
            `Hierarchical System Components: ${totalComponents} modules across ${activeLayers} architectural layers with complexity indicators`,
            createSystemFallback(componentHierarchy)
        );
    };

    // Helper function to render Mermaid diagrams with error handling
    const renderMermaidDiagram = (container, mermaidCode, description, fallbackHtml) => {
        try {
            container.innerHTML = `<div class="mermaid">${mermaidCode}</div><p class="diagram-info">${description}</p>`;
            
            if (window.mermaid) {
                window.mermaid.init(undefined, container.querySelector('.mermaid'));
                console.log('✅ Mermaid diagram rendered successfully');
            }
        } catch (error) {
            console.warn('⚠️ Mermaid rendering failed, using fallback:', error);
            container.innerHTML = fallbackHtml;
        }
    };

    // Fallback HTML generators
    const createRepositoryFallback = (topDirs, totalModules) => {
        return `<div class="fallback-diagram">
            <h3>📁 Repository Structure</h3>
            <ul style="list-style: none; padding: 0;">
                <li style="margin: 10px 0;"><strong>🏠 Repository Root</strong> (${totalModules} modules)</li>
                ${topDirs.map(([dir, info]) => 
                    `<li style="margin: 5px 0 5px 20px;">📁 <strong>${dir}</strong> - ${info.count} files</li>`
                ).join('')}
            </ul>
            <p class="diagram-info">Repository structure showing ${topDirs.length} main directories</p>
        </div>`;
    };

    const createEnterpriseFallback = (routers, parsers, apis, utils) => {
        return `<div class="fallback-diagram">
            <h3>🏢 Enterprise Architecture</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1rem 0;">
                <div style="padding: 1rem; border: 2px solid #4caf50; border-radius: 8px; background: #e8f5e8;">
                    <h4>🔌 API Layer</h4>
                    <p>${routers.length} routers</p>
                </div>
                <div style="padding: 1rem; border: 2px solid #ff9800; border-radius: 8px; background: #fff3e0;">
                    <h4>🧠 Processing</h4>
                    <p>${parsers.length} parsers, ${apis.length} services</p>
                </div>
                <div style="padding: 1rem; border: 2px solid #7b1fa2; border-radius: 8px; background: #f3e5f5;">
                    <h4>🛠️ Utilities</h4>
                    <p>${utils.length} utility modules</p>
                </div>
            </div>
        </div>`;
    };

    const createBasicFlowFallback = () => {
        return `<div class="fallback-diagram">
            <h3>🧠 Logical Architecture</h3>
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 2rem; border: 2px dashed #ccc; border-radius: 8px;">
                <div style="padding: 1rem; background: #e8f5e8; border-radius: 6px;">📥 Input Data</div>
                <div style="padding: 1rem; background: #e3f2fd; border-radius: 6px;">🔄 Processing</div>
                <div style="padding: 1rem; background: #ffebee; border-radius: 6px;">📤 Output</div>
            </div>
            <p class="diagram-info">Basic data flow pattern (no modules with sufficient complexity detected)</p>
        </div>`;
    };

    const createLogicalFallback = (dataFlowModules, safeName) => {
        return `<div class="fallback-diagram">
            <h3>🧠 Logical Architecture</h3>
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 2rem; border: 2px solid #1976d2; border-radius: 8px; background: #f8f9fa;">
                <div style="padding: 1rem; background: #e8f5e8; border-radius: 6px; margin: 0 1rem;">📥 Input</div>
                ${dataFlowModules.map((m,i) => 
                    `<div style="padding: 1rem; background: #e3f2fd; border-radius: 6px; margin: 0 0.5rem;">${safeName(m.name) || `Module ${i+1}`}</div>`
                ).join('')}
                <div style="padding: 1rem; background: #ffebee; border-radius: 6px; margin: 0 1rem;">📤 Output</div>
            </div>
            <p class="diagram-info">Data flow through ${dataFlowModules.length} processing modules</p>
        </div>`;
    };

    const createPhysicalFallback = (hasDocker, hasAPI, hasServer, hasConfig) => {
        return `<div class="fallback-diagram">
            <h3>🖥️ Physical Architecture</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin: 1rem 0;">
                <div style="padding: 1rem; border: 2px solid #1976d2; border-radius: 8px; background: #e3f2fd;">
                    <h4>💻 Development</h4>
                    <p>Local Environment</p>
                </div>
                <div style="padding: 1rem; border: 2px solid #4caf50; border-radius: 8px; background: #e8f5e8;">
                    <h4>🚀 Runtime</h4>
                    <p>${hasDocker ? 'Docker Container' : 'Python Runtime'}</p>
                </div>
                <div style="padding: 1rem; border: 2px solid #ff9800; border-radius: 8px; background: #fff3e0;">
                    <h4>📁 Storage</h4>
                    <p>Files & Cache</p>
                </div>
            </div>
        </div>`;
    };

    const createSystemFallback = (componentHierarchy) => {
        return `<div class="fallback-diagram">
            <h3>🏗️ Hierarchical System Components</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1rem 0;">
                ${Object.entries(componentHierarchy).filter(([k,layer]) => layer.modules.length > 0).map(([key, layer]) => 
                    `<div style="padding: 1rem; border: 2px solid ${layer.stroke}; border-radius: 8px; background: ${layer.color};">
                        <h4>${layer.icon} ${layer.name}</h4>
                        <p>${layer.modules.length} modules</p>
                        <small>${layer.modules.slice(0, 2).map(m => m.name || 'Module').join(', ')}</small>
                    </div>`
                ).join('')}
            </div>
            <p class="diagram-info">6-layer architectural hierarchy with module complexity indicators</p>
        </div>`;
    };

    const renderArchitectureDiagram = (modules) => {
        const container = document.getElementById('arch-dynamic-diagram');
        if (!container) return;
        
        console.log('🏗️ Rendering main architecture diagram from', modules.length, 'modules');
        
        // Select key modules for the architecture overview
        const keyModules = RepositoryDataManager.dedupeModules(modules)
            .filter(m => (m.stats?.functions || 0) > 2 || (m.stats?.classes || 0) > 0)
            .sort((a, b) => {
                const aScore = (a.stats?.functions || 0) + (a.stats?.classes || 0) * 2;
                const bScore = (b.stats?.functions || 0) + (b.stats?.classes || 0) * 2;
                return bScore - aScore;
            })
            .slice(0, 12); // Top 12 modules for clean diagram
        
        const safeName = (name) => {
            if (!name) return 'Module';
            // Keep more characters and handle common patterns better
            return name
                .replace(/[^a-zA-Z0-9\s_-]/g, '')
                .replace(/([a-z])([A-Z])/g, '$1 $2') // Split camelCase
                .replace(/_+/g, ' ') // Replace underscores with spaces
                .trim()
                .substring(0, 25); // Increased length
        };
        
        const cssSafe = (str) => {
            if (!str) return 'node';
            return str.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 30);
        };
        
        // Build module dependency diagram
        let nodes = [];
        let connections = [];
        let subgraphs = [];
        
        // Categorize modules by directory/type
        const categories = {
            main: [],
            api: [],
            core: [],
            utils: [],
            data: [],
            other: []
        };
        
        keyModules.forEach(m => {
            const path = (m.path || '').toLowerCase();
            const name = (m.name || '').toLowerCase();
            
            if (/main|app|index|__init__|entry/.test(path + name)) {
                categories.main.push(m);
            } else if (/api|server|router|endpoint|service/.test(path + name)) {
                categories.api.push(m);
            } else if (/core|engine|manager|controller/.test(path + name)) {
                categories.core.push(m);
            } else if (/util|helper|tool|lib|common/.test(path + name)) {
                categories.utils.push(m);
            } else if (/model|data|schema|db|database/.test(path + name)) {
                categories.data.push(m);
            } else {
                categories.other.push(m);
            }
        });
        
        // Generate subgraphs for each category
        Object.entries(categories).forEach(([catKey, catModules]) => {
            if (catModules.length === 0) return;
            
            const categoryName = catKey.toUpperCase();
            const categoryIcon = {
                main: '⚡',
                api: '🌐',
                core: '🧠',
                utils: '🛠️',
                data: '💾',
                other: '📦'
            }[catKey] || '📦';
            
            subgraphs.push(`subgraph ${categoryName} ["${categoryIcon} ${categoryName} Layer"]`);
            
            catModules.slice(0, 3).forEach((m, i) => {
                const nodeId = cssSafe(`${categoryName}${i + 1}`);
                const displayName = m.name || m.path?.split('/').pop()?.replace(/\.py$/, '') || 'Module';
                const nodeName = safeName(displayName);
                const functionCount = m.stats?.functions || 0;
                const classCount = m.stats?.classes || 0;
                
                // Create more readable node labels
                const nodeLabel = `${categoryIcon} ${nodeName}`;
                const nodeStats = `${functionCount}f${classCount > 0 ? `/${classCount}c` : ''}`;
                
                subgraphs.push(`        ${nodeId}["${nodeLabel}\\n${nodeStats}"]`);
                nodes.push({ id: nodeId, category: catKey, module: m, displayName: nodeName });
            });
            
            subgraphs.push(`    end`);
        });
        
        // Generate logical connections between layers
        const layerOrder = ['main', 'api', 'core', 'utils', 'data'];
        const nodesByCategory = {};
        
        nodes.forEach(node => {
            if (!nodesByCategory[node.category]) nodesByCategory[node.category] = [];
            nodesByCategory[node.category].push(node.id);
        });
        
        // Connect layers in architectural flow
        for (let i = 0; i < layerOrder.length - 1; i++) {
            const currentLayer = layerOrder[i];
            const nextLayer = layerOrder[i + 1];
            
            if (nodesByCategory[currentLayer] && nodesByCategory[nextLayer]) {
                connections.push(`${nodesByCategory[currentLayer][0]} --> ${nodesByCategory[nextLayer][0]}`);
            }
        }
        
        // Add some cross-connections for realistic architecture
        if (nodesByCategory.api && nodesByCategory.data) {
            connections.push(`${nodesByCategory.api[0]} --> ${nodesByCategory.data[0]}`);
        }
        if (nodesByCategory.core && nodesByCategory.utils) {
            connections.push(`${nodesByCategory.core[0]} --> ${nodesByCategory.utils[0]}`);
        }
        if (nodesByCategory.main && nodesByCategory.core) {
            connections.push(`${nodesByCategory.main[0]} --> ${nodesByCategory.core[0]}`);
        }
        
        // Add intra-layer connections
        Object.values(nodesByCategory).forEach(categoryNodes => {
            if (categoryNodes.length > 1) {
                connections.push(`${categoryNodes[0]} --> ${categoryNodes[1]}`);
            }
        });
        
        const mermaidCode = `graph TD
    ${subgraphs.join('\n    ')}
    
    ${connections.join('\n    ')}
    
    classDef main fill:#fff8e1,stroke:#ffc107,stroke-width:3px,color:#000
    classDef api fill:#e8f5e8,stroke:#4caf50,stroke-width:2px,color:#000
    classDef core fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    classDef utils fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
    classDef data fill:#fce4ec,stroke:#e91e63,stroke-width:2px,color:#000
    classDef other fill:#f5f5f5,stroke:#757575,stroke-width:2px,color:#000
    
    ${Object.entries(nodesByCategory).map(([category, nodeIds]) => 
        `class ${nodeIds.join(',')} ${category}`
    ).join('\n    ')}`;
        
        const totalModules = keyModules.length;
        const totalConnections = connections.length;
        
        renderMermaidDiagram(container, mermaidCode,
            `Dynamic Module Architecture: ${totalModules} key modules with ${totalConnections} relationships`,
            createArchitectureFallback(categories)
        );
    };

    const createArchitectureFallback = (categories) => {
        return `<div class="fallback-diagram">
            <h3>🏗️ Module Architecture Overview</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1rem 0;">
                ${Object.entries(categories).filter(([k,v]) => v.length > 0).map(([key, modules]) => {
                    const icons = { main: '⚡', api: '🌐', core: '🧠', utils: '🛠️', data: '💾', other: '📦' };
                    return `<div style="padding: 1rem; border: 2px solid #1976d2; border-radius: 8px; background: #f8f9fa;">
                        <h4>${icons[key] || '📦'} ${key.toUpperCase()}</h4>
                        <p>${modules.length} modules</p>
                        <small>${modules.slice(0, 2).map(m => m.name || 'Module').join(', ')}</small>
                    </div>`;
                }).join('')}
            </div>
            <p class="diagram-info">Architectural layers showing module dependencies and relationships</p>
        </div>`;
    };

    const renderPipelineArchitecture = (modules) => {
        const container = document.getElementById('pipeline-arch-dynamic');
        if (!container) return;
        
        console.log('⚙️ Rendering pipeline architecture from', modules.length, 'modules');
        
        // Auto-detect pipeline stages based on module patterns
        const pipelineStages = {
            input: modules.filter(m => /input|read|load|fetch|import/i.test(m.path || m.name || '')),
            process: modules.filter(m => /process|transform|parse|analy|extract/i.test(m.path || m.name || '')),
            enhance: modules.filter(m => /enhance|ai|generate|augment|enrich/i.test(m.path || m.name || '')),
            output: modules.filter(m => /output|write|save|export|render|generate/i.test(m.path || m.name || '')),
            utils: modules.filter(m => /util|helper|tool|lib|common/i.test(m.path || m.name || ''))
        };
        
        // Remove duplicates
        const usedModules = new Set();
        Object.keys(pipelineStages).forEach(stage => {
            pipelineStages[stage] = pipelineStages[stage].filter(m => {
                if (usedModules.has(m.path || m.name)) return false;
                usedModules.add(m.path || m.name);
                return true;
            });
        });
        
        const safeName = (name) => {
            if (!name) return 'Stage';
            return name
                .replace(/[^a-zA-Z0-9\s_-]/g, '')
                .replace(/([a-z])([A-Z])/g, '$1 $2')
                .replace(/_+/g, ' ')
                .trim()
                .substring(0, 20);
        };
        
        let subgraphs = [];
        let nodes = [];
        let connections = [];
        
        // Generate pipeline stages
        Object.entries(pipelineStages).forEach(([stageKey, stageModules]) => {
            if (stageModules.length === 0) return;
            
            const stageName = stageKey.toUpperCase();
            const stageIcons = {
                input: '📥',
                process: '⚙️',
                enhance: '✨',
                output: '📤',
                utils: '🛠️'
            };
            
            subgraphs.push(`subgraph ${stageName} ["${stageIcons[stageKey]} ${stageName} Stage"]`);
            
            stageModules.slice(0, 3).forEach((m, i) => {
                const nodeId = `${stageName}${i + 1}`;
                const nodeName = safeName(m.name || m.path?.split('/').pop() || 'Module');
                const functionCount = m.stats?.functions || 0;
                
                subgraphs.push(`        ${nodeId}["${stageIcons[stageKey]} ${nodeName}\\n${functionCount}f"]`);
                nodes.push({ id: nodeId, stage: stageKey });
            });
            
            subgraphs.push(`    end`);
        });
        
        // Create pipeline flow connections
        const stageOrder = ['input', 'process', 'enhance', 'output'];
        const nodesByStage = {};
        
        nodes.forEach(node => {
            if (!nodesByStage[node.stage]) nodesByStage[node.stage] = [];
            nodesByStage[node.stage].push(node.id);
        });
        
        // Connect stages in pipeline order
        for (let i = 0; i < stageOrder.length - 1; i++) {
            const currentStage = stageOrder[i];
            const nextStage = stageOrder[i + 1];
            
            if (nodesByStage[currentStage] && nodesByStage[nextStage]) {
                connections.push(`${nodesByStage[currentStage][0]} --> ${nodesByStage[nextStage][0]}`);
            }
        }
        
        // Add utility connections
        if (nodesByStage.utils) {
            ['process', 'enhance'].forEach(stage => {
                if (nodesByStage[stage]) {
                    connections.push(`${nodesByStage.utils[0]} --> ${nodesByStage[stage][0]}`);
                }
            });
        }
        
        const mermaidCode = `flowchart LR
    ${subgraphs.join('\n    ')}
    
    ${connections.join('\n    ')}
    
    classDef input fill:#e8f5e8,stroke:#4caf50,color:#000
    classDef process fill:#e3f2fd,stroke:#1976d2,color:#000
    classDef enhance fill:#fff3e0,stroke:#ff9800,color:#000
    classDef output fill:#ffebee,stroke:#f44336,color:#000
    classDef utils fill:#f3e5f5,stroke:#7b1fa2,color:#000
    
    ${Object.entries(nodesByStage).map(([stage, nodeIds]) => 
        `class ${nodeIds.join(',')} ${stage}`
    ).join('\n    ')}`;
        
        const totalStages = Object.keys(pipelineStages).filter(k => pipelineStages[k].length > 0).length;
        const totalPipelineModules = Object.values(pipelineStages).reduce((sum, stage) => sum + stage.length, 0);
        
        renderMermaidDiagram(container, mermaidCode,
            `Auto-generated Pipeline Architecture: ${totalPipelineModules} modules across ${totalStages} processing stages`,
            createPipelineFallback(pipelineStages)
        );
    };

    const createPipelineFallback = (pipelineStages) => {
        return `<div class="fallback-diagram">
            <h3>⚙️ Pipeline Architecture</h3>
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 2rem; border: 2px solid #1976d2; border-radius: 8px; background: #f8f9fa;">
                ${Object.entries(pipelineStages).filter(([k,v]) => v.length > 0).map(([stage, modules]) => {
                    const icons = { input: '📥', process: '⚙️', enhance: '✨', output: '📤', utils: '🛠️' };
                    return `<div style="padding: 1rem; background: #e3f2fd; border-radius: 6px; margin: 0 0.5rem; text-align: center;">
                        <div style="font-size: 1.5rem;">${icons[stage]}</div>
                        <div style="font-weight: bold; text-transform: uppercase;">${stage}</div>
                        <div style="font-size: 0.8rem;">${modules.length} modules</div>
                    </div>`;
                }).join('<div style="font-size: 1.5rem; color: #666;">→</div>')}
            </div>
            <p class="diagram-info">Processing pipeline with ${Object.keys(pipelineStages).filter(k => pipelineStages[k].length > 0).length} stages</p>
        </div>`;
    };

    // Public API
    return {
        renderRepositoryStructure,
        renderEnterpriseArchitecture,
        renderLogicalArchitecture,
        renderPhysicalArchitecture,
        renderSystemComponents,
        renderArchitectureDiagram,
        renderPipelineArchitecture
    };
})();

// Listen for data loaded event
document.addEventListener('repositoryDataLoaded', (event) => {
    const data = event.detail;
    const modules = data.modules || [];
    
    console.log('🏗️ Rendering architecture diagrams with', modules.length, 'modules');
    
    // Render all architecture diagrams
    ArchitectureDiagrams.renderRepositoryStructure(modules);
    ArchitectureDiagrams.renderEnterpriseArchitecture(modules);
    ArchitectureDiagrams.renderLogicalArchitecture(modules);
    ArchitectureDiagrams.renderPhysicalArchitecture(modules);
    ArchitectureDiagrams.renderSystemComponents(modules);
    ArchitectureDiagrams.renderArchitectureDiagram(modules);
    ArchitectureDiagrams.renderPipelineArchitecture(modules);
});

// Export for global access
window.ArchitectureDiagrams = ArchitectureDiagrams;

// Make individual functions globally available for backward compatibility
window.renderRepositoryStructure = ArchitectureDiagrams.renderRepositoryStructure;
window.renderEnterpriseArchitecture = ArchitectureDiagrams.renderEnterpriseArchitecture;
window.renderLogicalArchitecture = ArchitectureDiagrams.renderLogicalArchitecture;
window.renderPhysicalArchitecture = ArchitectureDiagrams.renderPhysicalArchitecture;
window.renderSystemComponents = ArchitectureDiagrams.renderSystemComponents;