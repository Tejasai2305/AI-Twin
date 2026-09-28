"""
Decision Support (Feature 18).

Gemini handles qualitative scoring, justifications, assumptions, and
trade-offs. Weighted totals are recalculated deterministically on the
server so the final arithmetic is always consistent with the supplied
criteria weights.
"""

import json

from backend.ai.gemini_service import ask_gemini


def _build_prompt(options, criteria, weights):
    weights_text = (
        "\n".join(f"- {c}: weight {weights.get(c, 1)}" for c in criteria)
        if weights
        else "\n".join(f"- {c}: equal weight" for c in criteria)
    )

    options_text = "\n".join(f"{i + 1}. {opt}" for i, opt in enumerate(options))
    criteria_text = "\n".join(f"- {c}" for c in criteria)

    return f"""
You are a decision-support assistant. Compare the options below using
ONLY the criteria the user gave you.

STRICT RULES:
- Do not assume anything about the user's personal preferences, goals,
  skills, or circumstances.
- You may use reliable general knowledge about recognizable options when
  that knowledge is relevant to the criterion.
- Do not invent specific facts, specifications, prices, measurements, or
  claims when you do not have reliable knowledge of them.
- When reliable information is unavailable, explicitly say that the
  criterion cannot be determined from the available information instead
  of pretending to know it.
- Score each option on each criterion from 1 (worst) to 10 (best).
- Scores should reflect meaningful differences between options when
  reliable evidence supports those differences. Do not give every option
  5/10 merely because the input is brief.
- Use a neutral score only when there is genuinely insufficient information
  to distinguish the options.
- Give one short justification per score explaining the evidence or
  uncertainty behind the score.
- Clearly list any assumptions you had to make to score something.
- List genuine trade-offs between the top options.
- Return ONLY valid JSON. No markdown, no code fences, no commentary.

IMPORTANT:
- "weighted_total" will be recalculated by the application from the
  individual scores and supplied weights.
- Do not try to estimate or override the weighted total.

OPTIONS:
{options_text}

CRITERIA (with weights, higher = more important):
{weights_text}

Return JSON in exactly this shape:
{{
  "options": [
    {{
      "name": "<option text>",
      "scores": {{"<criterion>": {{"score": <1-10>, "justification": "<short reason>"}}, ...}},
      "weighted_total": 0
    }}
  ],
  "assumptions": ["<assumption 1>", "..."],
  "trade_offs": ["<trade-off 1>", "..."],
  "recommendation": "<one sentence, or 'No clear winner - it depends on X' if genuinely close>"
}}

CRITERIA LIST (for reference): {criteria_text}
"""


def _recalculate_weighted_totals(data, criteria, weights):
    """
    Calculate weighted totals deterministically.

    Formula:
        weighted_total = sum(score × criterion_weight)

    This prevents LLM arithmetic errors from reaching the UI.
    """
    for option in data.get("options", []):
        scores = option.get("scores", {})
        total = 0.0

        for criterion in criteria:
            criterion_result = scores.get(criterion, {})

            if not isinstance(criterion_result, dict):
                continue

            score = criterion_result.get("score")

            try:
                score = float(score)
            except (TypeError, ValueError):
                continue

            weight = weights.get(criterion, 1)

            try:
                weight = float(weight)
            except (TypeError, ValueError):
                weight = 1.0

            total += score * weight

        option["weighted_total"] = (
            int(total) if total.is_integer() else round(total, 2)
        )

    return data


def compare_options(options, criteria, weights=None):
    if not options or len(options) < 2:
        raise ValueError("At least two options are required to compare.")

    if not criteria:
        raise ValueError("At least one criterion is required.")

    weights = weights or {}

    prompt = _build_prompt(options, criteria, weights)

    try:
        text = ask_gemini(prompt).strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        if not text.startswith("{"):
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                text = text[start:end + 1]

        data = json.loads(text)

        if not isinstance(data, dict) or "options" not in data:
            raise ValueError("Malformed comparison response.")

        data = _recalculate_weighted_totals(data, criteria, weights)

        return data

    except (json.JSONDecodeError, ValueError) as e:
        print("Decision support parse error:", e)
        return {
            "options": [],
            "assumptions": [],
            "trade_offs": [],
            "recommendation": None,
            "error": "Unable to generate a structured comparison. Please try rephrasing your options or criteria.",
        }

