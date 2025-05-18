// Create a Radial Bar Chart
function createRadialBarChart(selector, data, dimensions, selectionCallback) {
    // Clear any existing SVG
    d3.select(selector).selectAll("*").remove();
    
    // Set up dimensions
    const container = d3.select(selector).node().getBoundingClientRect();
    const width = container.width;
    const height = container.height;
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };
    const radius = Math.min(width, height) / 2 - Math.max(margin.top, margin.right, margin.bottom, margin.left);
    
    // Create SVG
    const svg = d3.select(selector)
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .append("g")
        .attr("transform", `translate(${width / 2}, ${height / 2})`);
    
    // Scale for angles
    const x = d3.scaleBand()
        .domain(data.map(d => d.category))
        .range([0, 2 * Math.PI])
        .padding(0.1);
    
    // Scale for radius
    const maxValue = d3.max(data, d => d.value);
    const y = d3.scaleRadial()
        .domain([0, maxValue])
        .range([0, radius]);
    
    // Add bars
    const bars = svg.selectAll(".bar")
        .data(data)
        .enter()
        .append("path")
        .attr("class", "bar")
        .attr("fill", d => getColor(d.category))
        .attr("d", d3.arc()
            .innerRadius(0)
            .outerRadius(d => y(d.value))
            .startAngle(d => x(d.category))
            .endAngle(d => x(d.category) + x.bandwidth())
            .padAngle(0.01)
            .padRadius(radius / 2)
        )
        .style("cursor", "pointer")
        .on("mouseover", function(event, d) {
            d3.select(this).attr("opacity", 0.8);
            showTooltip(event, `
                <strong>${d.category}</strong><br>
                ${dimensions.value}: ${d.value}
            `);
        })
        .on("mouseout", function() {
            d3.select(this).attr("opacity", 1);
            hideTooltip();
        })
        .on("click", function(event, d) {
            const isSelected = d3.select(this).classed("selected");
            d3.select(this).classed("selected", !isSelected);
            selectionCallback("radialBar", d.category, !isSelected);
        });
    
    // Add category labels
    svg.selectAll(".category-label")
        .data(data)
        .enter()
        .append("text")
        .attr("class", "category-label")
        .attr("x", d => {
            const angle = x(d.category) + x.bandwidth() / 2;
            const labelRadius = radius + 10;
            return Math.sin(angle) * labelRadius;
        })
        .attr("y", d => {
            const angle = x(d.category) + x.bandwidth() / 2;
            const labelRadius = radius + 10;
            return -Math.cos(angle) * labelRadius;
        })
        .text(d => d.category)
        .attr("text-anchor", "middle")
        .attr("font-size", "10px")
        .attr("transform", d => {
            const angle = x(d.category) + x.bandwidth() / 2;
            return `rotate(${angle * 180 / Math.PI - 90}, ${Math.sin(angle) * (radius + 10)}, ${-Math.cos(angle) * (radius + 10)})`;
        });
    
    // Add a tick for each value
    const yTicks = y.ticks(5);
    const yAxis = svg.selectAll(".y-axis")
        .data(yTicks)
        .enter()
        .append("g")
        .attr("class", "y-axis");
    
    // Add circles for y-axis ticks
    yAxis.append("circle")
        .attr("fill", "none")
        .attr("stroke", "#ddd")
        .attr("r", d => y(d));
    
    // Add tick labels
    yAxis.append("text")
        .attr("y", d => -y(d))
        .attr("dy", "0.35em")
        .attr("text-anchor", "middle")
        .attr("font-size", "8px")
        .text(d => d);
    
    // Function to update the chart based on selection
    function update(selectedItems) {
        svg.selectAll(".bar")
            .classed("selected", d => selectedItems.has(d.category))
            .attr("opacity", d => selectedItems.size === 0 || selectedItems.has(d.category) ? 1 : 0.3);
    }
    
    // Return the chart API
    return {
        update
    };
}