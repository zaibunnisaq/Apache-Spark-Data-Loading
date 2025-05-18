// Create a Chord Diagram
function createChordDiagram(selector, data, dimensions, selectionCallback) {
    // Clear any existing SVG
    d3.select(selector).selectAll("*").remove();
    
    // Extract data for the chord diagram
    const { categories, matrix, nodeMap, raw } = data;
    
    // Set up dimensions
    const container = d3.select(selector).node().getBoundingClientRect();
    const width = container.width;
    const height = container.height;
    const outerRadius = Math.min(width, height) * 0.4;
    const innerRadius = outerRadius - 20;
    
    // Create SVG
    const svg = d3.select(selector)
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .append("g")
        .attr("transform", `translate(${width / 2}, ${height / 2})`);
    
    // Create chord layout
    const chord = d3.chord()
        .padAngle(0.05)
        .sortSubgroups(d3.descending);
    
    // Compute the chord layout
    const chords = chord(matrix);
    
    // Create a group for each element
    const group = svg.append("g")
        .attr("class", "groups")
        .selectAll("g")
        .data(chords.groups)
        .enter()
        .append("g");
    
    // Add arcs for groups
    group.append("path")
        .attr("class", "arc")
        .attr("d", d3.arc()
            .innerRadius(innerRadius)
            .outerRadius(outerRadius)
        )
        .attr("fill", d => getColor(categories[d.index]))
        .attr("stroke", "#fff")
        .style("cursor", "pointer")
        .on("mouseover", function(event, d) {
            d3.select(this).attr("opacity", 0.8);
            
            // Highlight connected chords
            svg.selectAll(".chord")
                .attr("opacity", chord => {
                    return (chord.source.index === d.index || chord.target.index === d.index) ? 1 : 0.1;
                });
            
            // Show tooltip
            showTooltip(event, `<strong>${categories[d.index]}</strong>`);
        })
        .on("mouseout", function() {
            d3.select(this).attr("opacity", 1);
            svg.selectAll(".chord").attr("opacity", 0.8);
            hideTooltip();
        })
        .on("click", function(event, d) {
            const category = categories[d.index];
            const isSelected = d3.select(this).classed("selected");
            d3.select(this).classed("selected", !isSelected);
            selectionCallback("chord", category, !isSelected);
        });
    
    // Add labels for groups
    group.append("text")
        .attr("dy", ".35em")
        .attr("transform", d => {
            const angle = (d.startAngle + d.endAngle) / 2;
            const radius = outerRadius + 10;
            return `rotate(${angle * 180 / Math.PI - 90}) translate(${radius},0) ${angle > Math.PI ? "rotate(180)" : ""}`;
        })
        .attr("text-anchor", d => (d.startAngle + d.endAngle) / 2 > Math.PI ? "end" : "start")
        .text(d => {
            const name = categories[d.index];
            return name.length > 15 ? name.substring(0, 15) + "..." : name;
        })
        .attr("font-size", "10px");
    
    // Add chords
    svg.append("g")
        .attr("class", "chords")
        .selectAll("path")
        .data(chords)
        .enter()
        .append("path")
        .attr("class", "chord")
        .attr("d", d3.ribbon()
            .radius(innerRadius)
        )
        .attr("fill", d => getColor(categories[d.source.index]))
        .attr("stroke", "#fff")
        .attr("stroke-width", 0.5)
        .attr("opacity", 0.8)
        .on("mouseover", function(event, d) {
            d3.select(this).attr("opacity", 1);
            showTooltip(event, `
                <strong>${categories[d.source.index]}</strong> → 
                <strong>${categories[d.target.index]}</strong>
            `);
        })
        .on("mouseout", function() {
            d3.select(this).attr("opacity", 0.8);
            hideTooltip();
        });
    
    // Function to update the chart based on selection
    function update(selectedItems) {
        if (selectedItems.size === 0) {
            svg.selectAll(".arc").attr("opacity", 1);
            svg.selectAll(".chord").attr("opacity", 0.8);
            return;
        }
        
        // Get indices of selected categories
        const selectedIndices = Array.from(selectedItems)
            .map(item => categories.indexOf(item))
            .filter(index => index !== -1);
        
        // Highlight arcs of selected categories
        svg.selectAll(".arc")
            .attr("opacity", (d, i) => selectedIndices.includes(i) ? 1 : 0.3);
        
        // Highlight chords connected to selected categories
        svg.selectAll(".chord")
            .attr("opacity", d => {
                return selectedIndices.includes(d.source.index) || 
                       selectedIndices.includes(d.target.index) ? 0.8 : 0.1;
            });
    }
    
    // Return the chart API
    return {
        update
    };
}