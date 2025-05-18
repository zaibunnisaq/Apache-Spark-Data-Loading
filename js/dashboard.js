// Global variables to store data and selected dimensions
let rawData = [];
let selectedData = null;
let colorScale = d3.scaleOrdinal(d3.schemeCategory10);
let selectedItems = new Set();
let charts = {
    radialBar: null,
    chord: null,
    forceDirected: null,
    sunburst: null
};

// DOM elements
const fileUpload = document.getElementById('file-upload');
const fileName = document.getElementById('file-name');
const dimensionSelector = document.getElementById('dimension-selector');
const dashboard = document.getElementById('dashboard');
const generateDashboardBtn = document.getElementById('generate-dashboard');
const addHierarchyLevelBtn = document.getElementById('add-hierarchy-level');

// Event listeners
document.addEventListener('DOMContentLoaded', initialize);

function initialize() {
    fileUpload.addEventListener('change', handleFileUpload);
    generateDashboardBtn.addEventListener('click', generateDashboard);
    addHierarchyLevelBtn.addEventListener('click', addSunburstHierarchyLevel);
}

// Handle file upload
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    fileName.textContent = file.name;
    
    try {
        const fileContent = await readFile(file);
        const jsonData = JSON.parse(fileContent);
        
        // Store the raw data
        rawData = Array.isArray(jsonData) ? jsonData : [jsonData];
        
        // Extract and populate dimension options
        populateDimensionOptions();
        
        // Show dimension selector
        dimensionSelector.classList.remove('hidden');
        dashboard.classList.add('hidden');
    } catch (error) {
        console.error('Error processing file:', error);
        alert('Error processing the file. Please ensure it is a valid JSON file.');
    }
}

// Read file as text
function readFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = event => resolve(event.target.result);
        reader.onerror = error => reject(error);
        reader.readAsText(file);
    });
}

// Extract and populate dimension options
function populateDimensionOptions() {
    // Get all possible dimensions from the data
    const dimensions = extractDimensions(rawData);
    
    // Clear all select elements
    document.querySelectorAll('select').forEach(select => {
        select.innerHTML = '';
    });
    
    // Populate dimension options for each chart
    populateRadialBarOptions(dimensions);
    populateChordOptions(dimensions);
    populateForceDirectedOptions(dimensions);
    populateSunburstOptions(dimensions);
}

// Extract dimensions from data
function extractDimensions(data) {
    const dimensions = {};
    
    data.forEach(item => {
        Object.entries(item).forEach(([key, value]) => {
            // Skip arrays and nested objects for basic options
            if (!Array.isArray(value) && typeof value !== 'object') {
                if (!dimensions[key]) {
                    dimensions[key] = { type: typeof value, isNumeric: typeof value === 'number' };
                }
            } 
            // Handle arrays specifically
            else if (Array.isArray(value)) {
                if (!dimensions[key]) {
                    dimensions[key] = { type: 'array', isNumeric: false };
                }
            }
            // Handle objects (like monthly data)
            else if (typeof value === 'object') {
                if (!dimensions[key]) {
                    dimensions[key] = { type: 'object', isNumeric: Object.values(value).every(v => typeof v === 'number') };
                }
            }
        });
    });
    
    return dimensions;
}

// Populate radial bar chart options
function populateRadialBarOptions(dimensions) {
    const categorySelect = document.getElementById('radial-category');
    const valueSelect = document.getElementById('radial-value');
    
    // Add category options (all dimensions)
    Object.keys(dimensions).forEach(dim => {
        const option = document.createElement('option');
        option.value = dim;
        option.textContent = dim;
        categorySelect.appendChild(option);
    });
    
    // Add value options (only numeric dimensions)
    Object.entries(dimensions).forEach(([dim, props]) => {
        if (props.isNumeric) {
            const option = document.createElement('option');
            option.value = dim;
            option.textContent = dim;
            valueSelect.appendChild(option);
        }
    });
    
    // Add monthly object options for value if they exist
    Object.entries(dimensions).forEach(([dim, props]) => {
        if (props.type === 'object' && props.isNumeric) {
            const option = document.createElement('option');
            option.value = `${dim}:sum`;
            option.textContent = `Sum of ${dim}`;
            valueSelect.appendChild(option);
        }
    });
}

// Populate chord diagram options
function populateChordOptions(dimensions) {
    const categorySelect = document.getElementById('chord-category');
    const connectionsSelect = document.getElementById('chord-connections');
    
    // Add category options (all dimensions)
    Object.keys(dimensions).forEach(dim => {
        const option = document.createElement('option');
        option.value = dim;
        option.textContent = dim;
        categorySelect.appendChild(option);
    });
    
    // Add connections options (array fields)
    Object.entries(dimensions).forEach(([dim, props]) => {
        if (props.type === 'array') {
            const option = document.createElement('option');
            option.value = dim;
            option.textContent = dim;
            connectionsSelect.appendChild(option);
        }
    });
}

// Populate force-directed graph options
function populateForceDirectedOptions(dimensions) {
    const nodesSelect = document.getElementById('force-nodes');
    const linksSelect = document.getElementById('force-links');
    const strengthSelect = document.getElementById('force-strength');
    
    // Add nodes options (all dimensions)
    Object.keys(dimensions).forEach(dim => {
        const option = document.createElement('option');
        option.value = dim;
        option.textContent = dim;
        nodesSelect.appendChild(option);
    });
    
    // Add links options (array fields)
    Object.entries(dimensions).forEach(([dim, props]) => {
        if (props.type === 'array') {
            const option = document.createElement('option');
            option.value = dim;
            option.textContent = dim;
            linksSelect.appendChild(option);
        }
    });
    
    // Add strength options (numeric fields)
    Object.entries(dimensions).forEach(([dim, props]) => {
        if (props.isNumeric) {
            const option = document.createElement('option');
            option.value = dim;
            option.textContent = dim;
            strengthSelect.appendChild(option);
        }
    });
}

// Populate sunburst chart options
function populateSunburstOptions(dimensions) {
    const levelSelect = document.querySelector('.sunburst-level');
    const valueSelect = document.getElementById('sunburst-value');
    
    // Reset hierarchy levels
    const container = document.getElementById('sunburst-hierarchy-container');
    const levels = container.querySelectorAll('.sunburst-level');
    for (let i = 1; i < levels.length; i++) {
        container.removeChild(levels[i]);
    }
    
    // Add level options (all dimensions)
    Object.keys(dimensions).forEach(dim => {
        if (dim !== 'MonthlySales' && dim !== 'MonthlyConcerts') { // Skip complex objects for hierarchy
            const option = document.createElement('option');
            option.value = dim;
            option.textContent = dim;
            levelSelect.appendChild(option);
        }
    });
    
    // Add value options (numeric fields)
    Object.entries(dimensions).forEach(([dim, props]) => {
        if (props.isNumeric) {
            const option = document.createElement('option');
            option.value = dim;
            option.textContent = dim;
            valueSelect.appendChild(option);
        }
    });
}

// Add a new hierarchy level for sunburst
function addSunburstHierarchyLevel() {
    const container = document.getElementById('sunburst-hierarchy-container');
    const levels = container.querySelectorAll('.sunburst-level');
    const newLevel = document.createElement('select');
    
    newLevel.className = 'sunburst-level';
    newLevel.dataset.level = levels.length + 1;
    
    // Copy options from the first level
    const firstLevel = levels[0];
    Array.from(firstLevel.options).forEach(opt => {
        const option = document.createElement('option');
        option.value = opt.value;
        option.textContent = opt.textContent;
        newLevel.appendChild(option);
    });
    
    // Add before the button
    container.insertBefore(newLevel, addHierarchyLevelBtn);
}

// Generate dashboard based on selected dimensions
function generateDashboard() {
    // Get selected dimensions
    const dimensions = {
        radialBar: {
            category: document.getElementById('radial-category').value,
            value: document.getElementById('radial-value').value
        },
        chord: {
            category: document.getElementById('chord-category').value,
            connections: document.getElementById('chord-connections').value
        },
        forceDirected: {
            nodes: document.getElementById('force-nodes').value,
            links: document.getElementById('force-links').value,
            strength: document.getElementById('force-strength').value
        },
        sunburst: {
            hierarchy: Array.from(document.querySelectorAll('.sunburst-level')).map(select => select.value),
            value: document.getElementById('sunburst-value').value
        }
    };
    
    // Hide selector and show dashboard
    dimensionSelector.classList.add('hidden');
    dashboard.classList.remove('hidden');
    
    // Process data based on selected dimensions
    processData(dimensions);
    
    // Render charts
    renderCharts();
}

// Process data based on selected dimensions
function processData(dimensions) {
    // Store dimensions for later use
    selectedData = {
        dimensions: dimensions,
        radialBar: processRadialBarData(dimensions.radialBar),
        chord: processChordData(dimensions.chord),
        forceDirected: processForceDirectedData(dimensions.forceDirected),
        sunburst: processSunburstData(dimensions.sunburst)
    };
}

// Process data for radial bar chart
function processRadialBarData(dims) {
    const { category, value } = dims;
    const data = [];
    
    rawData.forEach(item => {
        // Handle sum of object values
        if (value.includes(':sum')) {
            const fieldName = value.split(':')[0];
            const sum = Object.values(item[fieldName]).reduce((a, b) => a + b, 0);
            data.push({
                category: item[category],
                value: sum,
                raw: item
            });
        } else {
            data.push({
                category: item[category],
                value: item[value],
                raw: item
            });
        }
    });
    
    return data;
}

// Process data for chord diagram
function processChordData(dims) {
    const { category, connections } = dims;
    const categories = [...new Set(rawData.map(item => item[category]))];
    const matrix = Array(categories.length).fill().map(() => Array(categories.length).fill(0));
    const nodeMap = {};
    
    // Create a map of categories to indices
    categories.forEach((cat, i) => {
        nodeMap[cat] = i;
    });
    
    // Build the matrix
    rawData.forEach(item => {
        const sourceIdx = nodeMap[item[category]];
        const connectionsList = item[connections] || [];
        
        connectionsList.forEach(conn => {
            // Find the target in the categories
            const targetItems = rawData.filter(d => d[category] === conn);
            if (targetItems.length > 0) {
                const targetIdx = nodeMap[conn];
                matrix[sourceIdx][targetIdx] += 1;
                // Making it bidirectional
                matrix[targetIdx][sourceIdx] += 1;
            }
        });
    });
    
    return {
        categories,
        matrix,
        nodeMap,
        raw: rawData
    };
}

function processForceDirectedData(dims) {
    const { nodes: nodeDim, links: linksDim, strength: strengthDim } = dims;
    
    // Calculate value range for scaling
    const values = rawData.map(d => d[strengthDim] || 0);
    const maxValue = d3.max(values);
    const minValue = d3.min(values);
    const valueRange = maxValue - minValue;

    // Create nodes with normalized sizes
    const nodeMap = new Map();
    const nodes = [];
    
    rawData.forEach(item => {
        const nodeId = item[nodeDim];
        if (!nodeMap.has(nodeId)) {
            const rawValue = item[strengthDim] || 0;
            const normalizedValue = valueRange > 0 
                ? (rawValue - minValue) / valueRange
                : 0.5;
            
            nodes.push({
                id: nodeId,
                radius: 10 + (normalizedValue * 20), // 10-30px radius
                rawValue: rawValue,
                raw: item
            });
            nodeMap.set(nodeId, nodeId);
        }
    });

    // Create links with valid references
    const links = [];
    rawData.forEach(item => {
        const source = item[nodeDim];
        const linksList = item[linksDim] || [];
        
        linksList.forEach(target => {
            if (nodeMap.has(source) && nodeMap.has(target)) {
                links.push({
                    source: source,
                    target: target,
                    value: 1
                });
            }
        });
    });

    return {
        nodes,
        links: links.filter(l => l.source && l.target),
        nodeMap,
        raw: rawData
    };
}

// Process data for sunburst chart
function processSunburstData(dims) {
    const { hierarchy, value } = dims;
    
    // Create hierarchical structure
    const root = {
        name: "root",
        children: []
    };
    
    // Function to find or create a node at the specified path
    function findOrCreateNode(path, parent) {
        if (path.length === 0) return parent;
        
        const [currentName, ...restPath] = path;
        let child = parent.children.find(c => c.name === currentName);
        
        if (!child) {
            child = { name: currentName, children: [] };
            parent.children.push(child);
        }
        
        return findOrCreateNode(restPath, child);
    }
    
    // Add each data point to the hierarchy
    rawData.forEach(item => {
        const path = hierarchy.map(h => item[h]);
        const leaf = findOrCreateNode(path, root);
        
        // If this is the last level, add the value
        leaf.value = item[value] || 0;
        leaf.raw = item;
    });
    
    return {
        root,
        raw: rawData
    };
}

// Render all charts
function renderCharts() {
    const { dimensions, radialBar, chord, forceDirected, sunburst } = selectedData;
    
    // Create charts
    charts.radialBar = createRadialBarChart(
        '#radial-chart', 
        radialBar, 
        dimensions.radialBar,
        handleSelection
    );
    
    charts.chord = createChordDiagram(
        '#chord-chart', 
        chord, 
        dimensions.chord,
        handleSelection
    );
    
    charts.forceDirected = createForceDirectedGraph(
        '#force-chart', 
        forceDirected, 
        dimensions.forceDirected,
        handleSelection
    );
    
    charts.sunburst = createSunburstChart(
        '#sunburst-chart', 
        sunburst, 
        dimensions.sunburst,
        handleSelection
    );
}

// Handle selection across charts
function handleSelection(type, selected, add = true) {
    if (add) {
        selectedItems.add(selected);
    } else {
        selectedItems.delete(selected);
    }
    
    // Update all charts with selected items
    updateCharts();
}

// Clear all selections
function clearSelection() {
    selectedItems.clear();
    updateCharts();
}

// Update all charts based on selection
function updateCharts() {
    Object.values(charts).forEach(chart => {
        if (chart && chart.update) {
            chart.update(selectedItems);
        }
    });
}

// Show tooltip
function showTooltip(event, content) {
    const tooltip = document.getElementById('tooltip');
    tooltip.style.visibility = 'visible';
    tooltip.style.opacity = 1;
    tooltip.innerHTML = content;
    
    // Position the tooltip
    const x = event.pageX + 10;
    const y = event.pageY + 10;
    tooltip.style.left = `${x}px`;
    tooltip.style.top = `${y}px`;
}

// Hide tooltip
function hideTooltip() {
    const tooltip = document.getElementById('tooltip');
    tooltip.style.visibility = 'hidden';
    tooltip.style.opacity = 0;
}

// Utility function to get a consistent color for an item
function getColor(key) {
    return colorScale(key);
}