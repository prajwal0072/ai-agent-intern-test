# Aster & Row — AI Support Agent
Deployed Link:https://ai-agent-intern-test-2507.streamlit.app/
Demo video:https://drive.google.com/file/d/18vcX0IkjQE-N5ikIJ1abCnisis7gugxg/view?usp=sharing
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
support chat experience for testing the agent.
