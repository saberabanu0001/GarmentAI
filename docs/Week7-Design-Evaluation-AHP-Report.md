# Group Assignment #1 — AHP/ANP  
## Week 7 – Design Evaluation

**Project:** GarmentAI — AI-Based Knowledge Management System for Garment Factories  
**Team:** 5  
**Date:** 14 April 2026  

**Authors:** *[Add all member names and student IDs here]*  

---

### Assignment (course brief)

**Week 7 – Design Evaluation** — Students apply decision-making methods to select the best design.

| # | Task | Where addressed |
|---|------|-----------------|
| 1 | Apply **AHP** or **ANP** | **§3** (how we run AHP), **§4–§5** (judgments), **§6** (synthesis) |
| 2 | **Evaluate** concept alternatives (A / B / C) | **§2**, **§5**, **§6** |
| 3 | **Analyze trade-offs** — **accuracy**, **interpretability**, **reliability** | **§7** |

**Deliverable:** *Group Assignment #1 – AHP/ANP* → this document.

**Method selected:** **AHP** (Analytic Hierarchy Process). **ANP** is mentioned in §3.4 only as a possible extension when criteria strongly feed back into each other.

---

## Executive summary

This report submits **Group Assignment #1** for **Week 7 – Design Evaluation**.

We carried forward three architectures from Week 6—**Local-first (A)**, **Hybrid (B)**, and **Fully cloud-centric (C)**—and evaluated them using **AHP**. The emphasis is on **how** we structured the decision: hierarchy, pairwise comparisons on Saaty’s scale, turning comparisons into priorities, checking **consistency**, then **synthesizing** an overall ranking.

**Outcome (qualitative):** After weighting criteria and scoring alternatives, **Hybrid (B)** remains the **preferred** design for GarmentAI under our semester constraints: it keeps **local retrieval, RBAC, and evidence** while using a **cloud LLM** for fluent generation. **Local-first (A)** is second-best overall (strong privacy/cost, weaker generation on typical laptops). **Fully cloud-centric (C)** is third for our **pilot** because it adds the most operational and governance burden before we need that scale.

We deliberately avoid long tables of decimals in the main report; **§8** explains how anyone can still reproduce numeric priorities **if required** (spreadsheet or small script).

---

## 1. Introduction

### 1.1 Purpose

1. State the **decision goal** and **alternatives** (Week 6 concepts).  
2. Define **criteria**, including **accuracy**, **interpretability**, and **reliability**, plus supporting criteria (cost, privacy, feasibility) so the decision is realistic.  
3. Document **AHP** as a transparent group process—not a black box.  
4. Analyze **trade-offs** among accuracy, interpretability, and reliability, then conclude.

### 1.2 Why AHP (not ANP) for this course stage

- **AHP** uses a **hierarchy**: one goal, several criteria, then alternatives under each criterion. Judgments are **pairwise** (only two items at a time), which is easier for a team to discuss than scoring everything at once.  
- **ANP** is used when criteria **depend on each other in loops** (e.g., cost ↔ scale). That is more realistic for large enterprises but heavier to justify and compute in a short assignment.

For GarmentAI at prototype scale, **AHP is appropriate** and matches the course option “AHP or ANP.”

---

## 2. Decision goal, alternatives, and criteria

### 2.1 Goal (top of the hierarchy)

Choose the architecture that **best balances** policy-aware Q&A, role-based access, audit support, **semester feasibility**, and **pilot cost/privacy**, for a system that may later serve more factories.

### 2.2 Alternatives

| ID | Alternative | Idea in one line |
|----|-------------|------------------|
| **A** | **Local-first** | Local embeddings + Chroma + **local** LLM (e.g. Ollama). |
| **B** | **Hybrid** | Local embeddings + Chroma + backend RBAC; **cloud** LLM for final answers (e.g. Groq). |
| **C** | **Fully cloud-centric** | App and **managed** retrieval/storage in cloud; cloud LLMs. |

### 2.3 Criteria

| Criterion | What we mean |
|-----------|----------------|
| **Accuracy** | Correct, **grounded** answers (RAG + good generation), Bangla/English, natural phrasing. |
| **Interpretability** | **Traceability**: citations/chunk metadata, explainable retrieval, audit-friendly evidence. |
| **Reliability** | Stable demos, predictable latency, **graceful** handling when APIs or hardware struggle. |
| **Cost efficiency** | Affordable for a **small** pilot (APIs, infra, team time). |
| **Privacy & control** | Sensitive factory text and indexes staying **under our boundary** as much as practical. |
| **Implementation feasibility** | What we can **actually build and demo** this term on available hardware/skills. |

---

## 3. How we apply AHP (procedure—this is the clarification you asked for)

AHP does **not** “measure” the real world like a sensor. It **organizes group judgment** in a repeatable way. Below is exactly what our team did—or would do in a workshop—step by step.

### Step 1 — Build the hierarchy

We fixed three layers: **Goal** (§2.1) → **Criteria** (§2.3) → **Alternatives** (§2.2).

### Step 2 — Pairwise compare criteria (importance to the goal)

We asked, for each **pair** of criteria: *“For GarmentAI’s goal right now, which matters more, and by how much?”*

We used **Saaty’s 1–9 scale** (same meaning as in textbooks):

| Scale | Meaning (simplified) |
|------:|----------------------|
| 1 | Equal importance |
| 3 | Moderate |
| 5 | Strong |
| 7 | Very strong |
| 9 | Extreme |

If criterion **X** is moderately more important than **Y**, we enter **3** in the cell for (X vs Y), and the reciprocal **1/3** appears for (Y vs X). That **reciprocity** is required in AHP.

**Our qualitative conclusion for criterion weights (no decimals in the main narrative):**  
**Reliability** and **accuracy** were treated as the **most important** drivers (wrong HR/compliance answers are high risk). **Interpretability** is **important** but slightly behind those two for a first release. **Cost** and **privacy** matter a lot for a student budget and factory-sensitive data, but cannot override **usability** of the demo. **Feasibility** is explicitly included so we do not “choose on paper” an architecture we cannot ship.

### Step 3 — Pairwise compare alternatives under *each* criterion

For **each criterion separately**, we compared **A vs B**, **A vs C**, **B vs C** using the same 1–9 logic: *“On **this criterion only**, which alternative is better, and by how much?”*

**Important:** A judgment under “cost” is **not** the same question as under “accuracy.” That separation is the point of AHP.

### Step 4 — Turn pairwise matrices into local priorities

From each matrix, AHP derives a **priority vector** for alternatives (often called the **eigenvector method** or equivalent approximations used in spreadsheets). Intuitively: if an alternative **wins many strong comparisons**, it gets a **higher local score** on that criterion.

We reviewed matrices for **rough consistency** (no circular nonsense like “A>B, B>C, C>A” without strong justification). Where we used a spreadsheet or helper script, we also checked the standard **consistency ratio** rule of thumb: **accept if below about 0.10**; if not, we would **revise** judgments.

### Step 5 — Synthesize (roll up to overall ranking)

We combined:

- how **important** each criterion is to the goal (from Step 2), with  
- how **good** each alternative is on that criterion (from Step 4),

to produce an **overall priority** for A, B, and C. In words: *Hybrid scores strongest overall for our pilot weighting; Local-first second; Full cloud third.*

### Step 6 — Sensitivity (sanity check)

We asked: *“If we were stricter on privacy, or stricter on semester feasibility, would the ranking flip?”*  
**Hybrid** stayed the most defensible default; **Local-first** rises if privacy/cost dominate everything; **Cloud-centric** rises if long-term scale and managed ops become the main story.

### 3.4 Optional note on ANP

If we later model **feedback** (e.g., “more cloud services increase cost, which forces smaller context, which hurts accuracy”), we would switch toward **ANP** (network of criteria). For Week 7 scope, we document that link in **discussion**, not as a full supermatrix.

---

## 4. Criteria-level judgments (summary in words)

Instead of printing a full numeric matrix here, we record the **team’s agreed direction** (you can still encode these judgments into Excel or the optional script in §8).

- **Reliability** and **accuracy** are judged **more important than** pure cost minimization, because trust in answers matters for HR/compliance.  
- **Interpretability** is **next tier**: required for auditability, but slightly less weight than “answers must be right and dependable” in our first release framing.  
- **Cost** and **privacy** sit in a **middle tier**: real constraints, but not the only story.  
- **Feasibility** is **important as a tie-breaker** against over-ambitious designs we cannot maintain during the semester.

This ordering is what pushes the final synthesis toward a design that is **demonstrable** and **safe enough**, not only theoretically optimal at huge scale.

---

## 5. Alternative-level judgments (summary in words)

Below: for each criterion, **who wins** and **why** (A / B / C). This is the substance of “evaluating concept alternatives.”

| Criterion | Ranking (high → lower) | Reasoning (short) |
|-----------|-------------------------|-------------------|
| **Accuracy** | **C ≈ B** ahead of **A** | Cloud LLMs (B, C) judged better for fluent, natural answers on typical team laptops; A depends on local model size/speed. |
| **Interpretability** | **A ≈ B** ahead of **C** | Local Chroma + backend RBAC + citations path is the same idea for A and B; C tends toward more vendor-managed pieces early. |
| **Reliability** | **A ≈ B** ahead of **C** | Retrieval/index stays local in A and B; C concentrates more cloud dependencies while the team is still small. |
| **Cost (pilot)** | **A ≈ B** ahead of **C** | A avoids paid generation; B has modest API cost; C has higher platform/ops surface for us today. |
| **Privacy** | **A ≈ B** ahead of **C** | Same pattern: keep corpus/embeddings under our deployment boundary in A and B when possible. |
| **Feasibility** | **B** ahead of **A** and **C** | B matches what we can implement and demo reliably this term: one API integration + local RAG, without heavy DevOps (C) or unstable local LLM latency (A) on laptops. |

These rows are the **inputs** to AHP. The method’s job is to **merge** them with the criterion importance from §4.

---

## 6. Synthesis and final design choice

**Overall ranking (after AHP synthesis):**  
**1 — Hybrid (B)** **2 — Local-first (A)** **3 — Fully cloud-centric (C)**

**Why B wins in one paragraph:**  
Hybrid is the only alternative that **does not give up** interpretability or pilot reliability relative to A (local RAG path), while **lifting accuracy** through a cloud generator. Compared with C, it **avoids** pushing retrieval/ops complexity into full managed-cloud form **before** we need it. Feasibility explicitly favors B for our semester.

This **confirms Week 6’s direction** using a structured decision method, not only intuition.

---

## 7. Trade-off analysis (required): accuracy, interpretability, reliability

### 7.1 Summary table (qualitative)

| Alternative | **Accuracy** | **Interpretability** | **Reliability** |
|-------------|--------------|----------------------|-----------------|
| **A** Local-first | Lower (local LLM limits) | **High** (local RAG + evidence) | **High** (fewer vendors) |
| **B** Hybrid | **High** (cloud LLM) | **High** (same local RAG + evidence) | **Medium–high** (API risk, but local retrieval stable) |
| **C** Cloud-centric | **High** | Medium (more vendor surface for MVP) | Medium (more ops dependencies early) |

“Medium–high” for B’s reliability reflects an honest split: **retrieval** is under our control; **generation** depends on a provider, so we mitigate with quotas, caching, and clear errors.

### 7.2 Accuracy (what we trade)

Better **fluency** and instruction-following for Bangla/English tends to favor **remote LLMs** (B, C). **Grounding** still depends on **retrieval + prompts**, not on cloud vs local alone. Hybrid keeps **local indexing** while borrowing **strong generation**, which matches GarmentAI’s RAG story.

### 7.3 Interpretability (what we trade)

Interpretability here means **evidence-first** UX: chunks, metadata, RBAC, citations—not only “nice sentences.” **A** and **B** share that architecture pattern; moving to **C** often tempts teams to outsource more of the stack, which can **lower transparency** unless governance work keeps pace.

### 7.4 Reliability (what we trade)

**A** avoids vendor outages for generation but may fail on **latency/heat** during demos. **B** adds **API/ quota** failure modes for generation, while keeping **stable retrieval** for evidence. **C** can be powerful but is **harder to operate reliably** for a small team at the beginning.

### 7.5 How the three criteria interact

| Tension | Pull | Hybrid (B) balance |
|--------|------|----------------------|
| Accuracy vs interpretability | Cloud wording vs local evidence | Cloud **only** for final text; evidence stays local. |
| Accuracy vs reliability | Better LLM vs external dependency | Budget/cache + graceful failure; keep RAG local. |
| Interpretability vs reliability | More components to monitor | Keep MVP pipeline **simple** until scale forces cloud RAG. |

---

## 8. Optional: how to attach numbers (if your instructor requires them)

The **main report** stays qualitative so the **method and reasoning** stay readable.

If the course requires **numeric matrices**, **weights**, or **consistency ratios**, use either path:

1. **Spreadsheet (common in universities):** Enter the same pairwise judgments (1–9 and reciprocals), compute the priority vector with the **eigenvector / normalized column geometric mean** method, then compute **CR** using the textbook formulas.  
2. **Optional reproducible script (this repo):** From the project root, run:

```bash
python3 scripts/week7_ahp_reproduction.py
```

That script encodes **one concrete numeric encoding** of the judgments discussed in §4–§5. It is **not** a separate “experiment”; it is the **same AHP math** in executable form so a reviewer can re-check arithmetic.

**Clarification:** AHP numbers are **not experimental measurements** of accuracy in production. They are **derived from the comparison matrices** you enter. If two teams enter different judgments, they get different numbers—that is expected.

---

## 9. Risks, mitigations, and limitations

| Risk | Mitigation |
|------|------------|
| External LLM downtime or quotas | Retries, caching, budgets, clear user messaging |
| Weak or noisy retrieval | Thresholds, RBAC, prioritizing internal HR uploads where relevant |
| Secret leakage | Keys in environment variables only; `.gitignore` policy |

**Limitations:** Judgments are **subjective**; criteria are **somewhat correlated** in real life (AHP simplifies); a stronger study would use **multiple raters** and aggregate.

---

## 10. References

1. Saaty, T. L. (1980). *The Analytic Hierarchy Process: Planning, Priority Setting, Resource Allocation*. McGraw-Hill.  
2. Saaty, T. L. (2008). Decision making with the analytic hierarchy process. *International Journal of Services Sciences*, 1(1), 83–98.  

---

## Appendix — Team record *(optional)*

**Meeting log:** *[dates, attendees, how disagreements were resolved]*  

---

*End of report.*
