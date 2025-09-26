/**
 * Routing System - Analyzes code relationships and creates navigation paths
 */
const RoutingSystem = (() => {
    let repositoryData = null;
    let routingGraph = null;
    let dependencyMap = null;

    const init = (data) => {
        repositoryData = data;
        console.log('🚀 Initializing Routing System with', data.modules?.length || 0, 'modules');
        
        buildDependencyMap();
        buildRoutingGraph();
        createNavigationPaths();
    };

    const buildDependencyMap = () => {
        console.log('🔍 Building dependency map...');
        dependencyMap = new Map();
        
        if (!repositoryData?.modules) return;

        repositoryData.modules.forEach(module => {
            const moduleId = module.path || module.name;
            if (!moduleId) return;

            const dependencies = {
                imports: [],
                exports: [],
                functions: [],
                classes: [],
                calledBy: [],
                calls: []
            };

            // Analyze imports
            if (module.imports) {
                dependencies.imports = Array.isArray(module.imports) 
                    ? module.imports 
                    : Object.keys(module.imports);
            }

            // Analyze functions
            if (module.functions) {
                dependencies.functions = Array.isArray(module.functions)
                    ? module.functions.map(f => typeof f === 'string' ? f : f.name)
                    : Object.keys(module.functions);
            }

            // Analyze classes
            if (module.classes) {
                dependencies.classes = Array.isArray(module.classes)
                    ? module.classes.map(c => typeof c === 'string' ? c : c.name)
                    : Object.keys(module.classes);
            }

            // Analyze exports (functions + classes that can be imported by others)
            dependencies.exports = [
                ...dependencies.functions,
                ...dependencies.classes
            ];

            dependencyMap.set(moduleId, {
                module,
                dependencies,
                score: calculateModuleScore(module),
                type: classifyModuleType(module),
                layer: determineArchitecturalLayer(module)
            });
        });

        // Build cross-references (who calls whom)
        buildCrossReferences();
    };

    const calculateModuleScore = (module) => {
        const functions = module.stats?.functions || module.functions?.length || 0;
        const classes = module.stats?.classes || module.classes?.length || 0;
        const lines = module.stats?.lines || module.lines_of_code || 0;
        
        return functions * 2 + classes * 5 + Math.min(lines / 100, 10);
    };

    const classifyModuleType = (module) => {
        const path = (module.path || '').toLowerCase();
        const name = (module.name || '').toLowerCase();
        const content = path + ' ' + name;

        if (/main|app|index|__init__|entry|bootstrap/.test(content)) return 'entry';
        if (/api|server|router|endpoint|controller|handler/.test(content)) return 'api';
        if (/service|manager|processor|engine|core/.test(content)) return 'service';
        if (/model|schema|entity|data|db|database/.test(content)) return 'data';
        if (/util|helper|tool|lib|common|config/.test(content)) return 'utility';
        if (/test|spec|mock/.test(content)) return 'test';
        if (/ui|view|component|render|display/.test(content)) return 'ui';
        
        return 'module';
    };

    const determineArchitecturalLayer = (module) => {
        const type = classifyModuleType(module);
        const layerMap = {
            'entry': 'application',
            'api': 'interface',
            'service': 'business',
            'data': 'data',
            'utility': 'infrastructure',
            'ui': 'presentation',
            'test': 'test',
            'module': 'business'
        };
        return layerMap[type] || 'business';
    };

    const buildCrossReferences = () => {
        console.log('🔗 Building cross-references...');
        
        // Find which modules are called by others based on imports and function usage
        dependencyMap.forEach((moduleInfo, moduleId) => {
            const { dependencies } = moduleInfo;
            
            dependencies.imports.forEach(importName => {
                // Find modules that export this import
                dependencyMap.forEach((otherModuleInfo, otherModuleId) => {
                    if (otherModuleId === moduleId) return;
                    
                    const { dependencies: otherDeps } = otherModuleInfo;
                    if (otherDeps.exports.some(exp => 
                        exp.toLowerCase().includes(importName.toLowerCase()) ||
                        importName.toLowerCase().includes(exp.toLowerCase())
                    )) {
                        dependencies.calls.push(otherModuleId);
                        otherDeps.calledBy.push(moduleId);
                    }
                });
            });
        });
    };

    const buildRoutingGraph = () => {
        console.log('📊 Building routing graph...');
        routingGraph = {
            nodes: [],
            edges: [],
            layers: {},
            entryPoints: [],
            criticalPaths: []
        };

        // Create nodes
        dependencyMap.forEach((moduleInfo, moduleId) => {
            const { module, dependencies, score, type, layer } = moduleInfo;
            
            const node = {
                id: moduleId,
                name: module.name || moduleId.split('/').pop(),
                path: module.path,
                type,
                layer,
                score,
                inDegree: dependencies.calledBy.length,
                outDegree: dependencies.calls.length,
                functions: dependencies.functions.length,
                classes: dependencies.classes.length,
                isEntryPoint: type === 'entry' || dependencies.calledBy.length === 0,
                isCritical: score > 10 || dependencies.calledBy.length > 3
            };

            routingGraph.nodes.push(node);

            // Group by layer
            if (!routingGraph.layers[layer]) {
                routingGraph.layers[layer] = [];
            }
            routingGraph.layers[layer].push(node);

            // Mark entry points
            if (node.isEntryPoint) {
                routingGraph.entryPoints.push(node);
            }
        });

        // Create edges
        dependencyMap.forEach((moduleInfo, moduleId) => {
            const { dependencies } = moduleInfo;
            
            dependencies.calls.forEach(targetId => {
                const sourceNode = routingGraph.nodes.find(n => n.id === moduleId);
                const targetNode = routingGraph.nodes.find(n => n.id === targetId);
                
                if (sourceNode && targetNode) {
                    routingGraph.edges.push({
                        source: moduleId,
                        target: targetId,
                        type: 'dependency',
                        weight: calculateEdgeWeight(sourceNode, targetNode)
                    });
                }
            });
        });

        // Find critical paths
        findCriticalPaths();
    };

    const calculateEdgeWeight = (sourceNode, targetNode) => {
        // Higher weight for more important connections
        let weight = 1;
        
        if (targetNode.type === 'entry') weight += 3;
        if (targetNode.type === 'api') weight += 2;
        if (targetNode.isCritical) weight += 2;
        if (sourceNode.layer !== targetNode.layer) weight += 1; // Cross-layer calls
        
        return weight;
    };

    const findCriticalPaths = () => {
        console.log('🎯 Finding critical paths...');
        
        // Find paths from entry points to critical modules
        routingGraph.entryPoints.forEach(entryPoint => {
            const paths = findPathsFromNode(entryPoint.id, 4); // Max depth of 4
            paths.forEach(path => {
                if (path.length > 2) { // Only paths with at least 3 nodes
                    routingGraph.criticalPaths.push({
                        path,
                        weight: path.reduce((sum, nodeId, i) => {
                            if (i === path.length - 1) return sum;
                            const edge = routingGraph.edges.find(e => 
                                e.source === nodeId && e.target === path[i + 1]
                            );
                            return sum + (edge?.weight || 1);
                        }, 0),
                        entryPoint: entryPoint.id
                    });
                }
            });
        });

        // Sort by weight (most important first)
        routingGraph.criticalPaths.sort((a, b) => b.weight - a.weight);
    };

    const findPathsFromNode = (startNodeId, maxDepth, visited = new Set(), currentPath = []) => {
        if (maxDepth <= 0 || visited.has(startNodeId)) {
            return [currentPath];
        }

        visited.add(startNodeId);
        currentPath.push(startNodeId);

        const outgoingEdges = routingGraph.edges.filter(e => e.source === startNodeId);
        
        if (outgoingEdges.length === 0) {
            const result = [currentPath.slice()];
            visited.delete(startNodeId);
            currentPath.pop();
            return result;
        }

        const allPaths = [];
        outgoingEdges.forEach(edge => {
            const subPaths = findPathsFromNode(
                edge.target, 
                maxDepth - 1, 
                new Set(visited), 
                currentPath.slice()
            );
            allPaths.push(...subPaths);
        });

        visited.delete(startNodeId);
        currentPath.pop();
        return allPaths;
    };

    const createNavigationPaths = () => {
        console.log('🗺️ Creating navigation paths...');
        
        if (!routingGraph) return;

        // Create navigation recommendations
        const navigationPaths = {
            quickStart: findQuickStartPath(),
            architecturalTour: findArchitecturalTour(),
            dataFlow: findDataFlowPath(),
            apiJourney: findApiJourney()
        };

        // Store for later use
        routingGraph.navigationPaths = navigationPaths;
    };

    const findQuickStartPath = () => {
        // Path for new developers: Entry -> Core -> Key Services
        const entryPoints = routingGraph.entryPoints.slice(0, 2);
        const coreModules = routingGraph.nodes
            .filter(n => n.type === 'service' || n.type === 'api')
            .sort((a, b) => b.score - a.score)
            .slice(0, 3);

        return {
            title: "🚀 Quick Start Path",
            description: "Essential modules for new developers",
            steps: [
                ...entryPoints.map(n => ({ node: n, reason: "Entry point" })),
                ...coreModules.map(n => ({ node: n, reason: "Core functionality" }))
            ]
        };
    };

    const findArchitecturalTour = () => {
        // One representative from each layer
        const layerRepresentatives = Object.entries(routingGraph.layers)
            .map(([layer, nodes]) => ({
                layer,
                node: nodes.sort((a, b) => b.score - a.score)[0]
            }))
            .filter(({ node }) => node);

        return {
            title: "🏗️ Architectural Tour",
            description: "Journey through each architectural layer",
            steps: layerRepresentatives.map(({ layer, node }) => ({
                node,
                reason: `${layer} layer representative`
            }))
        };
    };

    const findDataFlowPath = () => {
        // Follow data from input to output
        const dataModules = routingGraph.nodes.filter(n => n.type === 'data');
        const processingModules = routingGraph.nodes
            .filter(n => n.type === 'service')
            .sort((a, b) => b.score - a.score)
            .slice(0, 3);

        return {
            title: "📊 Data Flow Path",
            description: "How data moves through the system",
            steps: [
                ...dataModules.slice(0, 2).map(n => ({ node: n, reason: "Data source/sink" })),
                ...processingModules.map(n => ({ node: n, reason: "Data processing" }))
            ]
        };
    };

    const findApiJourney = () => {
        // API endpoints and their dependencies
        const apiModules = routingGraph.nodes
            .filter(n => n.type === 'api')
            .sort((a, b) => b.inDegree - a.inDegree); // Most called APIs first

        return {
            title: "🌐 API Journey",
            description: "Key API endpoints and integrations",
            steps: apiModules.slice(0, 4).map(n => ({
                node: n,
                reason: `API endpoint (${n.inDegree} callers)`
            }))
        };
    };

    // Public API for rendering and navigation
    const getRoutingGraph = () => routingGraph;
    const getDependencyMap = () => dependencyMap;
    
    const getModulesByType = (type) => {
        if (!routingGraph) return [];
        return routingGraph.nodes.filter(n => n.type === type);
    };

    const getModulesByLayer = (layer) => {
        if (!routingGraph) return [];
        return routingGraph.layers[layer] || [];
    };

    const findShortestPath = (sourceId, targetId) => {
        if (!routingGraph) return null;
        
        // Simple BFS for shortest path
        const queue = [{ id: sourceId, path: [sourceId] }];
        const visited = new Set();

        while (queue.length > 0) {
            const { id, path } = queue.shift();
            
            if (id === targetId) {
                return path;
            }

            if (visited.has(id)) continue;
            visited.add(id);

            const outgoingEdges = routingGraph.edges.filter(e => e.source === id);
            outgoingEdges.forEach(edge => {
                if (!visited.has(edge.target)) {
                    queue.push({
                        id: edge.target,
                        path: [...path, edge.target]
                    });
                }
            });
        }

        return null; // No path found
    };

    const getNavigationRecommendations = (currentModuleId) => {
        if (!routingGraph || !currentModuleId) return [];

        const currentModule = routingGraph.nodes.find(n => n.id === currentModuleId);
        if (!currentModule) return [];

        const recommendations = [];

        // Related modules in same layer
        const sameLayerModules = routingGraph.layers[currentModule.layer] || [];
        sameLayerModules
            .filter(n => n.id !== currentModuleId)
            .sort((a, b) => b.score - a.score)
            .slice(0, 2)
            .forEach(node => {
                recommendations.push({
                    node,
                    reason: `Same ${currentModule.layer} layer`,
                    priority: 2
                });
            });

        // Modules that call this one
        const callers = routingGraph.edges
            .filter(e => e.target === currentModuleId)
            .map(e => routingGraph.nodes.find(n => n.id === e.source))
            .filter(Boolean)
            .slice(0, 2);
        
        callers.forEach(node => {
            recommendations.push({
                node,
                reason: "Calls this module",
                priority: 3
            });
        });

        // Modules called by this one
        const called = routingGraph.edges
            .filter(e => e.source === currentModuleId)
            .map(e => routingGraph.nodes.find(n => n.id === e.target))
            .filter(Boolean)
            .slice(0, 2);
        
        called.forEach(node => {
            recommendations.push({
                node,
                reason: "Called by this module",
                priority: 3
            });
        });

        return recommendations
            .sort((a, b) => b.priority - a.priority)
            .slice(0, 5);
    };

    return {
        init,
        getRoutingGraph,
        getDependencyMap,
        getModulesByType,
        getModulesByLayer,
        findShortestPath,
        getNavigationRecommendations
    };
})();

// Listen for repository data
document.addEventListener('repositoryDataLoaded', (event) => {
    const data = event.detail;
    console.log('🚀 Initializing routing system...');
    RoutingSystem.init(data);
});

// Export for global access
window.RoutingSystem = RoutingSystem;
