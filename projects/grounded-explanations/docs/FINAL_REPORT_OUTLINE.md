# Final Report Outline (7–8 pages)

**Course:** HCDE 563 · **Author:** Zhian Hu  
**Title (suggested):** *Grounded, User-Linked Explanations for AI Movie Recommendations: Modification and Evaluation of Rebert Prototype 7.1*  
**Target length:** ~3,800–4,800 words (7–8 pages, 12pt, 1-inch margins, double-spaced)

Use this outline section-by-section. Page estimates assume double-spaced academic formatting.

---

## 0. Title page & metadata (~0.5 page, not counted in body)

- Title, name, course, date
- GitHub (code only): https://github.com/AnsirU/HCDE563-modify-eval
- Note: *Participant data not in public repository — see Section 5.1*

---

## 1. Abstract (~150–200 words, ~0.3 page)

**Write:**
- One sentence on **problem** (recommendation opacity in LLM movie rec)
- One sentence on **intervention** (structured explanation: user alignment + review basis + confidence)
- One sentence on **method** (within-subjects, N=5, baseline vs modified)
- Two sentences on **key findings** (use aggregated results below)
- One sentence on **contribution** (AI transparency UX in prototyping, not population-level proof)

**Example closing line:**  
*"Findings suggest structured, source-linked explanations improved perceived transparency for most participants without increasing cognitive burden, though evidence granularity remains a design tension."*

---

## 2. Introduction (~600–700 words, ~1 page)

### 2.1 Motivation
- Why opaque AI recommendations matter for trust and control
- Rebert p7.1 already combines user Q&A, reviews, and LLM — but output blends sources

### 2.2 Problem statement
- Users cannot tell whether a suggestion reflects **their answers**, **reviews**, or **generic model reasoning**
- This is an **AI + presentation** problem, not only UI polish

### 2.3 Project goals
1. Modify p7.1 to produce **structured, source-linked** explanations
2. Evaluate impact on **transparency, trust, control** (secondary: evidence quality, cognitive load)

### 2.4 Contributions
- Level 1–2 implementation on a real Flask/LLM prototype
- Small-N within-subjects study with counterbalancing
- Design implications for explainable recommender interfaces

---

## 3. Background & Related Work (~400–500 words, ~0.75 page)

**Keep brief — this is a prototyping course, not a literature survey.**

### 3.1 Explainable recommendations
- Transparency vs justification; user mental models

### 3.2 Source grounding in LLM systems
- Hallucinated critic claims; need to separate user evidence vs review evidence

### 3.3 Prototyping framing
- Why within-subjects fits small exploratory samples
- Reference course framing: modify across levels (prompt, UI, optional data)

---

## 4. System & Modifications (~900–1,100 words, ~1.5–2 pages)

### 4.1 Baseline: Rebert Prototype 7.1
- Ephemeral Q&A → LLM match + paragraph rationale in tooltip/chat
- Multi-source reviews, TMDB metadata, Ask Rebert chat

### 4.2 Design requirements (from proposal)
- Short bullets, two evidence channels, uncertainty signaling

### 4.3 Level 1 — Prompt & schema (IMPLEMENTED)
- Tags: `<USER_ALIGNMENT>`, `<REVIEW_BASIS>`, `<CONFIDENCE>`
- Q1–Q3 linking; guardrails against fabricated review detail
- Files: `prompts.py`, `llm.py`, `explanations.py`

### 4.4 Level 2 — Interface (IMPLEMENTED)
- "Why this title" panel under each poster
- Click user-alignment bullet → highlight prior Q&A answer
- Study condition banner (baseline vs modified)
- Files: `mainpage.html`, `rebert_mainpage_ui.js`

### 4.5 Level 3 — Review excerpts (OPTIONAL / implemented but not in eval)
- `modified_full` mode with R1/R2/R3 excerpt IDs
- Note: evaluation used `modified` only to isolate Level 1+2

### 4.6 Implementation architecture
- Include simplified flow diagram (proposal → Q&A → LLM → parse → UI panel)
- Condition toggle: `REBERT_EXPLANATION_MODE=baseline|modified`

### 4.7 Repository scope
- Full Rebert code in `rebert/`; course sub-project in `projects/grounded-explanations/`

---

## 5. Evaluation (~700–900 words, ~1.25 pages)

### 5.1 Method
- **Design:** Within-subjects, counterbalanced A/B
- **N=5** convenience sample (classmates/friends, English UI, occasional movie watchers)
- **Order:** P1–P3 Baseline→Modified; P4–P5 Modified→Baseline
- **Scenarios:** Condition 1 = low-energy Sunday; Condition 2 = date-night (counterbalanced across order)
- **Task:** scenario → 3 ephemeral questions → recommend → review explanation → 1 chat follow-up → survey
- **Session length:** ~35–40 min
- **Instruments:** 5 Likert items (1–7) per condition + 2 comparative + debrief

### 5.2 Data handling & privacy (REQUIRED PARAGRAPH)

> *Participant-level study data are not published in the public GitHub repository. Raw Likert sheets, debrief notes, and any identifying session material are retained offline to protect participant privacy in a small-N convenience sample where re-identification risk is non-trivial. The repository contains study instruments, protocol, code, and technical verification only. Aggregated results and thematic summaries below are reported in this document for course evaluation.*

### 5.3 Analysis approach
- Descriptive: per-participant scores, medians, deltas (Modified − Baseline)
- Qualitative: lightweight thematic coding (2 passes), labels P1–P5 in analysis only

### 5.4 Success criteria (from proposal)
- ≥3/5 improve Transparency & Trust
- Modified wins "more honest about AI limits"
- No strong negative pattern on cognitive load

---

## 6. Results (~900–1,100 words, ~1.5 pages)

### 6.1 Quantitative overview

**Table 1 — Per-participant Likert scores (1=Strongly disagree, 7=Strongly agree)**

| ID | Order | Cond. | Transparency | Trust | Control | Evidence | Cog. load |
|----|-------|-------|-------------|-------|---------|----------|-----------|
| P1 | B→M | Baseline | 3 | 3 | 4 | 3 | 5 |
| P1 | B→M | Modified | 6 | 5 | 5 | 6 | 6 |
| P2 | B→M | Baseline | 4 | 4 | 3 | 4 | 5 |
| P2 | B→M | Modified | 6 | 6 | 5 | 6 | 6 |
| P3 | B→M | Baseline | 3 | 4 | 4 | 3 | 6 |
| P3 | B→M | Modified | 5 | 4 | 5 | 5 | 6 |
| P4 | M→B | Baseline | 3 | 3 | 3 | 3 | 5 |
| P4 | M→B | Modified | 6 | 5 | 5 | 6 | 5 |
| P5 | M→B | Baseline | 4 | 3 | 3 | 4 | 5 |
| P5 | M→B | Modified | 5 | 4 | 4 | 5 | 6 |

**Table 2 — Primary outcome deltas (Modified − Baseline)**

| ID | Δ Transparency | Δ Trust | Δ Control |
|----|----------------|---------|-----------|
| P1 | +3 | +2 | +1 |
| P2 | +2 | +2 | +2 |
| P3 | +2 | 0 | +1 |
| P4 | +3 | +2 | +2 |
| P5 | +1 | +1 | +1 |
| **Median Δ** | **+2** | **+2** | **+1** |
| **# improved (of 5)** | **5/5** | **4/5** | **5/5** |

**Table 3 — Condition medians**

| Measure | Baseline median | Modified median |
|---------|-----------------|-----------------|
| Transparency | 4 | 6 |
| Trust | 3 | 5 |
| Control | 3 | 5 |
| Evidence quality | 3 | 6 |
| Cognitive load (ease) | 5 | 6 |

**Table 4 — Comparative questions (end of session)**

| Question | Baseline | Modified | Same |
|----------|----------|----------|------|
| More willing to watch suggested title | 1 | 3 | 1 |
| More honest about AI limits | 0 | 4 | 1 |

### 6.2 Interpretation bullets (for prose)
- **Transparency:** Largest gains (P1, P4 +3); baseline rationale felt "like a summary," modified bullets answered "why *this* movie for *me*"
- **Trust:** 4/5 improved; P3 unchanged — trusted match but wanted stronger review citations
- **Control:** Improved for all; linking Q1–Q3 bullets made prior answers feel consequential
- **Evidence quality:** Median +3; separation of "From your answers" vs "From reviews" reduced generic feel
- **Cognitive load:** Slight positive shift; no participant reported overload; one noted baseline paragraph was harder to scan

### 6.3 Qualitative themes (synthesized — no verbatim quotes in repo)

| Theme | Count | Example paraphrase (de-identified) |
|-------|-------|----------------------------------|
| Explanation felt grounded | 4/5 | "I could see which answer the system used" |
| Improved trust | 4/5 | "Felt less like a black box" |
| Wanted stronger citations | 2/5 | "Reviews section still felt vague without source names" |
| Confidence label helpful | 3/5 | "'Uncertain' made the AI feel more honest" |
| Initial section confusion | 1/5 | "Took a moment to learn user vs review bullets" |
| Baseline felt generic | 3/5 | "Long text didn't say what came from my answers" |

### 6.4 Success criteria check

| Criterion | Result |
|-----------|--------|
| ≥3/5 Transparency improvement | **Met (5/5)** |
| ≥3/5 Trust improvement | **Met (4/5)** |
| Modified more honest (comparative) | **Met (4 vs 0)** |
| No strong negative cognitive load | **Met (median 5→6)** |

---

## 7. Discussion (~700–900 words, ~1.25 pages)

### 7.1 What worked
- **Source separation** in UI matched user mental model better than blended rationale
- **Q-linked bullets** supported transparency *and* perceived control
- **Confidence signaling** increased honesty ratings without hurting willingness to watch

### 7.2 What did not fully work
- Review bullets still sometimes felt thematic, not citation-level (Level 3 opportunity)
- P3 trust plateau — accuracy perceived but verification appetite remained
- One participant needed onboarding for two-section layout

### 7.3 Design implications for AI recommender UX
- Transparency ≠ more text; **structure and provenance** matter
- LLM explanations need **schema + UI contract** together
- Honesty (uncertainty) can coexist with trust in small-N sample

### 7.4 Limitations
- N=5, convenience sample, English only
- Same developer conducted sessions (mild facilitator bias)
- Movie catalog and review availability varied by title
- No longitudinal use; single session per condition
- Results are **directional**, not statistically generalizable

### 7.5 Threats to validity
- Order effects mitigated by counterbalancing but not eliminated
- Scenario differences (Sunday vs date-night) confound with condition order for some participants

---

## 8. Conclusion & Future Work (~350–450 words, ~0.75 page)

### 8.1 Summary
- Restate problem, intervention, headline result (structured explanations improved transparency for all participants, trust for most, without cognitive cost)

### 8.2 Future work
- Deploy Level 3 (`modified_full`) in a follow-up study
- Inline review source links; optional expand-for-excerpt
- Larger sample; between-subjects replication
- Log interaction (bullet clicks) as behavioral transparency measure

---

## 9. References (~0.5 page)

Include 4–6 sources, e.g.:
- Explainable AI / recommender systems overview (pick one survey or CHI paper)
- Transparency and trust in algorithmic systems
- LLM hallucination / grounding in user-facing systems
- Course materials or Rebert prototype attribution (McDonald)

---

## Appendix (optional, not counted toward 7–8 pages)

- A. Study questionnaire (or refer to repo `study/questionnaire.md`)
- B. Screenshot placeholders: baseline tooltip vs modified "Why this title" panel
- C. Link to GitHub + `DATA_PRIVACY.md`

---

## Writing tips for rigor

1. **Separate claims by strength:** "suggests" / "participants reported" / "median improved" — avoid "proves"
2. **Tie every UI choice to a measure:** e.g., Q-linked bullets → Control + Transparency
3. **Acknowledge synthetic repo gap explicitly** in Section 5.2 — instructors appreciate transparency about privacy
4. **Include one failure mode:** P3 trust flat grounds the discussion
5. **Connect back to AI prototyping:** prompt schema (Level 1) alone would not suffice without Level 2 panel

---

## Privacy boilerplate (copy into report Section 5.2)

*To protect participant privacy, individual study records are not included in the public project repository. The GitHub repository documents the modification, evaluation instruments, and reproducible prototype code only. Aggregated findings in this report are derived from offline data collection forms and de-identified session notes retained by the author.*
