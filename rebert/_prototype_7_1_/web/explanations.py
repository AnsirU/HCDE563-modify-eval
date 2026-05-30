#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#   FILE: explanations.py
#   Grounded, user-linked explanation parsing and formatting for Rebert p7.1
#
import re


def create_ephem_qna_str_numbered(session=None):
    """Build Q&A text with Q1/Q2/Q3 labels for explanation linking."""
    qna_str = ""
    for i in range(1, 4):
        prompt = session["ephem_status"][str(i)]["prompt"]
        response = session["ephem_status"][str(i)]["response"]
        if response:
            qna_str += f"Q{i} QUESTION:\n\t{prompt}\n"
            qna_str += f"Q{i} ANSWER:\n\t{response}\n"
    return qna_str + "\n"


def create_review_excerpt_str(review_list=None, max_reviews=3, max_chars=280):
    """Level 3: pass trimmed review excerpts with stable IDs into the LLM prompt."""
    if not review_list:
        return ""
    excerpt_str = ""
    for idx, review in enumerate(review_list[:max_reviews]):
        excerpt_id = f"R{idx + 1}"
        review_text = (review.get("review") or "").strip()
        if len(review_text) > max_chars:
            review_text = review_text[:max_chars].rstrip() + "..."
        data = (
            f"EXCERPT_ID: {excerpt_id}\n"
            f"REVIEW OF: {review.get('title', '')}\n"
            f"REVIEW AUTHOR: {review.get('author', '')}\n"
            f"REVIEW SOURCE: {review.get('source', '')}\n"
            f"EXCERPT TEXT: {review_text}\n"
        )
        excerpt_str = data if not excerpt_str else excerpt_str + "\n" + data
    return excerpt_str


def _parse_tag_block(content, tag_name):
    open_tag = f"<{tag_name}>"
    close_tag = f"</{tag_name}>"
    block = content.partition(open_tag)[2]
    block = block.partition(close_tag)[0]
    return block.strip()


def _parse_bullets(block):
    bullets = []
    if not block:
        return bullets
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^[-*•]\s*", "", line).strip()
        if line:
            bullets.append(line)
    return bullets


def _parse_user_alignment_bullets(block):
    parsed = []
    for line in _parse_bullets(block):
        q_index = None
        text = line
        match = re.match(r"^Q([1-3])\s*:\s*(.+)$", line, flags=re.IGNORECASE)
        if match:
            q_index = int(match.group(1))
            text = match.group(2).strip()
        parsed.append({"q_index": q_index, "text": text})
    return parsed


def _parse_review_basis_bullets(block):
    parsed = []
    for line in _parse_bullets(block):
        excerpt_id = None
        text = line
        match = re.match(r"^(R[1-3])\s*:\s*(.+)$", line, flags=re.IGNORECASE)
        if match:
            excerpt_id = match.group(1).upper()
            text = match.group(2).strip()
        parsed.append({"excerpt_id": excerpt_id, "text": text})
    return parsed


def parse_structured_explanation(content):
    """Extract structured explanation sections from an LLM response."""
    explanation = {
        "user_alignment": [],
        "review_basis": [],
        "confidence": "",
        "confidence_detail": "",
    }
    if not content:
        return explanation

    user_block = _parse_tag_block(content, "USER_ALIGNMENT")
    review_block = _parse_tag_block(content, "REVIEW_BASIS")
    confidence_block = _parse_tag_block(content, "CONFIDENCE")

    explanation["user_alignment"] = _parse_user_alignment_bullets(user_block)
    explanation["review_basis"] = _parse_review_basis_bullets(review_block)

    if confidence_block:
        if "—" in confidence_block:
            label, _, detail = confidence_block.partition("—")
            explanation["confidence"] = label.strip().lower()
            explanation["confidence_detail"] = detail.strip()
        elif "-" in confidence_block and confidence_block.count("-") == 1:
            label, detail = confidence_block.split("-", 1)
            explanation["confidence"] = label.strip().lower()
            explanation["confidence_detail"] = detail.strip()
        else:
            explanation["confidence"] = confidence_block.split()[0].strip().lower()
            explanation["confidence_detail"] = confidence_block.strip()

    return explanation


def format_explanation_for_tooltip(explanation):
    """Compact multi-line text for recommendation flag tooltips."""
    if not explanation:
        return ""
    lines = []
    if explanation.get("confidence"):
        detail = explanation.get("confidence_detail", "")
        if detail:
            lines.append(f"Confidence: {explanation['confidence']} — {detail}")
        else:
            lines.append(f"Confidence: {explanation['confidence']}")

    if explanation.get("user_alignment"):
        lines.append("From your answers:")
        for bullet in explanation["user_alignment"]:
            prefix = f"Q{bullet['q_index']}: " if bullet.get("q_index") else ""
            lines.append(f"• {prefix}{bullet['text']}")

    if explanation.get("review_basis"):
        lines.append("From reviews:")
        for bullet in explanation["review_basis"]:
            prefix = f"{bullet['excerpt_id']}: " if bullet.get("excerpt_id") else ""
            lines.append(f"• {prefix}{bullet['text']}")

    return "\n".join(lines)


def empty_explanation():
    return {
        "user_alignment": [],
        "review_basis": [],
        "confidence": "",
        "confidence_detail": "",
    }
