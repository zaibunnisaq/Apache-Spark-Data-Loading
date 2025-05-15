// Create a Force-Directed Graph
function createForceDirectedGraph(selector, data, dimensions, selectionCallback) {
    // Clear any existing SVG
    d3.select(selector).selectAll("*").remove();
    
    // Extract data for the force-directed graph
    const { nodes, links, nodeMap, raw } = data;
    
    // Get container dimensions
    const container = d3.select(selector).node().getBoundingClientRect();
    const width = container.width;
    const height = container.height;
    
    // Create SVG with zoom support
    const svg = d3.select(selector)
        .append("svg")
        .attr("width", width)
        .attr("height", height);
    
    // Add zoom behavior
    const g = svg.append("g");
    
    svg.call(d3.zoom()
        .extent([[0, 0], [width, height]])
        .scaleExtent([0.1, 8])
        .on("zoom", (event) => {
            g.attr("transform", event.transform);
        })
    );
    
    // Create a force simulation
    const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id).distance(100))
        .force("charge", d3.forceManyBody().strength(-200))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collide", d3.forceCollide().radius(d => Math.sqrt(d.value) * 2 + 5));
    
    // Create links
    const link = g.append("g")
        .attr("class", "links")
        .selectAll("line")
        .data(links)
        .enter()
        .append("line")
        .attr("class", "link")
        .attr("stroke-width", d => Math.sqrt(d.value));
    
    // Create node groups
    const node = g.append("g")
        .attr("class", "nodes")
        .selectAll("g")
        .data(nodes)
        .enter()
        .append("g")
        .attr("class", "node")
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended)
        )
        .on("click", function(event, d) {
            const isSelected = d3.select(this).classed("selected");
            d3.select(this).classed("selected", !isSelected);
            selectionCallback("forceDirected", d.id, !isSelected);
            event.stopPropagation(); // Prevent zoom on click
        });
    
    // Add circles to node groups
    node.append("circle")
        .attr("r", d => Math.sqrt(d.value) * 2 + 5)
        .attr("fill", d => getColor(d.id))
        .attr("stroke", "#fff")
        .attr("stroke-width", 1.5)
        .on("mouseover", function(event, d) {
            d3.select(this).attr("opacity", 0.8);
            
            // Highlight connected links and nodes
            const connectedNodes = new Set();
            link.each(l => {
                if (l.source.id === d.id) connectedNodes.add(l.target.id);
                if (l.target.id === d.id) connectedNodes.add(l.source.id);
            });
            
            link.attr("opacity", l => 
                l.source.id === d.id || l.target.id === d.id ? 1 : 0.1
            );
            
            node.attr("opacity", n => 
                n.id === d.id || connectedNodes.has(n.id) ? 1 : 0.3
            );
            
            // Show tooltip
            showTooltip(event, `
                <strong>${d.id}</strong><br>
                Value: ${d.value.toFixed(2)}
            `);
        })
        .on("mouseout", function() {
            d3.select(this).attr("opacity", 1);
            link.attr("opacity", 1);
            node.attr("opacity", 1);
            hideTooltip();
        });
    
    // Add labels to node groups
    node.append("text")
        .attr("dy", -10)
        .attr("text-anchor", "middle")
        .text(d => d.id)
        .attr("font-size", "10px");
    
    // Update positions on tick
    simulation.on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);
        
        node
            .attr("transform", d => `translate(${d.x},${d.y})`);
    });
    
    // Drag functions
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
    
    // Function to update the chart based on selection
    function update(selectedItems) {
        if (selectedItems.size === 0) {
            node.attr("opacity", 1);
            link.attr("opacity", 1);
            return;
        }
        
        // Find connections between selected nodes
        const connectedNodes = new Set(selectedItems);
        
        // Expand connectedNodes to include neighbors of selected nodes
        selectedItems.forEach(selectedId => {
            links.forEach(l => {
                if (l.source.id === selectedId) connectedNodes.add(l.target.id);
                if (l.target.id === selectedId) connectedNodes.add(l.source.id);
            });
        });
        
        // Highlight nodes
        node.attr("opacity", d => connectedNodes.has(d.id) ? 1 : 0.3);
        
        // Highlight links
        link.attr("opacity", l => 
            (selectedItems.has(l.source.id) || selectedItems.has(l.target.id)) ? 1 : 0.1
        );
    }
    
    // Return the chart API
    return {
        update
    };
}