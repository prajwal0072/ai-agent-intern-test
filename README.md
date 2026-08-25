# Aster & Row — AI Support Agent

An AI-powered customer support agent built for the Aster & Row AI Agent Intern take-home assignment.

The agent combines **retrieval-augmented generation (RAG)**, structured order lookup, conversation memory, source prioritization, privacy controls, and deterministic business rules to answer customer support questions safely and accurately.

## Features

- Knowledge-base retrieval from Markdown policy documents
- Semantic search using embeddings
- LLM-powered customer support responses
- Structured order lookup tool
- Multi-turn conversation support
- Order ID detection and follow-up handling
- Customer-safe order information filtering
- Protection of internal customer information
- Prompt-injection resistance for retrieved documents
- Superseded-policy handling and source prioritization
- Business-rule enforcement for order statuses
- Human handoff for cases requiring support review
- Abstention when the available information is insufficient
- Multi-source grounding
- Streamlit customer-support interface
- Automated unit tests and evaluation cases

---

## Architecture

```text
                         ┌─────────────────────┐
                         │      Customer       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Streamlit UI     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    SupportAgent     │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
          ┌──────────────────┐            ┌──────────────────┐
          │ Knowledge Base   │            │   Order Tool     │
          │                  │            │                  │
          │ Markdown Policies│            │ orders.json      │
          │      ↓           │            │      ↓           │
          │    Chunks        │            │ Sanitization     │
          │      ↓           │            │      ↓           │
          │   Embeddings     │            │ Business Rules   │
          │      ↓           │            │                  │
          │   Retrieval      │            │ Customer-safe    │
          └────────┬─────────┘            │ output           │
                   │                      └────────┬─────────┘
                   │                               │
                   └───────────────┬───────────────┘
                                   │
                                   ▼
                         ┌─────────────────────┐
                         │         LLM         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Customer Response   │
                         └─────────────────────┘
ai-agent-intern-test/
│
├── app/
│   ├── __init__.py
│   ├── agent.py
│   ├── config.py
│   ├── embeddings.py
│   ├── frontend.py
│   ├── ingestion.py
│   ├── llm.py
│   ├── models.py
│   ├── order_tool.py
│   ├── retrieval.py
│   └── session.py
│
├── data/
│   ├── orders.json
│   └── orders-data-dictionary.md
│
├── evaluation/
│   ├── __init__.py
│   ├── original-cases.json
│   └── run_evaluation.py
│
├── knowledge-base/
│   ├── 01-returns-policy-current.md
│   ├── 02-returns-policy-legacy.md
│   ├── 03-final-sale-and-promotions.md
│   ├── 04-damaged-or-wrong-items.md
│   ├── 05-domestic-shipping.md
│   ├── 06-international-shipping.md
│   ├── 07-warranty.md
│   ├── 08-order-changes-and-cancellations.md
│   ├── 09-trailplus-membership.md
│   ├── 10-gift-cards-and-price-adjustments.md
│   ├── 11-product-care.md
│   ├── 12-breeze-tumbler-product-card.md
│   ├── 13-support-escalation.md
│   └── 14-internal-content-migration-notes.md
│
├── scripts/
│   └── inspect_orders.py
│
├── tests/
│   ├── test_agent.py
│   ├── test_config.py
│   ├── test_embeddings.py
│   ├── test_ingestion.py
│   ├── test_llm.py
│   ├── test_order_tool.py
│   ├── test_retrieval.py
│   └── test_session.py
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md


Tech Stack
Python
OpenAI API
Embeddings
Retrieval-Augmented Generation (RAG)
Pydantic / structured models
Streamlit
Pytest
JSON
Markdown knowledge base
How the Agent Works
1. Knowledge-base ingestion

The support policies are stored as Markdown documents.

The ingestion pipeline:

Markdown documents
       ↓
Document loading
       ↓
Section/chunk extraction
       ↓
Metadata preservation
       ↓
Embedding generation
       ↓
Retrievable knowledge base

Each chunk retains information such as the source document and section.

This allows the agent to provide grounded answers and identify which policy was used.

2. Retrieval

When a customer asks a policy-related question, the agent searches the knowledge base for relevant information.

For example:

How long does a regular customer have to return an unused backpack?

The system retrieves the relevant section from:

01-returns-policy-current.md

The agent then uses the retrieved policy to construct the response.

Superseded documents remain retrievable because they may be useful for conflict detection, but active authoritative documents receive higher priority.

3. Order lookup

Order-related questions use the structured order_lookup tool.

Example:

Customer:
Where is ORD-1007 and when should it arrive?

        ↓

Order ID detection

        ↓

order_lookup("ORD-1007")

        ↓

Customer-safe order data

        ↓

Agent response

The agent does not expose the complete raw order object to the customer.

Order Data Privacy

The order tool uses an explicit allowlist of customer-safe fields.

Safe information can include:

Order ID
Membership tier
Item name
Item quantity
Final-sale status
Order status
Status update time
Shipping information
Tracking number
Estimated delivery
Customer-safe message

The following information is deliberately excluded:

Customer name
Customer email
Shipping address
Internal risk scores
Warehouse notes
Support tags
Other internal information

The complete order dataset is never returned directly to the model.

Order Status Reliability

The order tool treats the status field as authoritative.

For example, if an order is:

status = cancelled

but an old estimated delivery date still exists in the dataset, the agent does not tell the customer that the order is arriving.

Similarly:

returned → stale delivery information is not presented as active
shipped + no ETA → the agent states that an estimate is unavailable
exception → the agent recommends human support review

This prevents stale operational data from producing misleading responses.

Prompt Injection Protection

Retrieved knowledge-base content is treated as data, not instructions.

This is especially important because internal documents may contain text that attempts to influence the agent.

The agent should:

Retrieve relevant content.
Treat retrieved content as evidence.
Follow system/application rules over retrieved text.
Never expose internal content.
Never execute instructions found inside customer-facing or internal documents.
Source Prioritization

The knowledge base contains both active and superseded policies.

For example:

RET-2026-01
Returns Policy
status: active

and:

RET-2024-01
Returns Policy — Legacy Version
status: superseded

The current authoritative policy is prioritized when answering current customer questions.

However, superseded documents are not simply deleted from retrieval because they can be useful when detecting conflicts between sources.

Conversation Handling

The agent supports multi-turn conversations.

Example:

Customer:
Where is ORD-1007?

Agent:
ORD-1007 has shipped...

Customer:
When will it arrive?

Agent:
The estimated delivery is August 22, 2026.

The session stores relevant conversation state, including the current order context.

This allows follow-up questions such as:

"When will it arrive?"
"Is it shipped?"
"Can I track it?"

to refer to the previously identified order.

Human Handoff

Certain situations should not be handled as ordinary automated answers.

The agent can recommend or trigger a support handoff when:

An order has an operational exception
Available information is insufficient
Conflicting authoritative information cannot be safely reconciled
A customer needs an action that the available tools cannot perform

The system does not falsely claim that unsupported actions were completed.

For example, if the dataset only provides lookup functionality, the agent does not claim:

"I cancelled your order."

unless an actual cancellation tool exists and successfully performs the action.

Streamlit Interface

The project includes a Streamlit frontend for interacting with the support agent.

Run it from the project root:

streamlit run app/frontend.py

The interface provides a simple customer-support chat experience for testing the agent.
