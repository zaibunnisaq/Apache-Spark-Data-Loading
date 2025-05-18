// Create a Sunburst Chart
function createSunburstChart(selector, data, dimensions, selectionCallback) {
    // Clear any existing SVG
    d3.select(selector).selectAll("*").remove();
    
    // Extract data for the sunburst chart
    const { root: dataRoot, raw } = data;
    
    // Process data for d3 hierarchy
    const root = d3.hierarchy(dataRoot)
        .sum(d => d.value || 0);
    
    // Get container dimensions
    const container = d3.select(selector).node().getBoundingClientRect();
    const width = container.width;
    const height = container.height;
    const radius = Math.min(width, height) / 2;
    
    // Create container with breadcrumb
    const chartContainer = d3.select(selector)
        .append("div")
        .style("position", "relative")
        .style("width", "100%")
        .style("height", "100%");
    
    // Add breadcrumb for navigation
    const breadcrumb = chartContainer.append("div")
        .attr("id", "sunburst-breadcrumb")
        .style("padding", "5px")
        .style("font-size", "12px");
        
    updateBreadcrumb([{ name: "Home", node: root }]);
    
    // Create SVG
    const svg = chartContainer.append("svg")
        .attr("width", width)
        .attr("height", height - 30) // Subtract breadcrumb height
        .append("g")
        .attr("transform", `translate(${width / 2}, ${(height - 30) / 2})`);
    
    // Create a partition layout
    const partition = d3.partition()
        .size([2 * Math.PI, radius]);
    
    // Apply partition layout to hierarchy
    partition(root);
    
    // Track current view
    let currentRoot = root;
    
    // Create arc generator
    const arc = d3.arc()
        .startAngle(d => d.x0)
        .endAngle(d => d.x1)
        .innerRadius(d => d.y0)
        .outerRadius(d => d.y1);
    
    // Create slices
    const slices = svg.selectAll("path")
        .data(root.descendants().filter(d => d.depth)) // Skip root
        .enter()
        .append("path")
        .attr("class", "slice")
        .attr("d", arc)
        .style("fill", d => getColor(d.data.name))
        .style("stroke", "#fff")
        .style("stroke-width", 1)
        .style("opacity", 0.8)
        .on("mouseover", function(event, d) {
            d3.select(this).style("opacity", 1);
            
            // Show tooltip
            const tooltipContent = `
                <strong>${d.ancestors().map(node => node.data.name).reverse().join(" > ")}</strong><br>
                Value: ${d.value || 0}
            `;
            showTooltip(event, tooltipContent);
        })
        .on("mouseout", function() {
            d3.select(this).style("opacity", 0.8);
            hideTooltip();
        })
        .on("click", function(event, d) {
            // If click on leaf node, select it
            if (!d.children) {
                const isSelected = d3.select(this).classed("selected");
                d3.select(this).classed("selected", !isSelected);
                selectionCallback("sunburst", d.data.name, !isSelected);
                return;
            }
            
            // Otherwise zoom in
            zoom(d);
        });
    
    // Add labels for larger segments
    const labels = svg.selectAll("text")
        .data(root.descendants().filter(d => d.depth && (d.y1 - d.y0) * (d.x1 - d.x0) > 0.03))
        .enter()
        .append("text")
        .attr("transform", d => {
            const x = (d.x0 + d.x1) / 2;
            const y = (d.y0 + d.y1) / 2;
            const angle = x - Math.PI / 2;
            const radius = y;
            return `rotate(${angle * 180 / Math.PI})translate(${radius},0)rotate(${angle >= Math.PI ? 180 : 0})`;
        })
        .attr("dy", "0.35em")
        .attr("text-anchor", "middle")
        .attr("pointer-events", "none")
        .text(d => d.data.name)
        .attr("font-size", "10px")
        .style("fill", "#fff")
        .style("opacity", d => {
            // Only show labels for slices that are big enough
            return (d.y1 - d.y0) * (d.x1 - d.x0) > 0.05 ? 1 : 0;
        });
    
    // Function to zoom to a node
    function zoom(d) {
        currentRoot = d;
        
        // Transition to the new view
        const transition = svg.transition()
            .duration(750)
            .tween("scale", () => {
                const xd = d3.interpolate(arc.startAngle(), d => d.x0);
                const yd = d3.interpolate(arc.endAngle(), d => d.x1);
                const yr = d3.interpolate(arc.innerRadius(), d => d.y0);
                const yt = d3.interpolate(arc.outerRadius(), d => d.y1);
                
                return t => {
                    arc
                        .startAngle(xd(t))
                        .endAngle(yd(t))
                        .innerRadius(yr(t))
                        .outerRadius(yt(t));
                };
            });
        
        transition.selectAll("path")
            .attrTween("d", d => () => arc(d));
        
        transition.selectAll("text")
            .attr("transform", d => {
                const x = (d.x0 + d.x1) / 2;
                const y = (d.y0 + d.y1) / 2;
                const angle = x - Math.PI / 2;
                const radius = y;
                return `rotate(${angle * 180 / Math.PI})translate(${radius},0)rotate(${angle >= Math.PI ? 180 : 0})`;
            })
            .style("opacity", d => {
                // Hide labels that are not children of the current node
                const isVisible = d.ancestors().includes(currentRoot);
                if (!isVisible) return 0;
                
                // Only show labels for slices that are big enough
                return (d.y1 - d.y0) * (d.x1 - d.x0) > 0.05 ? 1 : 0;
            });
        
        // Update breadcrumb
        const ancestors = d.ancestors().reverse();
        const breadcrumbItems = ancestors.map(node => ({
            name: node.data.name,
            node: node
        }));
        
        updateBreadcrumb(breadcrumbItems);
    }
    
    // Function to update breadcrumb navigation
    function updateBreadcrumb(items) {
        breadcrumb.html("");
        
        items.forEach((item, i) => {
            breadcrumb.append("span")
                .attr("class", "breadcrumb-item")
                .text(item.name)
                .style("cursor", "pointer")
                .on("click", () => zoom(item.node));
            
            if (i < items.length - 1) {
                breadcrumb.append("span")
                    .text(" > ");
            }
        });
    }
    
    // Function to update the chart based on selection
    function update(selectedItems) {
        if (selectedItems.size === 0) {
            svg.selectAll(".slice").style("opacity", 0.8);
            return;
        }
        
        // Highlight selected paths and their ancestors
        svg.selectAll(".slice")
            .style("opacity", d => {
                // Check if this slice or any of its descendants is selected
                const isSelected = selectedItems.has(d.data.name) || 
                                    d.descendants().some(node => selectedItems.has(node.data.name));
                
                // Check if this slice is an ancestor of any selected item
                const isAncestor = Array.from(selectedItems).some(selectedName => {
                    const selectedNode = root.descendants().find(node => node.data.name === selectedName);
                    return selectedNode && selectedNode.ancestors().some(ancestor => ancestor.data.name === d.data.name);
                });
                
                return isSelected || isAncestor ? 1 : 0.3;
            });
    }
    
    // Return the chart API
    return {
        update
    };
}