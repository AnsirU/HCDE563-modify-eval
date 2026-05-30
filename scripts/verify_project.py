#!/usr/bin/env python3
"""Smoke-test baseline vs modified explanation modes (no OpenAI calls)."""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def run_parser_tests():
    from rebert._prototype_7_1_.web.explanations import (
        parse_structured_explanation,
        format_explanation_for_tooltip,
        create_review_excerpt_str,
        create_ephem_qna_str_numbered,
    )

    sample = """
<MATCH>HIGHLY MATCHED</MATCH>
<RATIONALE>Good fit for your mood.</RATIONALE>
<USER_ALIGNMENT>
Q1: You wanted something relaxing for a quiet evening.
Q2: You prefer character-focused stories over action.
</USER_ALIGNMENT>
<REVIEW_BASIS>
R1: Reviews describe a gentle pace and warm performances.
</REVIEW_BASIS>
<CONFIDENCE>high — strong match to stated preferences</CONFIDENCE>
"""
    ex = parse_structured_explanation(sample)
    assert len(ex["user_alignment"]) == 2
    assert ex["user_alignment"][0]["q_index"] == 1
    assert ex["confidence"] == "high"
    tooltip = format_explanation_for_tooltip(ex)
    assert "Q1:" in tooltip

    excerpts = create_review_excerpt_str(
        [
            {
                "title": "Test Film",
                "author": "Critic A",
                "source": "Example",
                "review": "A" * 400,
            }
        ]
    )
    assert "EXCERPT_ID: R1" in excerpts
    assert len(excerpts) < 400 + 200

    session = {
        "ephem_status": {
            "1": {"prompt": "What mood?", "response": "Relaxed"},
            "2": {"prompt": "Genre?", "response": "Drama"},
            "3": {"prompt": "Length?", "response": "Short"},
        }
    }
    numbered = create_ephem_qna_str_numbered(session)
    assert "Q1 QUESTION" in numbered
    return "parser + excerpt + numbered Q&A"


def run_mode_tests():
    results = []

    os.environ["REBERT_EXPLANATION_MODE"] = "baseline"
    import importlib
    import rebert._prototype_7_1_.web.config as cfg

    importlib.reload(cfg)
    assert cfg.REBERT_GROUNDED_EXPLANATIONS is False
    results.append("baseline: grounded explanations OFF")

    os.environ["REBERT_EXPLANATION_MODE"] = "modified"
    importlib.reload(cfg)
    assert cfg.REBERT_GROUNDED_EXPLANATIONS is True
    assert cfg.REBERT_REVIEW_EXCERPT_IDS is False
    results.append("modified: grounded explanations ON")

    os.environ["REBERT_EXPLANATION_MODE"] = "modified_full"
    importlib.reload(cfg)
    assert cfg.REBERT_REVIEW_EXCERPT_IDS is True
    results.append("modified_full: review excerpt IDs ON")

    import rebert._prototype_7_1_.web.llm as llm

    importlib.reload(llm)
    q = llm.build_ephem_recommendation_user_question("Example Movie")
    assert "<USER_ALIGNMENT>" in q
    results.append("modified: recommendation prompt includes structured tags")
    return results


def main():
    print("=== HCDE563 Rebert Explanation Verification ===\n")
    ok = []
    ok.append(run_parser_tests())
    ok.extend(run_mode_tests())
    for line in ok:
        print(f"  PASS  {line}")
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
