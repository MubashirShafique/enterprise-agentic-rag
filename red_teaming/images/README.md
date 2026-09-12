# AI Red Team Dashboard & Attack Previews

Visual previews and execution summaries across the security evaluation suite.

---

### 1. Dashboard Overview
![Dashboard Overview](0_.png)

High-level security posture displaying overall resilience score, total tests executed, and vulnerability status.

---

<br>

### 2. Direct Prompt Injection
![Direct Prompt Injection](1_.png)

Evaluates whether direct system-override instructions can hijack the model's core directives.

---

<br>

### 3. Crescendo Multi-Turn Escalation
![Crescendo Escalation](2_.png)

Simulates multi-turn progressive conversation drift to bypass guardrails gradually over time.

---

<br>

### 4. Encoding Obfuscation
![Encoding Obfuscation](3_.png)

Tests model resistance against encoded adversarial instructions such as Base64 and ROT13.

---

<br>

### 5. Orchestrator Multi-Turn Attack
![Orchestrator Attack](4_.png)

Automated PyRIT orchestrator simulating natural, multi-turn escalation paths against the RAG system.

---

<br>

### 6. Cross-Prompt Injection (XPIA) Baseline
![XPIA Baseline](5_.png)

Evaluates system vulnerability against adversarial formatting instructions disguised as retrieved context.

---

<br>

### 7. Skeleton Key XPIA
![Skeleton Key XPIA](6_.png)

Tests research-justification jailbreak instructions disguised within administrative context payloads.

---

<br>

### 8. Advanced XPIA Suite
![Advanced XPIA](7_.png)

Evaluates multiple complex XPIA injection variants covering data exfiltration and credential exposure.

---

<br>

### 9. Bulk Fuzzing Scanner
![Bulk Fuzzing Scanner](8_.png)

Large-scale automated prompt mutation scanner running high-volume variations against the live endpoint.

---
