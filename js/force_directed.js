function createForceDirectedGraph(selector, data, dimensions, selectionCallback) {
    // Clear existing SVG
    d3.select(selector).selectAll("*").remove();

    // Validate data
    if (!data?.nodes?.length || !data?.links?.length) {
        console.error("Invalid graph data:", data);
        return { update: () => {} };
    }

    // Get container dimensions
    const container = d3.select(selector).node().getBoundingClientRect();
    const width = container.width;
    const height = container.height;

    // Create SVG
    const svg = d3.select(selector)
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .call(d3.zoom()
            .scaleExtent([0.1, 8])
            .on("zoom", (event) => {
                g.attr("transform", event.transform);
            }))
        .append("g");

    // Create force simulation
    const simulation = d3.forceSimulation(data.nodes)
        .force("link", d3.forceLink(data.links)
            .id(d => d.id)
            .distance(100)
            .strength(0.2))
        .force("charge", d3.forceManyBody().strength(-50))
        .force("center", d3.forceCenter(width/2, height/2))
        .force("collide", d3.forceCollide()
            .radius(d => d.radius + 5)
            .strength(0.8));

    // Create links
    const link = svg.append("g")
        .selectAll("line")
        .data(data.links)
        .join("line")
        .attr("class", "link")
        .attr("stroke", "#999")
        .attr("stroke-width", 1)
        .attr("stroke-opacity", 0.6);

    // Create nodes
    const node = svg.append("g")
        .selectAll("g")
        .data(data.nodes)
        .join("g")
        .attr("class", "node")
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended))
        .on("click", function(event, d) {
            const isSelected = d3.select(this).classed("selected");
            d3.select(this).classed("selected", !isSelected);
            selectionCallback("forceDirected", d.id, !isSelected);
            event.stopPropagation();
        });

    // Add circles with normalized sizing
    node.append("circle")
        .attr("r", d => d.radius)
        .attr("fill", d => getColor(d.id))
        .attr("stroke", "#fff")
        .attr("stroke-width", 2)
        .on("mouseover", showNodeDetails)
        .on("mouseout", hideNodeDetails);

    // Add labels
    node.append("text")
        .text(d => d.id)
        .attr("dy", -4)
        .attr("text-anchor", "middle")
        .attr("font-size", "10px")
        .attr("fill", "#333");

    // Simulation handler
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

    // Tooltip functions
    function showNodeDetails(event, d) {
        const connections = data.links
            .filter(l => l.source.id === d.id || l.target.id === d.id)
            .map(l => l.source.id === d.id ? l.target.id : l.source.id);

        showTooltip(event, `
            <strong>${d.id}</strong><br>
            ${dimensions.strength}: ${d.rawValue.toLocaleString()}<br>
            Connections: ${connections.length ? connections.join(', ') : 'None'}
        `);

        link.attr("stroke-opacity", l => 
            (l.source.id === d.id || l.target.id === d.id) ? 1 : 0.1
        );
    }

    function hideNodeDetails() {
        hideTooltip();
        link.attr("stroke-opacity", 0.6);
    }

    // Update function
    function update(selectedItems) {
        node.classed("selected", d => selectedItems.has(d.id))
            .attr("opacity", d => 
                selectedItems.size === 0 || selectedItems.has(d.id) ? 1 : 0.3
            );

        link.attr("opacity", l =>
            (selectedItems.has(l.source.id) || selectedItems.has(l.target.id)) ? 1 : 0.1
        );
    }

    return { update };
}