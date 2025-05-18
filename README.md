# Interactive Data Visualization Dashboard with D3.js

An interactive dashboard featuring multiple linked visualizations powered by D3.js. Upload your JSON data, configure dimensions, and explore relationships through dynamic charts.

## Features

- **4 Interactive Visualizations**:
  - **Radial Bar Chart**: Compare categorical values in a circular layout.
  - **Chord Diagram**: Reveal relationships and connections between entities.
  - **Force-Directed Graph**: Explore network relationships with dynamic physics simulation.
  - **Sunburst Chart**: Analyze hierarchical data with drill-down capability.
- **Cross-Chart Interaction**: Click elements to highlight related items across all visualizations.
- **Dynamic Data Loading**: Upload JSON files and configure dimensions in real-time.
- **Responsive Design**: Adapts to screen sizes with grid layouts.
- **Tooltips & Breadcrumbs**: Contextual information on hover and navigation.

1. **Upload Data**:
   - Click "Upload JSON Data" and select a properly formatted JSON file.
   - Supported data types: categorical, numerical, arrays, and nested objects.

2. **Configure Dimensions**:
   - Select appropriate dimensions for each visualization from dropdowns.
   - Add hierarchy levels for the sunburst chart using the "+ Add Level" button.

3. **Generate Dashboard**:
   - Click "Generate Dashboard" to render visualizations.

4. **Interact**:
   - Hover for tooltips
   - Click elements to filter/select across charts
   - Drag nodes in force-directed graph
   - Click sunburst segments to drill down

## Data Format Requirements

Sample JSON structure:
```json
[
  {
    "category": "A",
    "value": 42,
    "connections": ["B", "C"],
    "networkNodes": ["Node1", "Node2"],
    "hierarchy": {
      "level1": "Group1",
      "level2": "SubgroupA"
    }
  },
  {
    "category": "B",
    "value": 35,
    "connections": ["A", "D"],
    "networkNodes": ["Node2", "Node3"],
    "hierarchy": {
      "level1": "Group2",
      "level2": "SubgroupB"
    }
  }
]
```

## Dependencies

- [D3.js v7](https://d3js.org/)
- Modern browser (Chrome/Firefox/Edge recommended)

## Customization

Modify styles in `style.css` or extend functionality by editing:
- `radial_bar.js` - Radial bar chart logic
- `chord.js` - Chord diagram configuration
- `force_directed.js` - Network graph settings
- `sunburst.js` - Hierarchy visualization
- `dashboard.js` - Core application logic

