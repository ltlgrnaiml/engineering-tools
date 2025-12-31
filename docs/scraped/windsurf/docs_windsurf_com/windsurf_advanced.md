# Source: https://docs.windsurf.com/windsurf/advanced

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

- Enabling Cascade access to .gitignore files
- SSH Support
- Dev Containers
- WSL (Beta)
- Extension Marketplace
- Windsurf Plugins

All advanced configurations can be found in Windsurf Settings which can be accessed by the top right dropdown → Windsurf Settings or Command Palette (Ctrl/⌘+Shift+P) → Open Windsurf Settings Page.

# ​Enabling Cascade access to .gitignore files

To provide Cascade with access to files that match patterns in your project’s .gitignore , go to your Windsurf Settings and go to “Cascade Gitignore Access”. By default, it is turned off. To provide access, turn it on by clicking the toggle.

# ​SSH Support

The usual SSH support in VSCode is licensed by Microsoft, so we have implemented our own just for Windsurf. It does require you to have
[OpenSSH](https://www.openssh.com/)
installed, but otherwise has minimal dependencies, and should “just work” like you’re used to. You can access SSH under
`Remote-SSH`
in the Command Palette, or via the
`Open a Remote Window`
button in the bottom left.
This extension has worked great for our internal development, but there are some known caveats and bugs:

- We currently only support SSHing into Linux-based remote hosts.
- The usual Microsoft “Remote - SSH” extension (and theopen-remote-sshextension) will not work—please do not install them, as they conflict with our support.
- We don’t have all the features of the Microsoft SSH extension right now. We mostly just support the important thing: connecting to a host. If you have feature requests, let us know!
- Connecting to a remote host via SSH then accessing a devcontainer on that remote host won’t work like it does in VSCode. (We’re working on it!) For now, if you want to do this, we recommend instead manually setting up an SSH daemon inside your devcontainer. Here is the set-up which we’ve found to work, but please be careful to make sure it’s right for your use-case.Inside the devcontainer, run this once (running multiple times may mess up yoursshd_config):CopyAsk AIsudo -s -- <<HEREsed -i '/SSO SSH Config START/Q' /etc/ssh/sshd_configecho "Port 2222" >> /etc/ssh/sshd_configssh-keygen -AHEREInside the devcontainer, run this in a terminal you keep alive (e.g. via tmux):CopyAsk AIsudo /usr/sbin/sshd -DThen just connect to your remote host via SSH in windsurf, but using the port 2222.
- SSH agent-forwarding is on by default, and will use Windsurf’s latest connection to that host. If you’re having trouble with it, try reloading the window to refresh the connection.
- On Windows, you’ll see somecmd.exewindows when it asks for your password. This is expected—we’ll get rid of them soon.
- If you have issues, please first make sure that you can ssh into your remote host using regularsshin a terminal. If the problem persists, include the output from theOutput > Remote SSH (Windsurf)tab in any bug reports!

# ​Dev Containers

Windsurf supports Development Containers on Mac, Windows, and Linux for both local and remote (via SSH) workflows.
Prerequisites:

- Local: Docker must be installed on your machine and accessible from the Windsurf terminal.
- Remote over SSH: Connect to a remote host using Windsurf Remote-SSH. Docker must be installed and accessible on the remote host (from the remote shell). Your project should include adevcontainer.jsonor equivalent config.

Available commands (in both local and remote windows):

1. Dev Containers: Open Folder in ContainerOpen a new workspace using a specifieddevcontainer.json.
2. Dev Containers: Reopen in ContainerReopen the current workspace in a new container defined by yourdevcontainer.json.
3. Dev Containers: Attach to Running ContainerAttach to an existing Docker container and connect your current workspace to it. If the container does not follow theDevelopment Container Specificaton, Windsurf will attempt best-effort detection of the remote user and environment.
4. Dev Containers: Reopen Folder LocallyWhen connected to a development container, disconnect and reopen the workspace on the local filesystem.
5. Dev Containers: Show Windsurf Dev Containers LogOpen the Dev Containers log output for troubleshooting.

These commands are available from the Command Palette and will also appear when you click the
`Open a Remote Window`
button in the bottom left (including when you are connected to a remote host via SSH).
Related:

- Remote Explorer: Focus on Dev Containers (Windsurf) View— quickly open the Dev Containers view.

# ​WSL (Beta)

As of version 1.1.0, Windsurf has beta support for Windows Subsystem for Linux. You must already have WSL set up and configured on your Windows machine.
You can access WSL by clicking on the
`Open a Remote Window`
button in the bottom left, or under
`Remote-WSL`
in the Command Palette.

# ​Extension Marketplace

You can change the marketplace you use to download extensions from. To do this, go to
`Windsurf Settings`
and modify the Marketplace URL settings under the
`General`
section.

## ​Windsurf Plugins

[Vibe and Replace](https://docs.windsurf.com/windsurf/vibe-and-replace)
[Overview](https://docs.windsurf.com/windsurf/cascade/cascade)
Ctrl
+I
$
/$