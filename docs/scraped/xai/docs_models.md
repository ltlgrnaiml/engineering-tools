# Source: https://docs.x.ai/docs/models

---

#### [Key Information](https://docs.x.ai/docs/models#key-information)

# [Models and Pricing](https://docs.x.ai/docs/models#models-and-pricing)

An overview of our models' capabilities and their associated pricing.

## Grok 4.1 Fast

We’re excited to bring you Grok 4.1 Fast, a frontier multimodal model optimized specifically for high-performance agentic tool calling.

Modalities

Context window

2,000,000

Features

Function calling

Structured outputs

Reasoning

Lightning fast

Low cost

## [Model Pricing](https://docs.x.ai/docs/models#model-pricing)

| Model | Modalities | Capabilities | Context | Rate limits | Pricing |
| --- | --- | --- | --- | --- | --- |
|  |
| Language models |  | Per million tokens |
| grok-4-1-fast-reasoning |  |  | 2,000,000 | 4Mtpm480rpm | $0.20$0.50 |
| grok-4-1-fast-non-reasoning |  |  | 2,000,000 | 4Mtpm480rpm | $0.20$0.50 |
| grok-code-fast-1 |  |  | 256,000 | 2Mtpm480rpm | $0.20$1.50 |
| grok-4-fast-reasoning |  |  | 2,000,000 | 4Mtpm480rpm | $0.20$0.50 |
| grok-4-fast-non-reasoning |  |  | 2,000,000 | 4Mtpm480rpm | $0.20$0.50 |
| grok-4-0709 |  |  | 256,000 | 2Mtpm480rpm | $3.00$15.00 |
| grok-3-mini |  |  | 131,072 | 480rpm | $0.30$0.50 |
| grok-3 |  |  | 131,072 | 600rpm | $3.00$15.00 |
| grok-2-vision-1212 |  |  | 32,768 | 600rpm | $2.00$10.00 |
| Image generation models |  | Per image output |
| grok-2-image-1212 |  |  |  | 300rpm | $0.07 |

**Grok 4 Information for Grok 3 Users**
 When moving from `grok-3`/`grok-3-mini` to `grok-4`, please note the following differences:

- • Grok 4 is a reasoning model. There is no non-reasoning mode when using Grok 4.
- • `presencePenalty`, `frequencyPenalty` and `stop` parameters are not supported by reasoning models. Adding them in the request would result in an error.
- • Grok 4 does not have a `reasoning_effort` parameter. If a `reasoning_effort` is provided, the request will return an error.

## [Tools Pricing](https://docs.x.ai/docs/models#tools-pricing)

Requests which make use of xAI provided [server-side tools](https://docs.x.ai/docs/guides/tools/overview) are priced based on two components: **token usage** and **server-side tool invocations**. Since the agent autonomously decides how many tools to call, costs scale with query complexity.

### [Token Costs](https://docs.x.ai/docs/models#token-costs)

All standard token types are billed at the [rate](https://docs.x.ai/docs/models#model-pricing) for the model used in the request:

- **Input tokens**: Your query and conversation history
- **Reasoning tokens**: Agent's internal thinking and planning
- **Completion tokens**: The final response
- **Image tokens**: Visual content analysis (when applicable)
- **Cached prompt tokens**: Prompt tokens that were served from cache rather than recomputed

### [Tool Invocation Costs](https://docs.x.ai/docs/models#tool-invocation-costs)

| Tool | Cost per 1,000 calls | Description |
| --- | --- | --- |
| **Web Search** | $5 | Internet search and page browsing |
| **X Search** | $5 | X posts, users, and threads |
| **Code Execution** | $5 | Python code execution environment |
| **Document Search** | $5 | Search through uploaded files and documents |
| **View Image** | Token-based only | Image analysis within search results |
| **View X Video** | Token-based only | Video analysis within X posts |
| **Collections Search** | $2.50 | Knowledge base search using xAI Collections |
| **Remote MCP Tools** | Token-based only | Custom MCP tools |

For the view image and view x video tools, you will not be charged for the tool invocation itself but will be charged for the image tokens used to process the image or video.

For Remote MCP tools, you will not be charged for the tool invocation but will be charged for any tokens used.

For more information on using Tools, please visit [our guide on Tools](https://docs.x.ai/docs/guides/tools/overview).

## [Live Search Pricing](https://docs.x.ai/docs/models#live-search-pricing)

The advanced agentic search capabilities powering grok.com are generally available in the new [agentic tool calling API](https://docs.x.ai/docs/guides/tools/overview), and the Live Search API but will be deprecated by *January 12, 2026*.

Live Search costs $25 per 1,000 sources requested, each source used (Web, X, News, RSS) in a request counts toward the usage. That means a search using 4 sources costs $0.10 while a search using 1 source is $0.025. A source (e.g. Web) may return multiple citations, but you will be charged for only one source.

The number of sources used can be found in the `response` object, which contains a field called `response.usage.num_sources_used`.

For more information on using Live Search, visit our [guide on Live Search](https://docs.x.ai/docs/guides/live-search) or look for `search_parameters` parameter on [API Reference - Chat Completions](https://docs.x.ai/docs/api-reference#chat-completions).

## [Documents Search Pricing](https://docs.x.ai/docs/models#documents-search-pricing)

For users using our Collections API and Documents Search, the following pricing applies:

| Item | Price |
| --- | --- |
| Documents Search | $2.50/1k requests |

## [Usage Guidelines Violation Fee](https://docs.x.ai/docs/models#usage-guidelines-violation-fee)

A rare occurrence for most users, when your request is deemed to be in violation of our usage guideline by our system, we will charge a $0.05 per request usage guidelines violation fee.

## [Additional Information Regarding Models](https://docs.x.ai/docs/models#additional-information-regarding-models)

- **No access to realtime events without Live Search enabled** 
Grok has no knowledge of current events or data beyond what was present in its training data.
To incorporate realtime data with your request, please use Live Search function, or pass any realtime data as context in your system prompt.
- **Chat models** 
No role order limitation: You can mix system, user, or assistant roles in any sequence for your conversation context.
- **Image input models** 
Maximum image size: 20MiB
Maximum number of images: No limit
Supported image file types: jpg/jpeg or png.
Any image/text input order is accepted (e.g. text prompt can precede image prompt)
- Grok has no knowledge of current events or data beyond what was present in its training data.
- To incorporate realtime data with your request, please use [Live Search](https://docs.x.ai/docs/guides/live-search) function, or pass any realtime data as context in your system prompt.
- No role order limitation: You can mix `system`, `user`, or `assistant` roles in any sequence for your conversation context.
- Maximum image size: `20MiB`
- Maximum number of images: No limit
- Supported image file types: `jpg/jpeg` or `png`.
- Any image/text input order is accepted (e.g. text prompt can precede image prompt)

The knowledge cut-off date of Grok 3 and Grok 4 is November, 2024.

## [Model Aliases](https://docs.x.ai/docs/models#model-aliases)

Some models have aliases to help users automatically migrate to the next version of the same model. In general:

- `<modelname>` is aliased to the latest stable version.
- `<modelname>-latest` is aliased to the latest version. This is suitable for users who want to access the latest features.
- `<modelname>-<date>` refers directly to a specific model release. This will not be updated and is for workflows that demand consistency.

For most users, the aliased `<modelname>` or `<modelname>-latest` are recommended, as you would receive the latest features automatically.

## [Billing and Availability](https://docs.x.ai/docs/models#billing-and-availability)

Your model access might vary depending on various factors such as geographical location, account limitations, etc.

For how the **bills are charged**, visit [Manage Billing](https://docs.x.ai/docs/key-information/billing) for more information.

For the most up-to-date information on **your team's model availability**, visit [Models Page](https://console.x.ai/team/default/models) on xAI Console.

## [Model Input and Output](https://docs.x.ai/docs/models#model-input-and-output)

Each model can have one or multiple input and output capabilities. The input capabilities refer to which type(s) of prompt can the model accept in the request message body. The output capabilities refer to which type(s) of completion will the model generate in the response message body.

This is a prompt example for models with `text` input capability:

JSON

```
[
  {
    "role": "system",
    "content": "You are Grok, a chatbot inspired by the Hitchhiker's Guide to the Galaxy."
  },
  {
    "role": "user",
    "content": "What is the meaning of life, the universe, and everything?"
  }
]
```

This is a prompt example for models with `text` and `image` input capabilities:

JSON

```
[
  {
    "role": "user",
    "content": [
      {
        "type": "image_url",
        "image_url": {
          "url": "data:image/jpeg;base64,<base64_image_string>",
          "detail": "high"
        }
      },
      {
        "type": "text",
        "text": "Describe what's in this image."
      }
    ]
  }
]
```

This is a prompt example for models with `text` input and `image` output capabilities:

JSON

```
// The entire request body
{
  "model": "grok-4",
  "prompt": "A cat in a tree",
  "n": 4
}
```

## [Context Window](https://docs.x.ai/docs/models#context-window)

The context window determines the maximum amount of tokens accepted by the model in the prompt.

*For more information on how token is counted, visitConsumption and Rate Limits.*

If you are sending the entire conversation history in the prompt for use cases like chat assistant, the sum of all the prompts in your conversation history must be no greater than the context window.

## [Cached prompt tokens](https://docs.x.ai/docs/models#cached-prompt-tokens)

Trying to run the same prompt multiple times? You can now use cached prompt tokens to incur less cost on repeated prompts. By reusing stored prompt data, you save on processing expenses for identical requests. Enable caching in your settings and start saving today!

The caching is automatically enabled for all requests without user input. You can view the cached prompt token consumption in [the"usage"object](https://docs.x.ai/docs/key-information/consumption-and-rate-limits#checking-token-consumption).

For details on the pricing, please refer to the pricing table above, or on [xAI Console](https://console.x.ai).

- [Models and Pricing](https://docs.x.ai/docs/models#models-and-pricing)
- [Model Pricing](https://docs.x.ai/docs/models#model-pricing)
- [Tools Pricing](https://docs.x.ai/docs/models#tools-pricing)
- [Token Costs](https://docs.x.ai/docs/models#token-costs)
- [Tool Invocation Costs](https://docs.x.ai/docs/models#tool-invocation-costs)
- [Live Search Pricing](https://docs.x.ai/docs/models#live-search-pricing)
- [Documents Search Pricing](https://docs.x.ai/docs/models#documents-search-pricing)
- [Usage Guidelines Violation Fee](https://docs.x.ai/docs/models#usage-guidelines-violation-fee)
- [Additional Information Regarding Models](https://docs.x.ai/docs/models#additional-information-regarding-models)
- [Model Aliases](https://docs.x.ai/docs/models#model-aliases)
- [Billing and Availability](https://docs.x.ai/docs/models#billing-and-availability)
- [Model Input and Output](https://docs.x.ai/docs/models#model-input-and-output)
- [Context Window](https://docs.x.ai/docs/models#context-window)
- [Cached prompt tokens](https://docs.x.ai/docs/models#cached-prompt-tokens)