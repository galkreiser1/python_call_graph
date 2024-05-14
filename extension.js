const vscode = require("vscode");
const { exec } = require("child_process");
const vis = require("vis-network");
const fs = require("fs");

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
  let disposable = vscode.commands.registerCommand(
    "python-call-graph.showGraph",
    () => {
      const panel = vscode.window.createWebviewPanel(
        "graphVisualizer",
        "Graph Visualizer",
        vscode.ViewColumn.One,
        {
          enableScripts: true,
        }
      );

      // checkAndInstallDependencies();

      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showInformationMessage("No Python file is open");
        return;
      }

      // const code = editor.document.getText();
      const filePath = editor.document.fileName;

      const scriptPath = vscode.Uri.joinPath(
        context.extensionUri,
        "scripts",
        "ir_graph_builder.py"
      ).fsPath;

      exec(`python ${scriptPath} ${filePath}`, (error, stdout, stderr) => {
        if (error) {
          console.error(`exec error: ${error}`);
          return;
        }
        panel.webview.html = getWebviewContent(stdout);
      });
    }
  );

  context.subscriptions.push(disposable);
}

function getWebviewContent(graphData) {
  const graph = JSON.parse(graphData); // Parse the JSON data
  const nodes = graph.nodes;
  const edges = graph.links;

  try {
    nodes.forEach((item, index) => {
      console.log(`Item at index ${index}:`, item);
      // each item is a dict with type and id
    });
    edges.forEach((item, index) => {
      console.log(`Item at index ${index}:`, item);
      // each item is a dict with type, source and target
    });
  } catch (e) {
    console.log(e);
  }

  //now we'll need to convert nodes and edges so they can fit into the vis.js network
  // look at the comment above to see old format
  const visNodes = nodes.map((node) => ({
    id: node.id,
    label: node.id,
    group: node.type,
  }));
  const visEdges = edges.map((edge) => ({
    from: edge.source,
    to: edge.target,
    label: edge.type,
    arrows: "to",
  }));

  console.log("Vis nodes:", visNodes);
  console.log("Vis edges:", visEdges);

  return `
        <!DOCTYPE html>
        <html>
<head>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>

    <style type="text/css">
        #mynetwork {
            width: 600px;
            height: 400px;
            border: 1px solid lightgray;
        }
    </style>
</head>
<body>
<div id="mynetwork"></div>

<script type="text/javascript">
    // create an array with nodes
    var nodes = new vis.DataSet(${JSON.stringify(visNodes)});

    // create an array with edges
    var edges = new vis.DataSet(${JSON.stringify(visEdges)});

    // create a network
    var container = document.getElementById('mynetwork');

    // provide the data in the vis format
    var data = {
        nodes: nodes,
        edges: edges
    };
    var options = {};

    // initialize your network!
    var network = new vis.Network(container, data, options);
</script>
</body>
</html>
    `;
}

// This method is called when your extension is deactivated
function deactivate() {}

function checkAndInstallDependencies() {
  const pythonScript = `
import pkg_resources
required = {'networkx'}
installed = {pkg.key for pkg in pkg_resources.working_set}
missing = required - installed

print('Missing packages')
`;

  const dependencies = ["networkx", "astor"];

  exec("pip install astor", (error, stdout, stderr) => {
    if (error) {
      console.log("Error installing packages:", error);
      vscode.window.showErrorMessage(
        "Failed to install required packages. Please install manually."
      );
    } else {
      console.log("Packages installed successfully:", stdout);
      vscode.window.showInformationMessage(
        "All required packages installed successfully."
      );
    }
  });
}

module.exports = {
  activate,
  deactivate,
};
