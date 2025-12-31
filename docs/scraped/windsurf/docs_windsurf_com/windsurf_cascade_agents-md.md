# Source: https://docs.windsurf.com/windsurf/cascade/agents-md

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

- How It Works
- Creating an AGENTS.md File
- Example Structure
- Example Content
- Discovery and Scoping
- Automatic Scoping
- Best Practices
- Content Guidelines
- Comparison with Rules

`AGENTS.md`
files provide a simple way to give Cascade context-aware instructions that automatically apply based on where the file is located in your project. This is particularly useful for providing directory-specific coding guidelines, architectural decisions, or project conventions.

## ​How It Works

When you create an
`AGENTS.md`
file (or
`agents.md`
), Windsurf automatically discovers it and uses its contents as instructions for Cascade. The behavior depends on where the file is placed:

- Root directory: When placed at the root of your workspace or git repository, the instructions apply globally to all files (similar to an “always on” rule)
- Subdirectories: When placed in a subdirectory, the instructions automatically apply only when working with files in that directory or its children

This location-based scoping makes
`AGENTS.md`
ideal for providing targeted guidance without cluttering a single global configuration file.

## ​Creating an AGENTS.md File

Simply create a file named
`AGENTS.md`
or
`agents.md`
in the desired directory. The file uses plain markdown with no special frontmatter required.

### ​Example Structure

Copy
Ask AI

```
my-project/
├── AGENTS.md                    # Global instructions for the entire project
├── frontend/
│   ├── AGENTS.md                # Instructions specific to frontend code
│   └── src/
│       └── components/
│           └── AGENTS.md        # Instructions specific to components
├── backend/
│   └── AGENTS.md                # Instructions specific to backend code
└── docs/
    └── AGENTS.md                # Instructions for documentation

```

### ​Example Content

Here’s an example
`AGENTS.md`
file for a React components directory:
Copy
Ask AI

```
# Component Guidelines

When working with components in this directory:

- Use functional components with hooks
- Follow the naming convention: ComponentName.tsx for components, useHookName.ts for hooks
- Each component should have a corresponding test file: ComponentName.test.tsx
- Use CSS modules for styling: ComponentName.module.css
- Export components as named exports, not default exports

## File Structure

Each component folder should contain:
- The main component file
- A test file
- A styles file (if needed)
- An index.ts for re-exports

```

## ​Discovery and Scoping

Windsurf automatically discovers
`AGENTS.md`
files throughout your workspace:

- Workspace scanning: AllAGENTS.mdfiles within your workspace and its subdirectories are discovered
- Git repository support: For git repositories, Windsurf also searches parent directories up to the git root
- Case insensitive: BothAGENTS.mdandagents.mdare recognized

### ​Automatic Scoping

The key benefit of
`AGENTS.md`
is automatic scoping based on file location:
| File Location | Scope |
| Workspace root | Applies to all files (always on) |
| /frontend/ | Applies when working with files in/frontend/** |
| /frontend/components/ | Applies when working with files in/frontend/components/** |

This means you can have multiple
`AGENTS.md`
files at different levels, each providing increasingly specific guidance for their respective directories.

## ​Best Practices

To get the most out of
`AGENTS.md`
files:

- Keep instructions focused: EachAGENTS.mdshould contain instructions relevant to its directory’s purpose
- Use clear formatting: Bullet points, headers, and code blocks make instructions easier for Cascade to follow
- Be specific: Concrete examples and explicit conventions work better than vague guidelines
- Avoid redundancy: Don’t repeat global instructions in subdirectory files; they inherit from parent directories

### ​Content Guidelines

Copy
Ask AI

```
# Good Example
- Use TypeScript strict mode
- All API responses must include error handling
- Follow REST naming conventions for endpoints

# Less Effective Example
- Write good code
- Be careful with errors
- Use best practices

```

## ​Comparison with Rules

While both
`AGENTS.md`
and
[Rules](https://docs.windsurf.com/windsurf/cascade/memories#rules)
provide instructions to Cascade, they serve different purposes:
| Feature | AGENTS.md | Rules |
| Location | In project directories | .windsurf/rules/or global |
| Scoping | Automatic based on file location | Manual (glob, always on, model decision, manual) |
| Format | Plain markdown | Markdown with frontmatter |
| Best for | Directory-specific conventions | Cross-cutting concerns, complex activation logic |

Use
`AGENTS.md`
when you want simple, location-based instructions. Use Rules when you need more control over when and how instructions are applied.
[Memories & Rules](https://docs.windsurf.com/windsurf/cascade/memories)
[Workflows](https://docs.windsurf.com/windsurf/cascade/workflows)
Ctrl
+I
$
/$