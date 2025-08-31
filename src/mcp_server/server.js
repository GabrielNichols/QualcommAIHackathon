import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CapturePage } from "../tools/tools";

// Create an MCP server
const server = new McpServer({
  name: "tools-server",
  version: "1.0.0"
});

server.registerTool("extract-page-content",
  {
    title: "Extract Page Content",
    description: "Extract the text from an HTML page",
    inputSchema: { }
  },
  async () => ({
    content: [{ type: "text", text: await  CapturePage()}]
  })
);

const transport = new StdioServerTransport();
await server.connect(transport);