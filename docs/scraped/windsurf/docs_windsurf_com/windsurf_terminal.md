# Source: https://docs.windsurf.com/windsurf/terminal

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

- Command in the terminal
- Send terminal selection to Cascade
- @-mention your terminal
- Auto-executed Cascade commands
- Turbo Mode
- Allow list
- Deny list
- Dedicated terminal
- Troubleshooting

# ​Command in the terminal

Use our
[Command](https://docs.windsurf.com/command/overview)
modality in the terminal (
`Cmd/Ctrl+I`
) to generate the proper CLI syntax from prompts in natural language.

# ​Send terminal selection to Cascade

Highlight a portion of of the stack trace and press
`Cmd/Ctrl+L`
to send it to Cascade, where you can reference this selection in your next prompt.

# ​@-mention your terminal

Chat with Cascade about your active terminals.

# ​Auto-executed Cascade commands

Cascade has the ability to run terminal commands on its own with user permission. However, certain terminal commands can be accepted or rejected automatically through the Allow and Deny lists.
By enabling Auto mode, it will rely on Cascade’s judgement on whether the command requires the user’s permission to be executed. This feature is only available for messages sent with premium models.

### ​Turbo Mode

In Turbo mode, Cascade will always execute the command, unless it is in the deny list.
You can toggle this via the Windsurf - Settings panel in the bottom right hand corner of the editor.

### ​Allow list

An allow list defines a set of terminal commands that will always auto-execute. For example, if you add
`git`
, then Cascade will always accept
`git add -A`
.
The setting can be via Command Palette → Open Settings (UI) → Search for
`windsurf.cascadeCommandsAllowList`
.

### ​Deny list

A deny list defines a set of terminal commands that will never auto-execute. For example, if you add
`rm`
, then Cascade will always ask for permission to run
`rm index.py`
.
The setting can be via Command Palette → Open Settings (UI) → Search for
`windsurf.cascadeCommandsDenyList`
.

# ​Dedicated terminal

Starting in Wave 13, Windsurf introduced a dedicated terminal for Cascade to use for running commands on macOS.
This dedicated terminal is separate from your default terminal and
uses
`zsh`
as the shell.
The dedicated terminal
use your zsh configuration, so aliases and environment variables will be available from
`.zshrc`
and other zsh-specific files.
If you use a different shell instead of
`zsh`
, and want Windsurf to use shared environment variables, we recommend creating a shared configuration file that both shells can source.

### ​Troubleshooting

If you have issues with the dedicated terminal, you can revert to the legacy terminal by enabling the Legacy Terminal Profile option in Windsurf settings.
[Code Lenses](https://docs.windsurf.com/command/windsurf-related-features)
[Browser Previews](https://docs.windsurf.com/windsurf/previews)
Ctrl
+I
$
/$