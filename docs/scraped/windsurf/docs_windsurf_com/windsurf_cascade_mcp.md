# Source: https://docs.windsurf.com/windsurf/cascade/mcp

---

- Discord Community
- Windsurf Blog
- Support

##### Editor

- Getting Started
- Models
- Tab
- Command
- Code Lenses
- Terminal
- Browser Previews
- AI Commit Messages
- DeepWiki
- Codemaps (Beta)
- Vibe and Replace
- Advanced

##### Cascade

- Overview
- App Deploys
- Web and Docs Search
- Memories & Rules
- AGENTS.md
- Workflows
- Model Context Protocol (MCP)
- Cascade Hooks

##### Accounts

- Usage
- Analytics
- Teams & Enterprise

##### Context Awareness

- Overview
- Fast Context
- Windsurf Ignore

##### Troubleshooting

- Common Issues
- Proxy Configuration
- Gathering Logs

##### Security

- Reporting

- Adding a new MCP plugin
- Configuring MCP tools
- mcp_config.json
- Admin Controls (Teams & Enterprises)
- How Server Matching Works
- Configuration Options
- Common Regex Patterns
- Notes
- Admin Configuration Guidelines
- Troubleshooting
- General Information

is a protocol that enables LLMs to access custom tools and services.
An MCP client (Cascade, in this case) can make requests to MCP servers to access tools that they provide.
Cascade now natively integrates with MCP, allowing you to bring your own selection of MCP servers for Cascade to use.
See the
[official MCP docs](https://modelcontextprotocol.io/)
for more information.
Enterprise users must manually turn this on via settings

## ​Adding a new MCP plugin

New MCP plugins can be added from the Plugin Store, which you can access by clicking on the
`Plugins`
icon in the top right menu in the Cascade panel, or from the
`Windsurf Settings`
>
`Cascade`
>
`Plugins`
section.
If you cannot find your desired MCP plugin, you can add it manually by editing the raw
`mcp_config.json`
file.
Official MCP plugins will show up with a blue checkmark, indicating that they are made by the parent service company.
When you click on a plugin, simply click
`Install`
to expose the server and its tools to Cascade.
Windsurf supports two
[transport types](https://modelcontextprotocol.io/docs/concepts/transports)
for MCP servers:
`stdio`
and
`http`
.
For
`http`
servers, the URL should reflect that of the endpoint and resemble
`https://<your-server-url>/mcp`
.
We can also support streamable HTTP transport and MCP Authentication.
Make sure to press the refresh button after you add a new MCP plugin.

## ​Configuring MCP tools

Each plugin has a certain number of tools it has access to. Cascade has a limit of 100 total tools that it has access to at any given time.
At the plugin level, you can navigate to the Tools tab and toggle the tools that you wish to enable. Or, from the
`Windsurf Settings`
, you can click on the
`Manage plugins`
button.

## ​mcp_config.json

The
`~/.codeium/windsurf/mcp_config.json`
file is a JSON file that contains a list of servers that Cascade can connect to.
The JSON should follow the same schema as the config file for Claude Desktop.
Here’s an example configuration, which sets up a single server for GitHub:
Copy
Ask AI

```
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<YOUR_PERSONAL_ACCESS_TOKEN>"
      }
    }
  }
}

```

It’s important to note that for HTTP servers, the configuration is slightly different and requires a
`serverUrl`
field.
Here’s an example configuration for an HTTP server:
Copy
Ask AI

```
{
  "mcpServers": {
    "figma": {
      "serverUrl": "<your-server-url>/mcp"
    }
  }
}

```

For Figma Dev Mode MCP server, make sure you have updated to the latest Figma desktop app version to use the new
`/mcp`
endpoint.
Be sure to provide the required arguments and environment variables for the servers that you want to use.
See the
[official MCP server reference repository](https://github.com/modelcontextprotocol/servers)
or
[OpenTools](https://opentools.com/)
for some example servers.

## ​Admin Controls (Teams & Enterprises)

Team admins can toggle MCP access for their team, as well as whitelist approved MCP servers for their team to use:
[MCP Team SettingsConfigurable MCP settings for your team.](https://windsurf.com/team/settings)
The above link will only work if you have admin privileges for your team.
By default, users within a team will be able to configure their own MCP servers. However, once you whitelist even a single MCP server,
for your team.

### ​How Server Matching Works

When you whitelist an MCP server, the system uses
with the following rules:

- Full String Matching: All patterns are automatically anchored (wrapped with^(?:pattern)$) to prevent partial matches
- Command Field: Must match exactly or according to your regex pattern
- Arguments Array: Each argument is matched individually against its corresponding pattern
- Array Length: The number of arguments must match exactly between whitelist and user config
- Special Characters: Characters like$,.,[,],(,)have special regex meaning and should be escaped with\if you want literal matching

### ​Configuration Options

### ​Common Regex Patterns

| Pattern | Matches | Example |
| .* | Any string | /home/user/script.py |
| [0-9]+ | Any number | 8080,3000 |
| [a-zA-Z0-9_]+ | Alphanumeric + underscore | api_key_123 |
| \\$HOME | Literal$HOME | $HOME(not expanded) |
| \\.py | Literal.py | script.py |
| \\[cli\\] | Literal[cli] | mcp[cli] |

## ​Notes

### ​Admin Configuration Guidelines

- Environment Variables: Theenvsection is not regex-matched and can be configured freely by users
- Disabled Tools: ThedisabledToolsarray is handled separately and not part of whitelist matching
- Case Sensitivity: All matching is case-sensitive
- Error Handling: Invalid regex patterns will be logged and result in access denial
- Testing: Test your regex patterns carefully - overly restrictive patterns may block legitimate use cases

### ​Troubleshooting

If users report that their MCP servers aren’t working after whitelisting:

1. Check Exact Matching: Ensure the whitelist pattern exactly matches the user’s configuration
2. Verify Regex Escaping: Special characters may need escaping (e.g.,\.for literal dots)
3. Review Logs: Invalid regex patterns are logged with warnings
4. Test Patterns: Use a regex tester to verify your patterns work as expected

Remember: Once you whitelist any server,
for your team members.

### ​General Information

- Since MCP tool calls can invoke code written by arbitrary server implementers, we do not assume liability
for MCP tool call failures. To reiterate:
- We currently support an MCP server’stools,resources, andprompts.

[Workflows](https://docs.windsurf.com/windsurf/cascade/workflows)
[Cascade Hooks](https://docs.windsurf.com/windsurf/cascade/hooks)
Ctrl
+I
$
/$