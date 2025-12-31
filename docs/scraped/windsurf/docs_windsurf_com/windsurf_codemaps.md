# Source: https://docs.windsurf.com/windsurf/codemaps

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

- What are Codemaps?
- Accessing Codemaps
- Creating a Codemap
- Sharing Codemaps
- Using Codemaps with Cascade

Powered by a specialized agent, Codemaps are shareable artifacts that bridge the gap between human comprehension and AI reasoning, making it possible to navigate, discuss, and modify large codebases with precision and context.
Codemaps is currently in Beta and subject to change in future releases.

## ​What are Codemaps?

While
[DeepWiki](https://docs.windsurf.com/windsurf/deepwiki)
provides symbol-level documentation, Codemaps help with codebase understanding by mapping how everything works together—showing the order in which code and files are executed and how different components relate to each other.
To navigate a Codemap, click on any node to instantly jump to that file and function. Each node in the Codemap links directly to the corresponding location in your code.

## ​Accessing Codemaps

You can access Codemaps in one of two ways:

- Activity Bar: Find the Codemaps interface in the Activity Bar (left side panel)
- Command Palette: PressCmd+Shift+P(Mac) orCtrl+Shift+P(Windows/Linux) and search for “Focus on Codemaps View”

## ​Creating a Codemap

To create a new Codemap:

1. Open the Codemaps panel
2. Create a new Codemap by:Selecting a suggested topic (suggestions are based on your recent navigation history)Typing your own custom promptGenerating from Cascade: Create new Codemaps from the bottom of a Cascade conversation
3. The Codemap agent explores your repository, identify relevant files and functions, and generate a hierarchical view

## ​Sharing Codemaps

You can share Codemaps with teammates as links that can be viewed in a browser.
For enterprise customers, sharing Codemaps requires opt-in because they need to be stored on our servers. By default, Codemaps are only available within your Team and require authentication to view.

## ​Using Codemaps with Cascade

You can include Codemap information as context in your
[Cascade](https://docs.windsurf.com/windsurf/cascade)
conversations by using
`@-mention`
to reference a Codemap.
[DeepWiki](https://docs.windsurf.com/windsurf/deepwiki)
[Vibe and Replace](https://docs.windsurf.com/windsurf/vibe-and-replace)
Ctrl
+I
$
/$