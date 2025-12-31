# Source: https://docs.windsurf.com/windsurf/recommended-plugins

---

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

- General
- Security
- Languages
- Python
- Java
- Visual Basic
- C# / .NET
- C++

Windsurf, being a fork of VS Code, is easy to adopt for developers from VS, Eclipse, or VS Code. It uses the Open VSX Registry for extensions, accessible via the Extensions panel or website.
To help you get the most out of Windsurf for different programming languages, we’ve compiled a list of popular, community-recommended extensions from the Open VSX marketplace that other users have found helpful for replicating familiar IDE experiences.
Be sure to check out the full Open VSX marketplace for other useful extensions that may suit your specific workflow needs!

# ​General

Essential extensions that enhance your development workflow regardless of programming language:

- GitLens- Visualize code authorship at a glance via annotations and CodeLens
- GitHub Pull Requests- Review and manage your GitHub pull requests and issues directly
- GitLab Workflow- GitLab integration extension
- Mermaid Markdown Preview- Adds diagram and flowchart support
- Visual Studio Keybindings- Use Visual Studio keyboard shortcuts in Windsurf
- Eclipse Keymap- Use Eclipse keyboard shortcuts in Windsurf

## ​Security

Security-focused extensions to help identify vulnerabilities and maintain code quality:

- SonarQube for IDE- provides powerful code quality and security analysis. It helps you identify and fix bugs, vulnerabilities, and code smellsFor additional SonarQube functionality, you can also integrate the SonarQube MCP server with Cascade. Configure the SonarQube MCP Server through the Windsurf MCP Store or by following theSonarQube MCP server documentation.
- Snyk Security- Easily find and fix issues in your code, open source dependencies, infrastructure as code configurations with fast and accurate scans
- Checkmarx One- Comprehensive security scanning for identifying vulnerabilities in code, open source dependencies, and IaC files with real-time remediation insights. See the officialCheckmarx One Installation Guidefor more information.

# ​Languages

Language-specific extensions to enhance your development experience with comprehensive tooling and IntelliSense support.

## ​Python

- ms-python.python- Core Python support: IntelliSense, linting, debugging, and virtual environment management
- Windsurf Pyright- Fast, Pylance-like language server with strong type-checking and completions
- Ruff- Linter and code formatter
- Python Debugger- Debugging support for Python applications

## ​Java

- Extension Pack for Java- Bundle of essential Java tools: editing, refactoring, debugging, and project support (includes all below)
- redhat.java- Core Java language server for IntelliSense, navigation, and refactoring
- Java debug- Adds full Java debugging with breakpoints, variable inspection, etc.
- Java Test Runner- Run/debug JUnit/TestNG tests inside the editor with a testing UI
- Maven- Maven support: manage dependencies, run goals, view project structure
- Gradle- Gradle support: task explorer, project insights, and CLI integration
- Java Project Manager- Visualize and manage Java project dependencies

## ​Visual Basic

- Visual Basic Support- Syntax highlighting, code snippets, bracket matching, code folding
- VB Script Support- VBScript editing support: syntax highlighting, code outline view
- C# support- OmniSharp-based language server with IntelliSense and debugging
- Solution Explorer- Manage .sln and .csproj files visually

## ​C# / .NET

- DotRush- A lightweight, high-performance alternative to OmniSharp with Roslyn-based IntelliSense, built-in debuggers for .NET Core and Unity, test explorer, and code decompilation. DotRush is a powerful standalone C# extension that provides all essential features and can replace OmniSharp and several other extensions below.
- C# support- OmniSharp-based language server with IntelliSense and debugging
- .Net Install Tool- Installs and manages different versions of the .NET SDK and Runtime
- Solution Explorer- Manage .sln and .csproj files visually
- C# Extensions- Enhances the VS Code experience by providing features like adding C# classes, interfaces, and enums, as well as generating constructors from properties
- Unity-tools- Unity-specific workflow helpers (snippets, docs, folder structure) for game development

## ​C++

- Clangd- Advanced code completion, syntax checking, and semantic highlighting. AST-based code navigation and symbol indexing
- Cmake tools- Manage CMake projects, build configurations, and debugging within VS Code. Automatically generates accurate compilation databases (compile_commands.json) for clangd
- Cmake- Offers syntax highlighting and basic editing features for CMakeLists.txt files
- C++ runner- Quickly compile and execute single-file or small projects within VS Code

Ctrl
+I
$
/$