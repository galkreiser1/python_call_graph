const vscode = require("vscode");
const { exec } = require("child_process");
const vis = require("vis-network");
const fs = require("fs");
const path = require("path");

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
      console.log("editor: ", editor.document.fileName);
      if (!editor) {
        vscode.window.showInformationMessage("No Python file is open");
        return;
      }

      // const code = editor.document.getText();
      const filePath = editor.document.fileName;

      const scriptPath = vscode.Uri.joinPath(
        context.extensionUri,
        "scripts",
        "graph_builder.py"
      ).fsPath;

      exec(`python ${scriptPath} ${filePath}`, (error, stdout, stderr) => {
        if (error) {
          console.error(`exec error: ${error}`);
          return;
        }
        panel.webview.html = getWebviewContent(stdout, context);
      });

      panel.webview.onDidReceiveMessage(
        (message) => {
          if (message.command === "goto") {
            // Ensure the correct document is open and focused
            vscode.workspace
              .openTextDocument(editor.document.uri)
              .then((doc) => {
                vscode.window
                  .showTextDocument(doc, {
                    preserveFocus: false,
                    preview: false,
                  })
                  .then((editor) => {
                    const line = message.lineno - 1;
                    const pos = new vscode.Position(line, 0);
                    editor.selection = new vscode.Selection(pos, pos);
                    editor.revealRange(
                      new vscode.Range(pos, pos),
                      vscode.TextEditorRevealType.InCenter
                    );
                  });
              });
          } else if (message.command === "setBreakpoint") {
            vscode.workspace
              .openTextDocument(editor.document.uri)
              .then((doc) => {
                vscode.window
                  .showTextDocument(doc, {
                    preserveFocus: false,
                    preview: false,
                  })
                  .then((editor) => {
                    const line = message.lineno - 1;
                    const uri = editor.document.uri; // Get the URI of the current document
                    const range = new vscode.Range(
                      line,
                      0,
                      line,
                      editor.document.lineAt(line).text.length
                    );
                    const location = new vscode.Location(uri, range); // Create a Location object

                    const breakpoint = new vscode.SourceBreakpoint(location);
                    vscode.debug.addBreakpoints([breakpoint]);
                  });
              });
          }
        },
        undefined,
        context.subscriptions
      );
    }
  );

  context.subscriptions.push(disposable);
}

function getWebviewContent(graphData, context = null) {
  const graph = JSON.parse(graphData); // Parse the JSON data
  const nodes = graph.nodes;
  const edges = graph.links;

  //now we'll need to convert nodes and edges so they can fit into the vis.js network
  // look at the comment above to see old format

  nodes.forEach((node) => {
    console.log(node.id + " starts at line: " + node.lineno);
  });

  const visNodes = nodes.map((node) => ({
    id: node.id,
    label: node.id,
    group: node.type,
    lineno: node.lineno,
  }));
  const visEdges = edges.map((edge) => ({
    from: edge.source,
    to: edge.target,
    label: edge.type,
    arrows: "to",
  }));

  // Read the HTML template file
  const templatePath = vscode.Uri.joinPath(
    context.extensionUri,
    "frontend",
    "template.html"
  ).fsPath;
  let template = fs.readFileSync(templatePath, "utf8");

  // Replace placeholders with actual data
  template = template.replace("{{nodes}}", JSON.stringify(visNodes));
  template = template.replace("{{edges}}", JSON.stringify(visEdges));

  return template;
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

  exec("pip install networkx", (error, stdout, stderr) => {
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
