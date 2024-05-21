const options = {
  nodes: {
    shape: "dot",
    size: 20,
    font: {
      size: 14,
      color: "#000000",
    },
  },
  edges: {
    font: {
      align: "middle",
    },
  },
  layout: {
    hierarchical: false,
  },
  physics: {
    enabled: true,
    barnesHut: {
      springLength: 200, // Adjust this value to make edges longer
    },
    forceAtlas2Based: {
      springLength: 200, // Adjust this value if using forceAtlas2Based
    },
    repulsion: {
      nodeDistance: 200, // Adjust this value to increase distance between nodes
    },
    hierarchicalRepulsion: {
      nodeDistance: 200, // Adjust this value if using hierarchical layout
    },
  },
};

export default options;
