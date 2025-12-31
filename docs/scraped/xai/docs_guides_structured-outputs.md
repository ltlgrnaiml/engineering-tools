# Source: https://docs.x.ai/docs/guides/structured-outputs

---

#### [Guides](https://docs.x.ai/docs/guides/structured-outputs#guides)

# [Structured Outputs](https://docs.x.ai/docs/guides/structured-outputs#structured-outputs)

Structured Outputs is a feature that lets the API return responses in a specific, organized format, like JSON or other schemas you define. Instead of getting free-form text, you receive data that's consistent and easy to parse.

Ideal for tasks like document parsing, entity extraction, or report generation, it lets you define schemas using tools like [Pydantic](https://pydantic.dev/) or [Zod](https://zod.dev/) to enforce data types, constraints, and structure.

When using structured outputs, the LLM's response is **guaranteed** to match your input schema.

## [Supported models](https://docs.x.ai/docs/guides/structured-outputs#supported-models)

Structured outputs is supported by all language models later than `grok-2-1212` and `grok-2-vision-1212`.

## [Supported schemas](https://docs.x.ai/docs/guides/structured-outputs#supported-schemas)

For structured output, the following types are supported for structured output:

- string  
minLength and maxLength properties are not supported
- number  
integer
float
- object
- array  
minItems and maxItem properties are not supported
maxContains and minContains properties are not supported
- boolean
- enum
- anyOf
- `minLength` and `maxLength` properties are not supported
- integer
- float
- `minItems` and `maxItem` properties are not supported
- `maxContains` and `minContains` properties are not supported

`allOf` is not supported at the moment.

## [Example: Invoice Parsing](https://docs.x.ai/docs/guides/structured-outputs#example-invoice-parsing)

A common use case for Structured Outputs is parsing raw documents. For example, invoices contain structured data like vendor details, amounts, and dates, but extracting this data from raw text can be error-prone. Structured Outputs ensure the extracted data matches a predefined schema.

Let's say you want to extract the following data from an invoice:

- Vendor name and address
- Invoice number and date
- Line items (description, quantity, price)
- Total amount and currency

We'll use structured outputs to have Grok generate a strongly-typed JSON for this.

### [Step 1: Defining the Schema](https://docs.x.ai/docs/guides/structured-outputs#step-1-defining-the-schema)

You can use [Pydantic](https://pydantic.dev/) or [Zod](https://zod.dev/) to define your schema.

```
from datetime import date
from enum import Enum

from pydantic import BaseModel, Field

class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"

class LineItem(BaseModel):
    description: str = Field(description="Description of the item or service")
    quantity: int = Field(description="Number of units", ge=1)
    unit_price: float = Field(description="Price per unit", ge=0)

class Address(BaseModel):
    street: str = Field(description="Street address")
    city: str = Field(description="City")
    postal_code: str = Field(description="Postal/ZIP code")
    country: str = Field(description="Country")

class Invoice(BaseModel):
    vendor_name: str = Field(description="Name of the vendor")
    vendor_address: Address = Field(description="Vendor's address")
    invoice_number: str = Field(description="Unique invoice identifier")
    invoice_date: date = Field(description="Date the invoice was issued")
    line_items: list[LineItem] = Field(description="List of purchased items/services")
    total_amount: float = Field(description="Total amount due", ge=0)
    currency: Currency = Field(description="Currency of the invoice")
```

### [Step 2: Prepare The Prompts](https://docs.x.ai/docs/guides/structured-outputs#step-2-prepare-the-prompts)

### [System Prompt](https://docs.x.ai/docs/guides/structured-outputs#system-prompt)

The system prompt instructs the model to extract invoice data from text. Since the schema is defined separately, the prompt can focus on the task without explicitly specifying the required fields in the output JSON.

Text

```
Given a raw invoice, carefully analyze the text and extract the relevant invoice data into JSON format.
```

### [Example Invoice Text](https://docs.x.ai/docs/guides/structured-outputs#example-invoice-text)

Text

```
Vendor: Acme Corp, 123 Main St, Springfield, IL 62704
Invoice Number: INV-2025-001
Date: 2025-02-10
Items:
- Widget A, 5 units, $10.00 each
- Widget B, 2 units, $15.00 each
Total: $80.00 USD
```

### [Step 3: The Final Code](https://docs.x.ai/docs/guides/structured-outputs#step-3-the-final-code)

Use the structured outputs feature of the the SDK to parse the invoice.

```
import os
from datetime import date
from enum import Enum

from pydantic import BaseModel, Field

from xai_sdk import Client
from xai_sdk.chat import system, user

# Pydantic Schemas

class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"

class LineItem(BaseModel):
    description: str = Field(description="Description of the item or service")
    quantity: int = Field(description="Number of units", ge=1)
    unit_price: float = Field(description="Price per unit", ge=0)

class Address(BaseModel):
    street: str = Field(description="Street address")
    city: str = Field(description="City")
    postal_code: str = Field(description="Postal/ZIP code")
    country: str = Field(description="Country")

class Invoice(BaseModel):
    vendor_name: str = Field(description="Name of the vendor")
    vendor_address: Address = Field(description="Vendor's address")
    invoice_number: str = Field(description="Unique invoice identifier")
    invoice_date: date = Field(description="Date the invoice was issued")
    line_items: list[LineItem] = Field(description="List of purchased items/services")
    total_amount: float = Field(description="Total amount due", ge=0)
    currency: Currency = Field(description="Currency of the invoice")

client = Client(api_key=os.getenv("XAI_API_KEY"))
chat = client.chat.create(model="grok-4")

chat.append(system("Given a raw invoice, carefully analyze the text and extract the invoice data into JSON format."))
chat.append(
user("""
Vendor: Acme Corp, 123 Main St, Springfield, IL 62704
Invoice Number: INV-2025-001
Date: 2025-02-10
Items: - Widget A, 5 units, $10.00 each - Widget B, 2 units, $15.00 each
Total: $80.00 USD
""")
)

# The parse method returns a tuple of the full response object as well as the parsed pydantic object.

response, invoice = chat.parse(Invoice)
assert isinstance(invoice, Invoice)

# Can access fields of the parsed invoice object directly

print(invoice.vendor_name)
print(invoice.invoice_number)
print(invoice.invoice_date)
print(invoice.line_items)
print(invoice.total_amount)
print(invoice.currency)

# Can also access fields from the raw response object such as the content.

# In this case, the content is the JSON schema representation of the parsed invoice object

print(response.content)
```

### [Step 4: Type-safe Output](https://docs.x.ai/docs/guides/structured-outputs#step-4-type-safe-output)

The output will **always** be type-safe and respect the input schema.

JSON

```
{
  "vendor_name": "Acme Corp",
  "vendor_address": {
    "street": "123 Main St",
    "city": "Springfield",
    "postal_code": "62704",
    "country": "IL"
  },
  "invoice_number": "INV-2025-001",
  "invoice_date": "2025-02-10",
  "line_items": [
    { "description": "Widget A", "quantity": 5, "unit_price": 10.0 },
    { "description": "Widget B", "quantity": 2, "unit_price": 15.0 }
  ],
  "total_amount": 80.0,
  "currency": "USD"
}
```

## [Structured Outputs with Tools](https://docs.x.ai/docs/guides/structured-outputs#structured-outputs-with-tools)

Structured outputs with tools is only available for the Grok 4 family of models (e.g., `grok-4-1-fast`, `grok-4-fast`, `grok-4-1-fast-non-reasoning`, `grok-4-fast-non-reasoning`).

You can combine structured outputs with tool calling to get type-safe responses from tool-augmented queries. This works with both:

- **Agentic tool calling**: Server-side tools like web search, X search, and code execution that the model orchestrates autonomously.
- **Function calling**: User-supplied tools where you define custom functions and handle tool execution yourself.

This combination enables workflows where the model can use tools to gather information and return results in a predictable, strongly-typed format.

### [Example: Agentic Tools with Structured Output](https://docs.x.ai/docs/guides/structured-outputs#example-agentic-tools-with-structured-output)

This example uses web search to find the latest research on a topic and extracts structured data into a schema:

```
from pydantic import BaseModel, Field

class ProofInfo(BaseModel):
    name: str = Field(description="Name of the proof or paper")
    authors: str = Field(description="Authors of the proof")
    year: str = Field(description="Year published")
    summary: str = Field(description="Brief summary of the approach")
```

```
import os
from pydantic import BaseModel, Field

from xai_sdk import Client
from xai_sdk.chat import user
from xai_sdk.tools import web_search

# ProofInfo schema defined above

client = Client(api_key=os.getenv("XAI_API_KEY"))
chat = client.chat.create(
    model="grok-4-1-fast",
    tools=[web_search()],
)

chat.append(user("Find the latest machine-checked proof of the four color theorem."))

response, proof = chat.parse(ProofInfo)

print(f"Name: {proof.name}")
print(f"Authors: {proof.authors}")
print(f"Year: {proof.year}")
print(f"Summary: {proof.summary}")
```

### [Example: Client-side Tools with Structured Output](https://docs.x.ai/docs/guides/structured-outputs#example-client-side-tools-with-structured-output)

This example uses a client-side function tool to compute Collatz sequence steps and returns the result in a structured format:

```
from pydantic import BaseModel, Field

class CollatzResult(BaseModel):
    starting_number: int = Field(description="The input number")
    steps: int = Field(description="Number of steps to reach 1")
```

```
import os
import json
from pydantic import BaseModel, Field

from xai_sdk import Client
from xai_sdk.chat import tool, tool_result, user

# CollatzResult schema defined above

def collatz_steps(n: int) -> int:
    """Returns the number of steps for n to reach 1 in the Collatz sequence."""
    steps = 0
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        steps += 1
    return steps

collatz_tool = tool(
    name="collatz_steps",
    description="Compute the number of steps for a number to reach 1 in the Collatz sequence",
    parameters={
        "type": "object",
        "properties": {
            "n": {"type": "integer", "description": "The starting number"},
        },
        "required": ["n"],
    },
)

client = Client(api_key=os.getenv("XAI_API_KEY"))
chat = client.chat.create(
    model="grok-4-1-fast-non-reasoning",
    tools=[collatz_tool],
)

chat.append(user("Use the collatz_steps tool to find how many steps it takes for 20250709 to reach 1."))

# Handle tool calls until we get a final response
while True:
    response = chat.sample()

    if not response.tool_calls:
        break

    chat.append(response)
    for tc in response.tool_calls:
        args = json.loads(tc.function.arguments)
        result = collatz_steps(args["n"])
        chat.append(tool_result(str(result)))

# Parse the final response into structured output
response, result = chat.parse(CollatzResult)

print(f"Starting number: {result.starting_number}")
print(f"Steps to reach 1: {result.steps}")
```

## [Alternative: Usingresponse_formatwithsample()orstream()](https://docs.x.ai/docs/guides/structured-outputs#alternative-using-response_format-with-sample-or-stream)

When using the xAI Python SDK, there's an alternative way to retrieve structured outputs. Instead of using the `parse()` method, you can pass your Pydantic model directly to the `response_format` parameter when creating a chat, and then use `sample()` or `stream()` to get the response.

### [How It Works](https://docs.x.ai/docs/guides/structured-outputs#how-it-works)

When you pass a Pydantic model to `response_format`, the SDK automatically:

1. Converts your Pydantic model to a JSON schema
2. Constrains the model's output to conform to that schema
3. Returns the response as a JSON string, that is conforming to the Pydantic model, in `response.content`

You then manually parse the JSON string into your Pydantic model instance.

### [Key Differences](https://docs.x.ai/docs/guides/structured-outputs#key-differences)

| Approach | Method | Returns | Parsing |
| --- | --- | --- | --- |
| **Usingparse()** | `chat.parse(Model)` | Tuple of `(Response, Model)` | Automatic - SDK parses for you |
| **Usingresponse_format** | `chat.sample()` or `chat.stream()` | `Response` with JSON string | Manual - You parse `response.content` |

### [When to Use Each Approach](https://docs.x.ai/docs/guides/structured-outputs#when-to-use-each-approach)

- **Useparse()** when you want the simplest, most convenient experience with automatic parsing
- **Useresponse_format+sample()orstream()** when you:  
Want more control over the parsing process
Need to handle the raw JSON string before parsing
Want to use streaming with structured outputs
Are integrating with existing code that expects to work with sample() or stream()
- Want more control over the parsing process
- Need to handle the raw JSON string before parsing
- Want to use streaming with structured outputs
- Are integrating with existing code that expects to work with `sample()` or `stream()`

### [Example Usingresponse_format](https://docs.x.ai/docs/guides/structured-outputs#example-using-response_format)

Python

```
import os
from datetime import date
from enum import Enum

from pydantic import BaseModel, Field
from xai_sdk import Client
from xai_sdk.chat import system, user

# Pydantic Schemas
class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"

class LineItem(BaseModel):
    description: str = Field(description="Description of the item or service")
    quantity: int = Field(description="Number of units", ge=1)
    unit_price: float = Field(description="Price per unit", ge=0)

class Address(BaseModel):
    street: str = Field(description="Street address")
    city: str = Field(description="City")
    postal_code: str = Field(description="Postal/ZIP code")
    country: str = Field(description="Country")

class Invoice(BaseModel):
    vendor_name: str = Field(description="Name of the vendor")
    vendor_address: Address = Field(description="Vendor's address")
    invoice_number: str = Field(description="Unique invoice identifier")
    invoice_date: date = Field(description="Date the invoice was issued")
    line_items: list[LineItem] = Field(description="List of purchased items/services")
    total_amount: float = Field(description="Total amount due", ge=0)
    currency: Currency = Field(description="Currency of the invoice")

client = Client(api_key=os.getenv("XAI_API_KEY"))

# Pass the Pydantic model to response_format instead of using parse()
chat = client.chat.create(
    model="grok-4",
    response_format=Invoice,  # Pass the Pydantic model here
)

chat.append(system("Given a raw invoice, carefully analyze the text and extract the invoice data into JSON format."))
chat.append(
    user("""
Vendor: Acme Corp, 123 Main St, Springfield, IL 62704
Invoice Number: INV-2025-001
Date: 2025-02-10
Items: - Widget A, 5 units, $10.00 each - Widget B, 2 units, $15.00 each
Total: $80.00 USD
""")
)

# Use sample() instead of parse() - returns Response object
response = chat.sample()

# The response.content is a valid JSON string conforming to your schema
print(response.content)
# Output: {"vendor_name": "Acme Corp", "vendor_address": {...}, ...}

# Manually parse the JSON string into your Pydantic model
invoice = Invoice.model_validate_json(response.content)
assert isinstance(invoice, Invoice)

# Access fields of the parsed invoice object
print(invoice.vendor_name)
print(invoice.invoice_number)
print(invoice.total_amount)
```

### [Streaming with Structured Outputs](https://docs.x.ai/docs/guides/structured-outputs#streaming-with-structured-outputs)

You can also use `stream()` with `response_format` to get streaming structured output. The chunks will progressively build up the JSON string:

Python

```
import os

from pydantic import BaseModel, Field
from xai_sdk import Client
from xai_sdk.chat import system, user

class Summary(BaseModel):
    title: str = Field(description="A brief title")
    key_points: list[str] = Field(description="Main points from the text")
    sentiment: str = Field(description="Overall sentiment: positive, negative, or neutral")

client = Client(api_key=os.getenv("XAI_API_KEY"))

chat = client.chat.create(
    model="grok-4",
    response_format=Summary,  # Pass the Pydantic model here
)

chat.append(system("Analyze the following text and provide a structured summary."))
chat.append(user("The new product launch exceeded expectations with record sales..."))

# Stream the response - chunks contain partial JSON
for response, chunk in chat.stream():
    print(chunk.content, end="", flush=True)

# Parse the complete JSON string into your model
summary = Summary.model_validate_json(response.content)
print(f"Title: {summary.title}")
print(f"Sentiment: {summary.sentiment}")
```

- [Structured Outputs](https://docs.x.ai/docs/guides/structured-outputs#structured-outputs)
- [Supported models](https://docs.x.ai/docs/guides/structured-outputs#supported-models)
- [Supported schemas](https://docs.x.ai/docs/guides/structured-outputs#supported-schemas)
- [Example: Invoice Parsing](https://docs.x.ai/docs/guides/structured-outputs#example-invoice-parsing)
- [Step 1: Defining the Schema](https://docs.x.ai/docs/guides/structured-outputs#step-1-defining-the-schema)
- [Step 2: Prepare The Prompts](https://docs.x.ai/docs/guides/structured-outputs#step-2-prepare-the-prompts)
- [System Prompt](https://docs.x.ai/docs/guides/structured-outputs#system-prompt)
- [Example Invoice Text](https://docs.x.ai/docs/guides/structured-outputs#example-invoice-text)
- [Step 3: The Final Code](https://docs.x.ai/docs/guides/structured-outputs#step-3-the-final-code)
- [Step 4: Type-safe Output](https://docs.x.ai/docs/guides/structured-outputs#step-4-type-safe-output)
- [Structured Outputs with Tools](https://docs.x.ai/docs/guides/structured-outputs#structured-outputs-with-tools)
- [Example: Agentic Tools with Structured Output](https://docs.x.ai/docs/guides/structured-outputs#example-agentic-tools-with-structured-output)
- [Example: Client-side Tools with Structured Output](https://docs.x.ai/docs/guides/structured-outputs#example-client-side-tools-with-structured-output)
- [Alternative: Using response_format with sample() or stream()](https://docs.x.ai/docs/guides/structured-outputs#alternative-using-response_format-with-sample-or-stream)
- [How It Works](https://docs.x.ai/docs/guides/structured-outputs#how-it-works)
- [Key Differences](https://docs.x.ai/docs/guides/structured-outputs#key-differences)
- [When to Use Each Approach](https://docs.x.ai/docs/guides/structured-outputs#when-to-use-each-approach)
- [Example Using response_format](https://docs.x.ai/docs/guides/structured-outputs#example-using-response_format)
- [Streaming with Structured Outputs](https://docs.x.ai/docs/guides/structured-outputs#streaming-with-structured-outputs)