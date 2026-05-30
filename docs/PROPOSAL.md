# Course Project Proposal (Modified)

**Project:** Grounded, User-Linked Explanations for AI Movie Recommendations  
**Starting Prototype:** Rebert Prototype 7.1 (p7.1)  
**Author:** Zhian Hu  
**Course:** HCDE 563  
**Date:** May 13, 2026

## Problem to Address

The starting prototype is Rebert Prototype 7.1, a Flask web app that supports LLM-based movie recommendation, an “Ask Rebert” chat interface, ephemeral preference questions before recommendation, multi-source review collection, TMDB-grounded movie metadata, and optional voice or text movie-rating flows.

The problem addressed is **recommendation opacity**. In Rebert 7.1, the system can recommend movies using a combination of user answers, collected reviews, and LLM-generated language, but the user cannot easily tell why a specific movie was suggested. This creates an AI-centered UX problem: users may not know whether the recommendation is grounded in their inputs or in actual review evidence.

## Modifications (Implemented)

| Level | Status | Summary |
|-------|--------|---------|
| Level 1 | Done | Structured LLM output: user alignment, review basis, confidence guardrails |
| Level 2 | Done | “Why this title” panel + click-to-highlight linked Q&A answers |
| Level 3 | Optional | Review excerpts with IDs (`R1`, `R2`, …) via `REBERT_EXPLANATION_MODE=modified_full` |

## Evaluation Plan

Within-subjects, counterbalanced A/B comparison (~5 participants):

- **Baseline:** `REBERT_EXPLANATION_MODE=baseline`
- **Modified:** `REBERT_EXPLANATION_MODE=modified`

Primary outcomes: transparency, trust, control/steerability.  
Instruments and procedure: see [`../study/evaluation_protocol.md`](../study/evaluation_protocol.md).

## Success Criteria

- ≥3/5 participants improve on Transparency
- ≥3/5 participants improve on Trust
- Modified chosen more often on “more honest about AI limits”
- No strong negative pattern on cognitive load
