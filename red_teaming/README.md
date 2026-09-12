# AI Red Team Security Dashboard

This project tests how well an AI-powered customer support system can defend itself against attacks.

The support system here is a RAG (Retrieval-Augmented Generation) chatbot — it answers customer questions by pulling info from a knowledge base and passing it to an AI model. It's built with LangGraph, NeMo Guardrails, Qdrant, FlashRank, and Portkey.

This project sends it a large set of adversarial (attack) prompts to check if it can be tricked into doing things it shouldn't — like revealing internal system info, leaking sensitive data, or ignoring its own safety rules. The results are shown in an easy-to-read dashboard.

**Important:** This is an authorized test on a system the author owns and controls. No third-party or public systems are targeted.

## Security Dashboard Preview

![AI Red Team Dashboard Overview](images/0_.png)
<br>
🔴 **For more previews of each attack module, [click here](images/README.md)!**
## Latest Results

| Metric | Value |
|---|---|
| Total tests run | 209 |
| Passed (system defended itself) | 208 |
| Failed (system got tricked) | 1 |
| Overall resistance score | 99% (A+) |

## What Gets Tested

1. **Direct Prompt Injection :**  trying to override the system's instructions directly, using tricks like fake system tags, authority claims, hidden text inside quotes, and switching languages.
2. **Crescendo Escalation :** a slow, multi-turn conversation that builds trust before trying to sneak in a harmful request.
3. **Encoding Tricks :** hiding the attack inside Base64, hex, ROT13, or other encodings so simple filters can't catch it.
4. **Multi-Persona Attack :** the attacker keeps switching personas (confused new employee, frustrated user, "auditor", etc.) across one long conversation to find a weak spot.
5. **XPIA (Cross-Prompt Injection) :** simulates indirect prompt injection by formatting adversarial instructions directly within user query payloads to mimic poisoned retrieved context without altering the underlying database.
6. **Skeleton Key XPIA :** combines a fake "audit mode" jailbreak with the XPIA trick above.
7. **Advanced XPIA :** six different ways to sneak instructions into retrieved documents (HTML comments, fake metadata, fake footnotes, etc.).
8. **Bulk Fuzzing :**  automatically generates and tests many variations of each attack at once for broader coverage.

## Guardrails Hardening

The first version of the safety rules was weak — early tests found real problems, including some internal system details leaking out. The rules and system prompt were then strengthened, and every test was run again on the live system to confirm the fixes worked. The results above are from **after** the fix.

## Environment Setup

Before running anything, create a `.env` file in the main project folder and add these fields:

```dotenv
RAG_ENDPOINT=http://127.0.0.1:8000/query
RAG_REQUEST_KEY=q
RAG_RESPONSE_KEY=response
CHAT_MODEL="gpt-4o-mini"
OPENAI_API_KEY="your-api-key-here"
```

- `RAG_ENDPOINT` — the URL of the chatbot's `/query` endpoint that will be tested.
- `RAG_REQUEST_KEY` / `RAG_RESPONSE_KEY` — the field names the endpoint expects for the request and the response.
- `CHAT_MODEL` — the model used by the attacker/judge AI (separate from the system being tested).
- `OPENAI_API_KEY` — your own OpenAI API key. Never commit this file or share the real key.

## How to Run This

**Step 1 — Install the requirements:**

```bash
pip install -r requirements_for_red_teaming.txt
```

**Step 2 — Launch the dashboard:**

```bash
streamlit run app.py
```

This opens the dashboard in your browser, where you can run any attack module and see the results.

## Disclaimer

This is an authorized, internal security test of a system the author owns and controls. Every attack payload is sent only to the author's own deployed RAG endpoint. No third-party systems are involved.
