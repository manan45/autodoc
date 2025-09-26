/**
 * Routing Visualizer - Creates visual representations of code routing and navigation
 */
const RoutingVisualizer = (() => {

    const renderRoutingDiagram = (containerId, routingType = 'overview') => {
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`Container ${containerId} not found for routing diagram`);
            return;
        }

        const routingGraph = RoutingSystem.getRoutingGraph();
        if (!routingGraph) {
            container.innerHTML = '<div class="loading-placeholder">Building routing analysis...</div>';
            return;
        }

        console.log(`🎨 Rendering ${routingType} routing diagram`);

        switch (routingType) {
            case 'overview':
                renderOverviewDiagram(container, routingGraph);
                break;
            case 'layers':
                renderLayerDiagram(container, routingGraph);
                break;
            case 'critical-paths':
                renderCriticalPathsDiagram(container, routingGraph);
                break;
            case 'navigation':
                renderNavigationDiagram(container, routingGraph);
                break;
            default:
                renderOverviewDiagram(container, routingGraph);
        }
    };

    const renderOverviewDiagram = (container, routingGraph) => {
        const { nodes, edges, entryPoints } = routingGraph;
        
        // Select key nodes for overview
        const keyNodes = [
            ...entryPoints.slice(0, 2),
            ...nodes.filter(n => n.isCritical).slice(0, 6),
            ...nodes.filter(n => n.type === 'api').slice(0, 3)
        ].slice(0, 10);

        const safeName = (name) => (name || 'Module').replace(/[^a-zA-Z0-9\s]/g, '').substring(0, 20);
        const nodeId = (node) => node.id.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 25);

        let mermaidCode = 'graph TD\n';
        
        // Add nodes
        keyNodes.forEach(node => {
            const id = nodeId(node);
            const name = safeName(node.name);
            const icon = getNodeIcon(node.type);
            const stats = `${node.functions}f/${node.classes}c`;
            
            mermaidCode += `    ${id}["${icon} ${name}\\n${stats}"]\n`;
        });

        // Add edges between key nodes
        const keyNodeIds = new Set(keyNodes.map(n => n.id));
        edges
            .filter(e => keyNodeIds.has(e.source) && keyNodeIds.has(e.target))
            .forEach(edge => {
                const sourceId = nodeId(keyNodes.find(n => n.id === edge.source));
                const targetId = nodeId(keyNodes.find(n => n.id === edge.target));
                mermaidCode += `    ${sourceId} --> ${targetId}\n`;
            });

        // Add styling
        mermaidCode += '\n';
        keyNodes.forEach(node => {
            const id = nodeId(node);
            const cssClass = getNodeCssClass(node.type);
            mermaidCode += `    class ${id} ${cssClass}\n`;
        });

        mermaidCode += `
    classDef entry fill:#fff8e1,stroke:#ffc107,stroke-width:3px,color:#000
    classDef api fill:#e8f5e8,stroke:#4caf50,stroke-width:2px,color:#000
    classDef service fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#000
    classDef data fill:#fce4ec,stroke:#e91e63,stroke-width:2px,color:#000
    classDef utility fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
    classDef module fill:#f5f5f5,stroke:#757575,stroke-width:2px,color:#000`;

        renderMermaidDiagram(container, mermaidCode, 
            `System Overview: ${keyNodes.length} key modules with routing relationships`,
            createOverviewFallback(keyNodes)
        );
    };

    const renderLayerDiagram = (container, routingGraph) => {
        const { layers } = routingGraph;
        
        let mermaidCode = 'graph TD\n';
        
        // Create subgraphs for each layer
        Object.entries(layers).forEach(([layerName, nodes]) => {
            if (nodes.length === 0) return;
            
            const layerTitle = layerName.toUpperCase();
            const layerIcon = getLayerIcon(layerName);
            
            mermaidCode += `    subgraph ${layerTitle} ["${layerIcon} ${layerTitle} Layer"]\n`;
            
            nodes.slice(0, 4).forEach((node, i) => {
                const id = `${layerTitle}${i + 1}`;
                const name = (node.name || 'Module').substring(0, 15);
                const icon = getNodeIcon(node.type);
                
                mermaidCode += `        ${id}["${icon} ${name}\\n${node.score.toFixed(1)} score"]\n`;
            });
            
            mermaidCode += '    end\n';
        });

        // Add cross-layer connections
        const layerOrder = ['presentation', 'interface', 'application', 'business', 'data', 'infrastructure'];
        layerOrder.forEach((layer, i) => {
            if (i < layerOrder.length - 1 && layers[layer] && layers[layerOrder[i + 1]]) {
                mermaidCode += `    ${layer.toUpperCase()}1 --> ${layerOrder[i + 1].toUpperCase()}1\n`;
            }
        });

        renderMermaidDiagram(container, mermaidCode,
            `Architectural Layers: ${Object.keys(layers).length} layers with ${Object.values(layers).reduce((sum, nodes) => sum + nodes.length, 0)} modules`,
            createLayerFallback(layers)
        );
    };

    const renderCriticalPathsDiagram = (container, routingGraph) => {
        const { criticalPaths, nodes } = routingGraph;
        
        if (criticalPaths.length === 0) {
            container.innerHTML = '<div class="info-message">No critical paths detected</div>';
            return;
        }

        const topPaths = criticalPaths.slice(0, 3);
        let mermaidCode = 'graph LR\n';
        
        topPaths.forEach((pathInfo, pathIndex) => {
            const { path } = pathInfo;
            
            path.forEach((nodeId, i) => {
                const node = nodes.find(n => n.id === nodeId);
                if (!node) return;
                
                const id = `P${pathIndex}_${i}`;
                const name = (node.name || 'Module').substring(0, 12);
                const icon = getNodeIcon(node.type);
                
                mermaidCode += `    ${id}["${icon} ${name}"]\n`;
                
                if (i < path.length - 1) {
                    const nextId = `P${pathIndex}_${i + 1}`;
                    mermaidCode += `    ${id} --> ${nextId}\n`;
                }
            });
        });

        renderMermaidDiagram(container, mermaidCode,
            `Critical Paths: ${topPaths.length} most important execution flows`,
            createCriticalPathsFallback(topPaths, nodes)
        );
    };

    const renderNavigationDiagram = (container, routingGraph) => {
        const { navigationPaths } = routingGraph;
        
        if (!navigationPaths) {
            container.innerHTML = '<div class="info-message">Building navigation paths...</div>';
            return;
        }

        const pathsHtml = Object.entries(navigationPaths)
            .map(([pathKey, pathInfo]) => {
                const steps = pathInfo.steps.slice(0, 5); // Limit to 5 steps
                
                return `
                    <div class="navigation-path">
                        <h4>${pathInfo.title}</h4>
                        <p class="path-description">${pathInfo.description}</p>
                        <div class="path-steps">
                            ${steps.map((step, i) => `
                                <div class="path-step" onclick="navigateToModule('${step.node.id}')">
                                    <div class="step-number">${i + 1}</div>
                                    <div class="step-content">
                                        <div class="step-title">${getNodeIcon(step.node.type)} ${step.node.name}</div>
                                        <div class="step-reason">${step.reason}</div>
                                        <div class="step-stats">${step.node.functions}f/${step.node.classes}c</div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            })
            .join('');

        container.innerHTML = `
            <div class="navigation-paths">
                <h3>🗺️ Guided Navigation Paths</h3>
                ${pathsHtml}
            </div>
        `;
    };

    const getNodeIcon = (type) => {
        const icons = {
            'entry': '⚡',
            'api': '🌐',
            'service': '🧠',
            'data': '💾',
            'utility': '🛠️',
            'ui': '🎨',
            'test': '🧪',
            'module': '📦'
        };
        return icons[type] || '📦';
    };

    const getLayerIcon = (layer) => {
        const icons = {
            'presentation': '🎨',
            'interface': '🌐',
            'application': '⚡',
            'business': '🧠',
            'data': '💾',
            'infrastructure': '🛠️',
            'test': '🧪'
        };
        return icons[layer] || '📦';
    };

    const getNodeCssClass = (type) => {
        const classes = {
            'entry': 'entry',
            'api': 'api',
            'service': 'service',
            'data': 'data',
            'utility': 'utility',
            'ui': 'api',
            'test': 'utility',
            'module': 'module'
        };
        return classes[type] || 'module';
    };

    const renderMermaidDiagram = (container, mermaidCode, description, fallbackHtml) => {
        try {
            container.innerHTML = `
                <div class="diagram-section">
                    <p class="diagram-description">${description}</p>
                    <div class="mermaid-container">
                        <div class="mermaid">${mermaidCode}</div>
                    </div>
                </div>
            `;
            
            if (typeof mermaid !== 'undefined') {
                mermaid.init(undefined, container.querySelector('.mermaid'));
            }
        } catch (error) {
            console.warn('Mermaid rendering failed:', error);
            container.innerHTML = fallbackHtml;
        }
    };

    const createOverviewFallback = (keyNodes) => {
        return `
            <div class="fallback-diagram">
                <h3>🚀 System Overview</h3>
                <div class="nodes-grid">
                    ${keyNodes.map(node => `
                        <div class="node-card ${node.type}" onclick="navigateToModule('${node.id}')">
                            <div class="node-icon">${getNodeIcon(node.type)}</div>
                            <div class="node-name">${node.name}</div>
                            <div class="node-stats">${node.functions}f/${node.classes}c</div>
                            <div class="node-type">${node.type}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    };

    const createLayerFallback = (layers) => {
        return `
            <div class="fallback-diagram">
                <h3>🏗️ Architectural Layers</h3>
                <div class="layers-grid">
                    ${Object.entries(layers).map(([layer, nodes]) => `
                        <div class="layer-card">
                            <h4>${getLayerIcon(layer)} ${layer.toUpperCase()}</h4>
                            <div class="layer-count">${nodes.length} modules</div>
                            <div class="layer-modules">
                                ${nodes.slice(0, 3).map(node => `
                                    <div class="layer-module" onclick="navigateToModule('${node.id}')">
                                        ${getNodeIcon(node.type)} ${node.name}
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    };

    const createCriticalPathsFallback = (paths, nodes) => {
        return `
            <div class="fallback-diagram">
                <h3>🎯 Critical Paths</h3>
                <div class="paths-list">
                    ${paths.map((pathInfo, i) => `
                        <div class="critical-path">
                            <h4>Path ${i + 1} (Weight: ${pathInfo.weight.toFixed(1)})</h4>
                            <div class="path-flow">
                                ${pathInfo.path.map((nodeId, j) => {
                                    const node = nodes.find(n => n.id === nodeId);
                                    return node ? `
                                        <div class="path-node" onclick="navigateToModule('${nodeId}')">
                                            ${getNodeIcon(node.type)} ${node.name}
                                        </div>
                                        ${j < pathInfo.path.length - 1 ? '<div class="path-arrow">→</div>' : ''}
                                    ` : '';
                                }).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    };

    // Navigation helper
    const navigateToModule = (moduleId) => {
        console.log('🧭 Navigating to module:', moduleId);
        
        // Get recommendations for this module
        const recommendations = RoutingSystem.getNavigationRecommendations(moduleId);
        
        // Show module details with routing context
        if (typeof ModuleRenderer !== 'undefined' && ModuleRenderer.showModuleModal) {
            ModuleRenderer.showModuleModal(moduleId);
        }
        
        // Update navigation recommendations if there's a recommendations panel
        updateNavigationRecommendations(moduleId, recommendations);
    };

    const updateNavigationRecommendations = (currentModuleId, recommendations) => {
        const panel = document.getElementById('navigation-recommendations');
        if (!panel || recommendations.length === 0) return;

        panel.innerHTML = `
            <div class="recommendations-panel">
                <h4>🧭 Where to go next</h4>
                <div class="recommendations-list">
                    ${recommendations.map(rec => `
                        <div class="recommendation" onclick="navigateToModule('${rec.node.id}')">
                            <div class="rec-icon">${getNodeIcon(rec.node.type)}</div>
                            <div class="rec-content">
                                <div class="rec-name">${rec.node.name}</div>
                                <div class="rec-reason">${rec.reason}</div>
                            </div>
                            <div class="rec-priority">P${rec.priority}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    };

    return {
        renderRoutingDiagram,
        navigateToModule,
        updateNavigationRecommendations
    };
})();

// Auto-render routing diagrams when data is loaded
document.addEventListener('repositoryDataLoaded', (event) => {
    // Wait a bit for routing system to initialize
    setTimeout(() => {
        // Render different routing diagrams based on available containers
        RoutingVisualizer.renderRoutingDiagram('routing-overview-diagram', 'overview');
        RoutingVisualizer.renderRoutingDiagram('routing-layers-diagram', 'layers');
        RoutingVisualizer.renderRoutingDiagram('routing-critical-paths-diagram', 'critical-paths');
        RoutingVisualizer.renderRoutingDiagram('routing-navigation-diagram', 'navigation');
    }, 1000);
});

// Export for global access
window.RoutingVisualizer = RoutingVisualizer;
window.navigateToModule = RoutingVisualizer.navigateToModule;
