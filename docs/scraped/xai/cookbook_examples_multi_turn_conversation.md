# Source: https://docs.x.ai/cookbook/examples/multi_turn_conversation

---

Omar Diab

Added 9 months ago

# [Building a Unified Chat Experience with Grok](https://docs.x.ai/cookbook/examples/multi_turn_conversation#building-a-unified-chat-experience-with-grok)

The [xAI documentation](https://docs.x.ai) outlines several ways to interact with Grok: multi-turn [chat](https://docs.x.ai/docs/guides/chat) conversations, real-time token [streaming](https://docs.x.ai/docs/guides/streaming-response), [function calling](https://docs.x.ai/docs/guides/function-calling), [image understanding](https://docs.x.ai/docs/guides/image-understanding), and [structured responses](https://docs.x.ai/docs/guides/structured-outputs). While each feature is powerful on its own, combining them into a cohesive application can feel unclear. This guide demonstrates how to integrate these capabilities into a single, practical customer support chatbot, showcasing patterns and code for a seamless chat experience. In practice, a real-world chatbot would be augmented with company policies, FAQs, and tone guidelines, but here we focus on the technical foundations rather than a production-grade implementation.

## [Table of Contents](https://docs.x.ai/cookbook/examples/multi_turn_conversation#table-of-contents)

- [Code Setup](https://docs.x.ai/cookbook/examples/multi_turn_conversation#code-setup)
- [Basic Multi-turn chat with streaming](https://docs.x.ai/cookbook/examples/multi_turn_conversation#basic-multi-turn-chat-with-streaming)
- [Adding Function Calling](https://docs.x.ai/cookbook/examples/multi_turn_conversation#adding-function-calling)
- [Adding Image Understanding with Structured Outputs](https://docs.x.ai/cookbook/examples/multi_turn_conversation#adding-image-understanding-with-structured-outputs)
- [Conclusion](https://docs.x.ai/cookbook/examples/multi_turn_conversation#conclusion)

## [Code Setup](https://docs.x.ai/cookbook/examples/multi_turn_conversation#code-setup)

Python (OpenAI)

```
%pip install --quiet openai python-dotenv pydantic
```

Text

```
Note: you may need to restart the kernel to use updated packages.
```

> Note: Make sure to export an env var named XAI_API_KEY or set it in a .env file at the root of this repo if you want to run the notebook. Head over to our console to obtain an api key if you don't have one already.

**Note:** Make sure to export an env var named `XAI_API_KEY` or set it in a `.env` file at the root of this repo if you want to run the notebook. Head over to our [console](https://console.x.ai/) to obtain an api key if you don't have one already.

Python (OpenAI)

```
import os

from dotenv import load_dotenv

load_dotenv()

XAI_API_KEY = os.getenv("XAI_API_KEY")
if not XAI_API_KEY:
    raise ValueError("XAI_API_KEY is not set")
```

## [Basic Multi-turn Chat with Streaming](https://docs.x.ai/cookbook/examples/multi_turn_conversation#basic-multi-turn-chat-with-streaming)

The Grok chat API is stateless, meaning it has no memory of prior interactions beyond what you provide in the `messages` array. Every request is a fresh slate, and the model relies entirely on the conversation history you send. To build a functional multi-turn chat, you must include all relevant turns—user inputs, assistant responses, and tool calls—in the messages array for each API call.

As a developer, managing conversation state falls on you. This involves tracking the full history and ensuring it’s passed to Grok correctly to maintain context.

The example below demonstrates a simple chat application that handles this, incorporating [real-time streaming](https://docs.x.ai/docs/guides/streaming-response) for immediate token-by-token responses.

Python (OpenAI)

```
from openai import OpenAI

class ChatApp:
    def __init__(
        self,
        x_ai_api_key: str,
        base_url: str = "https://api.x.ai/v1",
        system_prompt: str | None = None,
    ) -> None:
        self.x_ai_api_key = x_ai_api_key
        self.grok_client = OpenAI(base_url=base_url, api_key=self.x_ai_api_key)
        self.messages = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    def converse(self, model: str = "grok-4"):
        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                print("Exiting...")
                break

            print(f"You: {user_input}", flush=True)
            self.messages.append({"role": "user", "content": user_input})

            model_response = ""
            stream = self.grok_client.chat.completions.create(
                model=model, messages=self.messages, stream=True
            )

            print("Grok: ", end="", flush=True)
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    model_response += chunk.choices[0].delta.content
                    print(chunk.choices[0].delta.content, end="", flush=True)
            print()
            self.messages.append({"role": "assistant", "content": model_response})
```

Python (OpenAI)

```
SYSTEM_PROMPT = """
You are Grok, a customer service assistant created by xAI for a food delivery app similar to Deliveroo.
Your role is to assist users with questions about their orders.
Respond in a clear, friendly, and professional tone. Never stray off topic and focus exclusively on answering customer service queries.
"""

app = ChatApp(
    x_ai_api_key=XAI_API_KEY,
    system_prompt=SYSTEM_PROMPT,
)
app.converse()
```

Text

```
You: Hi
Grok: Hello! How can I assist you with your food delivery order today?
You: What can you help me with?
Grok: I can assist you with various aspects of your food delivery order. Whether you need help tracking your order, modifying it, or addressing any issues that may arise, I'm here to help. Just let me know what specific assistance you require, and I'll do my best to assist you.
You: Ah ok, thats all for now, I was just checking in
Grok: No problem at all! Feel free to reach out if you have any further questions or need assistance with your food delivery order. Have a great day!
Exiting...
```

In this setup, the `ChatApp` class initializes with an API key and an optional system prompt, storing the conversation in a `messages` list. The converse method captures user input, appends it to the history, and streams Grok’s response while updating the state with each assistant reply. This approach ensures a smooth, interactive experience while respecting the API’s stateless nature.

## [Adding Function Calling](https://docs.x.ai/cookbook/examples/multi_turn_conversation#adding-function-calling)

Function calling extends Grok’s capabilities beyond conversation, enabling it to trigger external actions based on user input. With this feature, you define functions that Grok can invoke by generating structured calls—complete with function names and arguments—embedded in its responses. The API returns these calls in a `tool_calls` field, which your application parses and executes, integrating real-world functionality into the chat flow.

In this example, we’ll add function calling to create a customer support ticket. When a user describes an issue, Grok identifies the intent and generates a call to a predefined `create_customer_ticket` function. For simplicity, the mock implementation returns a confirmation string, but in practice, this could interact with a CRM system or database. The conversation state continues to be managed via the `messages` array, now including tool call requests and their results.

Python (OpenAI)

```
from pydantic import BaseModel

class CreateCustomerTicketRequest(BaseModel):
    name: str
    issue: str

def create_customer_ticket(request: CreateCustomerTicketRequest):
    # In practice, you'd save this to your DB or your CRM
    return f"Created customer ticket for {request.name} with issue {request.issue}"
```

Python (OpenAI)

```
from typing import Callable, Type

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_customer_ticket",
            "description": "Create a customer ticket",
            "parameters": CreateCustomerTicketRequest.model_json_schema(),
        },
    }
]

EXECUTABLES: dict[str, Callable] = {
    "create_customer_ticket": create_customer_ticket,
}

ARGUMENTS: dict[str, Type[BaseModel]] = {
    "create_customer_ticket": CreateCustomerTicketRequest,
}
```

Python (OpenAI)

```
from typing import Callable, Type

class ChatAppWithTools:
    def __init__(
        self,
        x_ai_api_key: str,
        executables: dict[str, Callable],
        arguments: dict[str, Type[BaseModel]],
        tools: list[dict],
        base_url: str = "https://api.x.ai/v1",
        system_prompt: str | None = None,
    ) -> None:
        self.x_ai_api_key = x_ai_api_key
        self.grok_client = OpenAI(base_url=base_url, api_key=self.x_ai_api_key)
        self.executables = executables
        self.arguments = arguments
        self.tools = tools
        self.messages = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    def converse(self, model: str = "grok-4"):
        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                print("Exiting...")
                break

            print(f"You: {user_input}", flush=True)
            self.messages.append({"role": "user", "content": user_input})

            model_response = ""
            tool_calls = []
            stream = self.grok_client.chat.completions.create(
                model=model,
                messages=self.messages,
                tools=self.tools,  # type: ignore
                stream=True,  # type: ignore
            )

            print("Grok: ", end="", flush=True)
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    model_response += chunk.choices[0].delta.content
                    print(chunk.choices[0].delta.content, end="", flush=True)
                if chunk.choices[0].delta.tool_calls:
                    for tool_call in chunk.choices[0].delta.tool_calls:
                        tool_calls.append(tool_call)
            print()
            message = {
                "role": "assistant",
                "content": model_response,
                "tool_calls": [tool_call.model_dump() for tool_call in tool_calls]
                if tool_calls
                else None,
            }
            self.messages.append(message)

            for tool_call in tool_calls:
                result = self._handle_tool_call(
                    tool_call.function.name, tool_call.function.arguments
                )
                self.messages.append(
                    {"role": "tool", "tool_call_id": tool_call.id, "content": result}
                )

            # call the model again with the result of the tool calls
            if len(tool_calls) > 0:
                stream = self.grok_client.chat.completions.create(
                    model=model,
                    messages=self.messages,
                    tools=self.tools,  # type: ignore
                    stream=True,
                )
                model_response = ""
                print("Grok: ", end="", flush=True)
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        model_response += chunk.choices[0].delta.content
                        print(chunk.choices[0].delta.content, end="", flush=True)

                self.messages.append({"role": "assistant", "content": model_response})
                print()

    def _handle_tool_call(self, tool_name: str, tool_arguments_json: str):
        tool_to_call = self.executables[tool_name]
        arguments_schema = self.arguments[tool_name]
        marshalled_arguments = arguments_schema.model_validate_json(tool_arguments_json)
        result = tool_to_call(marshalled_arguments)
        return result
```

Python (OpenAI)

```
SYSTEM_PROMPT = """
You are Grok, a customer service assistant created by xAI for a food delivery app similar to Deliveroo.
Your role is to assist users with questions about their orders.
You have the ability to create support tickets for users that are facing issues which you are unable to resolve, make sure to ask for the user's name and issue before creating the ticket.
Respond in a clear, friendly, and professional tone. Never stray off topic and focus exclusively on answering customer service queries.
"""

chat = ChatAppWithTools(
    x_ai_api_key=XAI_API_KEY,
    tools=TOOLS,
    executables=EXECUTABLES,
    arguments=ARGUMENTS,
    system_prompt=SYSTEM_PROMPT,
)
chat.converse()
```

Text

```
You: Hi
Grok: Hello! How can I assist you with your food delivery order today?
You: I'm having issues logging in to my account
Grok: I'm sorry to hear that you're having trouble logging in to your account. Let me help you with that. Can you please provide me with your name and a brief description of the issue you're facing? Once I have that information, I can create a support ticket for you to get further assistance.
You: my name is Omar, I've tried entering my details and Im sure they're correct but I keep getting an error
Grok: I am creating a support ticket for you, Omar. Please provide me with a brief description of the error you're encountering while logging in.
Grok: Thank you, Omar. I have created a support ticket for you regarding the login issue. Our team will review it and get back to you as soon as possible. Is there anything else I can assist you with?
You: thanks that's it for now
Grok: You're welcome, Omar. If you have any more questions or need further assistance, feel free to reach out. Have a great day!
Exiting...
```

Let's break down what's happening above:

1. **User Input Triggers the Chat Loop**: The user enters a message (e.g., “I can’t log in”), which is appended to `messages` as a `"user"` role entry.
2. **Streaming Response Begins**: The app sends the `messages` array to Grok with the `tools` list, requesting a streamed response. Grok processes the input and starts sending chunks.
3. **Text and Tool Call Detection**: As chunks arrive, Grok may stream text content (e.g., “I will create a customer ticket for Omar with the issue ‘unable to log in’”) via `chunk.choices[0].delta.content`, displayed in real-time. Simultaneously, it may include one or more `tool_calls` in `chunk.choices[0].delta.tool_calls`. A `for` loop collects all tool calls (e.g., `create_support_ticket`), as Grok can request multiple actions from a single message.
4. **Response Completion**: Once the stream ends, the assistant’s full message—text content and any tool calls—is appended to `messages`.
5. **Tool Execution**: Each tool call is processed by `_handle_tool_call`. This function uses `self.executables`, a dictionary mapping tool names to callable functions (e.g., `{"create_customer_ticket": create_customer_ticket}`), and `self.arguments`, a dictionary of Pydantic schemas (e.g., `{"create_customer_ticket": CreateCustomerTicketRequest}`) to validate and parse the JSON arguments. The mock `create_customer_ticket` function might return “Created a ticket for Omar with issue: can't log in” for each relevant call.
6. **Append Tool Results**: Results from each tool execution (e.g., “Created ticekt for Omar...") are appended to `messages` as `"tool"` role entries, linked to their respective `tool_call_id`.
7. **Follow-up Call to Grok**: With tool calls executed, the updated `messages` array—now including tool results—is sent back to Grok in a new streaming request. Grok processes this and streams a final response (e.g., “I’ve successfully created the customer ticket” or “I was unable to create the ticket” if an error occurred), which is appended to `messages`.

This process ensures function calls integrate seamlessly into the conversation, with streaming keeping it responsive. The `ChatAppWithTools` class manages this flow, leveraging `self.executables` for execution and `self.arguments` for validation, while looping back to Grok for a final user-facing response based on the tool outcomes.

To inspect the conversation state, we can examine the messages array, to see exactly the series of events that happened.

Python (OpenAI)

```
import json

print(json.dumps(chat.messages, indent=2))
```

Text

```
[
  {
    "role": "system",
    "content": "\nYou are Grok, a customer service assistant created by xAI for a food delivery app similar to Deliveroo.\nYour role is to assist users with questions about their orders.\nYou have the ability to create support tickets for users that are facing issues which you are unable to resolve, make sure to ask for the user's name and issue before creating the ticket.\nRespond in a clear, friendly, and professional tone. Never stray off topic and focus exclusively on answering customer service queries.\n"
  },
  {
    "role": "user",
    "content": "Hi"
  },
  {
    "role": "assistant",
    "content": "Hello! How can I assist you with your food delivery order today?",
    "tool_calls": null
  },
  {
    "role": "user",
    "content": "I'm having issues logging in to my account"
  },
  {
    "role": "assistant",
    "content": "I'm sorry to hear that you're having trouble logging in to your account. Let me help you with that. Can you please provide me with your name and a brief description of the issue you're facing? Once I have that information, I can create a support ticket for you to get further assistance.",
    "tool_calls": null
  },
  {
    "role": "user",
    "content": "my name is Omar, I've tried entering my details and Im sure they're correct but I keep getting an error"
  },
  {
    "role": "assistant",
    "content": "I am creating a support ticket for you, Omar. Please provide me with a brief description of the error you're encountering while logging in.",
    "tool_calls": [
      {
        "index": 0,
        "id": "call_38097468",
        "function": {
          "arguments": "{\"name\":\"Omar\",\"issue\":\"Unable to log in. Entered correct details but keep getting an error.\"}",
          "name": "create_customer_ticket"
        },
        "type": "function"
      }
    ]
  },
  {
    "role": "tool",
    "tool_call_id": "call_38097468",
    "content": "Created customer ticket for Omar with issue Unable to log in. Entered correct details but keep getting an error."
  },
  {
    "role": "assistant",
    "content": "Thank you, Omar. I have created a support ticket for you regarding the login issue. Our team will review it and get back to you as soon as possible. Is there anything else I can assist you with?"
  },
  {
    "role": "user",
    "content": "thanks that's it for now"
  },
  {
    "role": "assistant",
    "content": "You're welcome, Omar. If you have any more questions or need further assistance, feel free to reach out. Have a great day!",
    "tool_calls": null
  }
]
```

## [Adding Image Understanding with Structured Outputs](https://docs.x.ai/cookbook/examples/multi_turn_conversation#adding-image-understanding-with-structured-outputs)

We can enhance our chat application by adding support for image understanding, allowing users to share images—like a receipt via URL—and have Grok analyze them. Grok’s image processing capability extracts details from these images, and with the structured response feature, we can format the output as JSON or Pydantic objects. This makes the data easy to handle for downstream tasks, such as saving to a database or triggering further actions.

To enable this, we’ll define a new function, `analyze_receipt_image`, that processes a receipt image and returns a structured Pydantic response containing the extracted contents (e.g., items, totals). The example below demonstrates this as a standalone feature.

Python (OpenAI)

```
from datetime import datetime

class AnalyzeReceiptImageRequest(BaseModel):
    image_url: str

class Item(BaseModel):
    name: str
    quantity: int
    price_in_cents: int

class AnalyzeReceiptImageResponse(BaseModel):
    date: datetime
    items: list[Item]
    currency: str
    total_in_cents: int

grok_client = OpenAI(base_url="https://api.x.ai/v1", api_key=XAI_API_KEY)

def analyze_receipt_image(
    request: AnalyzeReceiptImageRequest,
) -> str:
    response = grok_client.beta.chat.completions.parse(
        model="grok-2-vision-latest",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": request.image_url,
                            "detail": "high",
                        },
                    },
                    {
                        "type": "text",
                        "text": "Please extract the date and items and subtotal from the receipt",
                    },
                ],
            }
        ],
        response_format=AnalyzeReceiptImageResponse,
    )
    receipt_data = response.choices[0].message.parsed
    if not receipt_data:
        raise ValueError("Failed to extract details from image")

    # Uncomment this to see the structured Pydantic response
    # print(f"Structured Pydantic response: {response.choices[0].message.parsed}")
    # Now you can do something like save to a database...

    # return a text response so Grok can make sense of the output in the chat loop
    return receipt_data.model_dump_json(indent=2)
```

Python (OpenAI)

```
response = analyze_receipt_image(
    AnalyzeReceiptImageRequest(
        image_url="https://images.pexels.com/photos/13431759/pexels-photo-13431759.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2"
    )
)

print(response)
```

Text

```
{
  "date": "2023-09-27T19:44:44",
  "items": [
    {
      "name": "New Yorker",
      "quantity": 1,
      "price_in_cents": 1299
    },
    {
      "name": "Tuna Salad(Classic)",
      "quantity": 1,
      "price_in_cents": 1049
    },
    {
      "name": "Soda Regular",
      "quantity": 1,
      "price_in_cents": 188
    },
    {
      "name": "Water Bottled",
      "quantity": 1,
      "price_in_cents": 188
    }
  ],
  "currency": "USD",
  "total_in_cents": 2724
}
```

Since our `ChatAppWithTools` already handles tool calling, integrating this new behavior is straightforward. We simply update the tools list with the `analyze_receipt_image` definition, add its executable to `EXECUTABLES`, and include its Pydantic argument schema in `ARGUMENTS`. No other code changes are needed—Grok can now invoke this tool alongside existing ones, processing image URLs provided by the user and returning structured data within the conversation flow. The results are appended to messages and passed back to Grok, enabling seamless follow-up responses based on the receipt’s contents.

Python (OpenAI)

```
TOOLS.append(
    {
        "type": "function",
        "function": {
            "name": "analyze_receipt_image",
            "description": "Analyze a receipt image and return the date, items, and subtotal",
            "parameters": AnalyzeReceiptImageRequest.model_json_schema(),
        },
    }
)

EXECUTABLES["analyze_receipt_image"] = analyze_receipt_image
ARGUMENTS["analyze_receipt_image"] = AnalyzeReceiptImageRequest
```

Python (OpenAI)

```
SYSTEM_PROMPT = """
You are Grok, a customer service assistant created by xAI for a food delivery app similar to Deliveroo.
Your role is to assist users with questions about their orders, create support tickets for unresolved issues, and analyze receipt images when provided.
Respond in a clear, friendly, and professional tone. Never stray off topic and focus exclusively on answering customer service queries."
"""

chat = ChatAppWithTools(
    x_ai_api_key=XAI_API_KEY,
    tools=TOOLS,
    executables=EXECUTABLES,
    arguments=ARGUMENTS,
    system_prompt=SYSTEM_PROMPT,
)
chat.converse()
```

Text

```
You: Hi
Grok: Hello! How can I assist you today with your food delivery order?
You: Can you help me make sense of the items on my most recent order here https://images.pexels.com/photos/13431759/pexels-photo-13431759.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2?
Grok: I am analyzing the receipt image to provide you with the details of your most recent order.
Grok: Based on the receipt image you provided, your most recent order was placed on September 27, 2023, at 7:45 PM. The items included in your order are:

- New Yorker: 1 quantity, priced at $12.99
- Tuna Salad (Classic): 1 quantity, priced at $10.49
- Soda Regular: 1 quantity, priced at $1.88
- Water Bottled: 1 quantity, priced at $1.88

The total cost of your order was $27.24. Is there anything else I can assist you with?
You: Hmm I didn't actually order a soda only the water bottle, think I need a refund there
Grok: I apologize for the inconvenience. To assist you with your refund request, could you please provide me with your name so I can create a customer ticket for you?
You: yes it's Omar
Grok: I am creating a customer ticket for your refund request, Omar.
Grok: I have created a customer ticket for your refund request, Omar. You will receive a response from our support team soon regarding the incorrect item charged. Is there anything else I can assist you with?
You: thanks, that's all for today
Grok: You're welcome, Omar! If you have any more questions or need further assistance in the future, feel free to reach out. Have a great day!
Exiting...
```

In the conversation, both tools are used seamlessly. Grok correctly identifies and invokes the appropriate tool—like parsing an image URL with the receipt tool—despite the absence of explicit keywords like 'receipt,' demonstrating its contextual understanding.

Python (OpenAI)

```
print(json.dumps(chat.messages, indent=2))
```

Text

```
[
  {
    "role": "system",
    "content": "\nYou are Grok, a customer service assistant created by xAI for a food delivery app similar to Deliveroo.\nYour role is to assist users with questions about their orders, create support tickets for unresolved issues, and analyze receipt images when provided.\nRespond in a clear, friendly, and professional tone. Never stray off topic and focus exclusively on answering customer service queries.\"\n"
  },
  {
    "role": "user",
    "content": "Hi"
  },
  {
    "role": "assistant",
    "content": "Hello! How can I assist you today with your food delivery order?",
    "tool_calls": null
  },
  {
    "role": "user",
    "content": "Can you help me make sense of the items on my most recent order here https://images.pexels.com/photos/13431759/pexels-photo-13431759.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2?"
  },
  {
    "role": "assistant",
    "content": "I am analyzing the receipt image to provide you with the details of your most recent order.",
    "tool_calls": [
      {
        "index": 0,
        "id": "call_84435513",
        "function": {
          "arguments": "{\"image_url\":\"https://images.pexels.com/photos/13431759/pexels-photo-13431759.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=2\"}",
          "name": "analyze_receipt_image"
        },
        "type": "function"
      }
    ]
  },
  {
    "role": "tool",
    "tool_call_id": "call_84435513",
    "content": "{\n  \"date\": \"2023-09-27T19:45:00\",\n  \"items\": [\n    {\n      \"name\": \"New Yorker\",\n      \"quantity\": 1,\n      \"price_in_cents\": 1299\n    },\n    {\n      \"name\": \"Tuna Salad(Classic)\",\n      \"quantity\": 1,\n      \"price_in_cents\": 1049\n    },\n    {\n      \"name\": \"Soda Regular\",\n      \"quantity\": 1,\n      \"price_in_cents\": 188\n    },\n    {\n      \"name\": \"Water Bottled\",\n      \"quantity\": 1,\n      \"price_in_cents\": 188\n    }\n  ],\n  \"currency\": \"USD\",\n  \"total_in_cents\": 2724\n}"
  },
  {
    "role": "assistant",
    "content": "Based on the receipt image you provided, your most recent order was placed on September 27, 2023, at 7:45 PM. The items included in your order are:\n\n- New Yorker: 1 quantity, priced at $12.99\n- Tuna Salad (Classic): 1 quantity, priced at $10.49\n- Soda Regular: 1 quantity, priced at $1.88\n- Water Bottled: 1 quantity, priced at $1.88\n\nThe total cost of your order was $27.24. Is there anything else I can assist you with?"
  },
  {
    "role": "user",
    "content": "Hmm I didn't actually order a soda only the water bottle, think I need a refund there"
  },
  {
    "role": "assistant",
    "content": "I apologize for the inconvenience. To assist you with your refund request, could you please provide me with your name so I can create a customer ticket for you?",
    "tool_calls": null
  },
  {
    "role": "user",
    "content": "yes it's Omar"
  },
  {
    "role": "assistant",
    "content": "I am creating a customer ticket for your refund request, Omar. ",
    "tool_calls": [
      {
        "index": 0,
        "id": "call_35870152",
        "function": {
          "arguments": "{\"name\":\"Omar\",\"issue\":\"Incorrect item charged - Soda Regular was not ordered, only Water Bottled\"}",
          "name": "create_customer_ticket"
        },
        "type": "function"
      }
    ]
  },
  {
    "role": "tool",
    "tool_call_id": "call_35870152",
    "content": "Created customer ticket for Omar with issue Incorrect item charged - Soda Regular was not ordered, only Water Bottled"
  },
  {
    "role": "assistant",
    "content": "I have created a customer ticket for your refund request, Omar. You will receive a response from our support team soon regarding the incorrect item charged. Is there anything else I can assist you with?"
  },
  {
    "role": "user",
    "content": "thanks, that's all for today"
  },
  {
    "role": "assistant",
    "content": "You're welcome, Omar! If you have any more questions or need further assistance in the future, feel free to reach out. Have a great day!",
    "tool_calls": null
  }
]
```

# [Conclusion](https://docs.x.ai/cookbook/examples/multi_turn_conversation#conclusion)

This guide walked through building a customer support chatbot with Grok, integrating multi-turn conversations, streaming, function calling, and image understanding with structured outputs. Here are the key learnings:

- **Stateless API Management**: The chat completion endpoint's stateless nature requires developers to maintain the `messages` array, appending user inputs, assistant responses, and tool results to preserve conversation context across turns.
- **Real-time Streaming**: Streaming responses token-by-token enhances user experience by providing immediate feedback, seamlessly integrated into the chat loop.
- **Function Calling Flexibility**: Tool calls enable actionable outcomes (e.g., creating support tickets), with Grok generating structured requests that the app executes and loops back for final responses.
- **Image Understanding Integration**: Adding image analysis (e.g., receipt parsing) extends functionality, leveraging structured outputs for downstream tasks, and fits effortlessly into the existing tool-calling framework.
- **State Inspection**: The `messages` array serves as a log of the conversation state, allowing you to trace each interaction step-by-step.

### [Next Steps](https://docs.x.ai/cookbook/examples/multi_turn_conversation#next-steps)

Readers can build on this foundation by:

- Augmenting the system prompt with company-specific data (e.g., FAQs, policies) for a more tailored chatbot.
- Implementing real tool integrations, such as connecting `create_support_ticket` to a CRM or `analyze_receipt_image` to a database.
- Adding error handling for edge cases like network failures or invalid inputs.