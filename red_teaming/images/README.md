# AI Red Team Dashboard & Attack Previews

Visual previews and execution summaries across the security evaluation suite.

---

### 1. Dashboard Overview
![Dashboard Overview](0_.png)

Central SOC-style security overview showing a 99% resistance score across 209 automated adversarial tests[cite: 1, 4]. It displays live system status badges, resilience progress bars, and module-level test breakdowns[cite: 4].

---

<br>

### 2. Direct Prompt Injection
![Direct Prompt Injection](1_.png)

Evaluates system resilience against authority personas, pseudo-XML delimiters, and token-smuggled system prompt leak attempts[cite: 7]. Tests verify whether the RAG model adheres to core directives without dropping its assistant persona[cite: 7].

---

<br>

### 3. Crescendo Multi-Turn Escalation
![Crescendo Escalation](2_.png)

Simulates PyRIT's adaptive multi-turn escalation strategy that gradually builds rapport under developer pretext before attempting boundary violations[cite: 6]. It monitors whether internal configurations or retrieval parameters leak over long conversations[cite: 6].

---

<br>

### 4. Encoding Obfuscation
![Encoding Obfuscation](3_.png)

Tests guardrail detection against multi-layered encoding chains like Base32, Hex, chunked reverse, and Cyrillic homoglyph look-alikes[cite: 8]. Ensures raw or transformed strings do not bypass input filters to execute hidden instructions[cite: 8].

---

<br>

### 5. Orchestrator Multi-Turn Attack
![Orchestrator Attack](4_.png)

Executes PyRIT RedTeamingAttack with rotating personas (auditor, debugging developer, frustrated user) across a single thread[cite: 9]. Verifies whether persistent behavioral pressure or context drift degrades system security boundaries[cite: 9].

---

<br>

### 6. Cross-Prompt Injection (XPIA) Baseline
![XPIA Baseline](5_.png)

Tests vulnerability against simulated internal knowledge base entries injected with subtle out-of-band marker directives[cite: 2]. Evaluates whether the system treats untrusted retrieved content as pure reference data rather than executable instructions[cite: 2].

---

<br>

### 7. Skeleton Key XPIA
![Skeleton Key XPIA](6_.png)

Delivers fake administrative audit-mode justifications embedded within simulated retrieved context chunks[cite: 3, 10]. Evaluates whether privileged framing inside retrieved context can trick the model into disclosing system access levels[cite: 3].

---

<br>

### 8. Advanced XPIA Suite
![Advanced XPIA](7_.png)

Runs complex injection vectors including HTML comment smuggling, fake markdown metadata, and footnote overrides targeting PII and credentials[cite: 3]. Ensures hidden document formatting cannot hijack downstream agent responses or exfiltrate parameters[cite: 3].

---

<br>

### 9. Bulk Fuzzing Scanner
![Bulk Fuzzing Scanner](8_.png)

Executes high-volume mutation scans combining deterministic technique matrices with LLM-generated semantic variations[cite: 5]. Tests live endpoint stability and throttles concurrent requests to identify boundary regressions[cite: 5].

---
