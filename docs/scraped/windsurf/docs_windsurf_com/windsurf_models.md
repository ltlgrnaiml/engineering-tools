# Source: https://docs.windsurf.com/windsurf/models

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

- SWE-1.5, swe-grep, SWE-1
- Bring your own key (BYOK)

In Cascade, you can easily switch between different models of your choosing.
Depending on the model you select, each of your input prompts will consume a different number of
[prompt credits](https://docs.windsurf.com/windsurf/cascade/usage)
.
Under the text input box, you will see a model selection dropdown menu containing the following models:
| Model | Credits | Free | Pro | Teams | Enterprise | Trial |
| SWE-1.5 | 0.5Promo pricing only available for a limited time |  |  |  |  |  |
| Claude Sonnet 4.5 | 2Promo pricing only available for a limited time |  |  |  | 3 |  |
| Claude Sonnet 4.5 (Thinking) | 3Promo pricing only available for a limited time |  |  |  | 4 |  |
| Claude Opus 4.5 | 4 |  |  |  | 6 |  |
| Claude Opus 4.5 (Thinking) | 5 |  |  |  | 8 |  |
| Claude Haiku 4.5 | 1 |  |  |  |  |  |
| Gemini 3.0 Pro (minimal) | 1 |  |  |  |  |  |
| Gemini 3.0 Pro (low) | 1 |  |  |  |  |  |
| Gemini 3.0 Pro (medium) | 1.5 |  |  |  |  |  |
| Gemini 3.0 Pro (high) | 2 |  |  |  |  |  |
| GPT-5.2 (No Reasoning) | 1 |  |  |  |  |  |
| GPT-5.2 (Low Reasoning) | 1 |  |  |  |  |  |

# ​SWE-1.5, swe-grep, SWE-1

Our SWE model family of in-house frontier models are built specifically for software engineering tasks.
Our latest frontier model, SWE-1.5, achieves near-SOTA performance in a fraction of the time.
Our in house models include:

- SWE-1.5: Our best agentic coding model we’ve released. Near Claude 4.5-level performance, at 13x the speed. Read ourresearch announcement.
- SWE-1: Our first agentic coding model. Achieved Claude 3.5-level performance at a fraction of the cost.
- SWE-1-mini: Powers passive suggestions in Windsurf Tab, optimized for real-time latency.
- swe-grep: Powers context retrieval andFast Context

# ​Bring your own key (BYOK)

This is only available to free and paid individual users.
For certain models, we allow users to bring their own API keys. In the model dropdown menu, individual users will see models labled with
`BYOK`
.
To input your API key, navigate to
[this page](https://windsurf.com/subscription/provider-api-keys)
in the subscription settings and add your key.
If you have not configured your API key, it will return an error if you try to use the BYOK model.
Currently, we only support BYOK for these models:

- Claude 4 Sonnet
- Claude 4 Sonnet (Thinking)
- Claude 4 Opus
- Claude 4 Opus (Thinking)

[C#, .NET, and CPP](https://docs.windsurf.com/windsurf/csharp-cpp)
[Tab](https://docs.windsurf.com/tab/overview)
Ctrl
+I