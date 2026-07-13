<!-- <p align="left">
  <img src="./logo.png" width="110" alt="PyDocs AI logo">
</p>

<h1 align="center">PyDocs AI</h1> -->
<p align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./banner-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="./banner-light.png">
  <img alt="PyDocs AI Banner" src="./assets/banner-dark.png" width="70%">
</picture>

</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="license">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="python">
  <img src="https://img.shields.io/badge/status-active-brightgreen" alt="status">
</p>

---

**Repo:** `pydantic-ai-docs-agent`

PyDocs AI is an independent, agentic RAG (Retrieval-Augmented Generation) chatbot built to answer questions about [Pydantic AI](https://ai.pydantic.dev)'s documentation. Instead of a single retrieval tool, it uses multiple specialized tools — each backed by its own vector store — so the agent can route your question to the most relevant part of the docs before answering.

> ⚠️ This is an independent, unofficial project built on Pydantic AI's open-source documentation. It is not affiliated with or endorsed by Pydantic Services Inc.

## Why this project

Most RAG demos use one tool and one vector database for everything. PyDocs AI instead splits the documentation into focused categories (agents, models, tools, testing, etc.), each with its own retrieval tool. The agent decides which tool(s) to call based on the question, which keeps retrieval more accurate and the reasoning more transparent.







```

## License

MIT
