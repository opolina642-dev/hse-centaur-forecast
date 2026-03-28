#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Конкурс «Кентавры нашего времени» — НИУ ВШЭ / Лаборатория «Молодёжная политика»
Задача: спрогнозировать заголовки СМИ на 2 апреля 2026 года
Модель: openai/gpt-4o (через OpenRouter)
Автор: Обухова Полина Олеговна
"""

import os
import re
import json
from datetime import datetime

import requests

# ─────────────────────────────────────────────
# 1. CONFIG
# ─────────────────────────────────────────────
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise ValueError("OPENROUTER_API_KEY не задан")

MODEL = "openai/gpt-4o"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://extra.hse.ru",
    "X-Title": "HSE Centaur News Forecast 2026",
}

# ─────────────────────────────────────────────
# 2. SYSTEM PROMPTS
# ─────────────────────────────────────────────
GENERATION_SYSTEM_PROMPT = """You are an experienced international news editor.

TASK:
Create a realistic forecast of a news item that could be published on April 2, 2026 by the specified outlet.

STRICT RULES:
1. The output language MUST exactly match the requested language.
2. Use ONLY facts explicitly present in the provided context.
3. Do NOT invent quotes, locations, numbers, outcomes, delays, injuries, statements or decisions that are not in the context.
4. Match the outlet's style closely.
5. Headline: maximum 12 words.
6. Lead: 3–5 sentences, about 80–120 words.
7. Avoid exaggerated language and avoid generic filler.
8. If the context says that something is not fully confirmed, preserve that uncertainty.

OUTPUT FORMAT:
**HEADLINE:** ...
**LEAD:** ...
"""

REWRITE_SYSTEM_PROMPT = """You are a strict copy editor and fact-checking editor.

TASK:
Rewrite the draft so that:
1. The language exactly matches the requested language.
2. The style matches the outlet.
3. Every factual element is supported by the provided context.
4. Unsupported details are removed.
5. The text remains natural, concise and news-like.

DO NOT:
- add new facts
- add quotes not present in the context
- add specific numbers unless they are in the context
- change the topic

OUTPUT FORMAT:
**HEADLINE:** ...
**LEAD:** ...
"""

# ─────────────────────────────────────────────
# 3. FORECASTS WITH SEPARATE VERIFIED CONTEXTS
# ─────────────────────────────────────────────
forecasts = [
    {
        "id": 1,
        "outlet": "UN News",
        "language": "English",
        "tone": "official UN informative and rights-based style",
        "context": """
[WORLD AUTISM AWARENESS DAY]
- April 2 is World Autism Awareness Day, a UN observance.
- UN observance pages list the 2026 event on Thursday, 2 April 2026.
- The 2026 theme is "Autism and Humanity – Every Life Has Value".
- WHO says that in 2021 about 1 in 127 persons had autism.
- WHO says care for autistic people needs greater accessibility, inclusivity and support.
- A strong likely angle is dignity, inclusion, rights and access to support.
""",
        "user_prompt": """Publication date: April 2, 2026.
Outlet: UN News.
Language: English.
Topic: World Autism Awareness Day 2026.
Specifics: official UN tone; focus on dignity, inclusion, rights, accessibility, support and the official 2026 theme.
Generate a realistic headline and lead."""
    },
    {
        "id": 2,
        "outlet": "Financial Times",
        "language": "English",
        "tone": "analytical business and economics style",
        "context": """
[ONE YEAR AFTER TRUMP'S APRIL 2, 2025 TARIFFS]
- On April 2, 2025, the White House issued a presidential action titled:
  "Regulating Imports with a Reciprocal Tariff to Rectify Trade Practices that Contribute to Large and Persistent Annual United States Goods Trade Deficits".
- The White House text says Trump declared a national emergency linked to large and persistent U.S. goods trade deficits.
- Reuters reported on April 2, 2025 that Trump unveiled global reciprocal tariffs at the White House.
- Reuters also reported that the new scheme included a baseline tariff of 10% and higher rates for some major trading partners.
- AP described April 2 as "Liberation Day", reflecting Trump's own framing.
- A realistic one-year lookback angle is global trade, supply chains, investor uncertainty and inflation pressure.
""",
        "user_prompt": """Publication date: April 2, 2026.
Outlet: Financial Times.
Language: English.
Topic: One year after Trump's April 2, 2025 reciprocal tariffs.
Specifics: analytical business angle; focus on trade, supply chains, inflation pressure, business adaptation and uncertainty one year later.
Generate a realistic headline and lead."""
    },
    {
        "id": 3,
        "outlet": "ТАСС",
        "language": "Russian",
        "tone": "official Russian state-agency style",
        "context": """
[ДЕНЬ ЕДИНЕНИЯ НАРОДОВ БЕЛАРУСИ И РОССИИ]
- День единения народов Беларуси и России ежегодно отмечается 2 апреля.
- Союзный ресурс soyuz.by пишет, что 2 апреля 1997 года был подписан Договор об образовании Сообщества Беларуси и России, и с тех пор 2 апреля отмечается как День единения.
- BelTA сообщала, что в 2025 году в Минске и Москве проходили мероприятия по случаю этой даты.
- Belarus.by публиковал поздравление Александра Лукашенко, где 2 апреля описывается как символ братства, общей истории и духовной близости.
- Наиболее вероятный угол освещения: официальные поздравления, символическое значение даты, интеграция, Союзное государство, совместные мероприятия.
""",
        "user_prompt": """Дата публикации: 2 апреля 2026.
Издание: ТАСС.
Язык: русский.
Тема: День единения народов Беларуси и России.
Специфика: официальный стиль, акцент на символическом значении даты, союзнических отношениях, интеграции и мероприятиях.
Сгенерируй реалистичный заголовок и первый абзац."""
    },
    {
        "id": 4,
        "outlet": "UEFA.com",
        "language": "English",
        "tone": "official football reporting style",
        "context": """
[UEFA WOMEN'S CHAMPIONS LEAGUE QUARTER-FINAL SECOND LEGS]
- UEFA's official fixtures list Thursday 2 April 2026 as the day of quarter-finals, second legs.
- Barcelona host Real Madrid on April 2 at 18:45 CET.
- UEFA's first-leg report shows Real Madrid 2-6 Barcelona.
- OL Lyonnes host Wolfsburg on April 2 at 21:00 CET.
- UEFA's official fixtures/results page shows Wolfsburg leading that tie 1-0 after the first leg.
- A realistic angle is a preview or day-of-match piece focused on aggregate scorelines, comeback pressure and the race for the semi-finals.
""",
        "user_prompt": """Publication date: April 2, 2026.
Outlet: UEFA.com.
Language: English.
Topic: UEFA Women's Champions League quarter-final second legs.
Specifics: Barcelona vs Real Madrid and OL Lyonnes vs Wolfsburg. Use official match-centre or preview style, with focus on aggregate scores and semi-final stakes.
Generate a realistic headline and lead."""
    },
    {
        "id": 5,
        "outlet": "Reuters",
        "language": "English",
        "tone": "neutral, concise wire-service style",
        "context": """
[NASA / ARTEMIS II / SLS]
- Artemis II is NASA's first crewed Artemis mission and a crewed lunar flyby mission.
- NASA says launch is targeted no earlier than April 1, 2026.
- NASA says the target time is no earlier than 6:24 p.m. EDT on Wednesday, April 1, with additional launch opportunities through Monday, April 6.
- NASA says the crew is Reid Wiseman, Victor Glover, Christina Koch and Jeremy Hansen.
- NASA says the mission will be about 10 days around the Moon.
- Reuters reported on March 27, 2026 that the Artemis II astronauts were in final preparations for a launch around April 1.
- A realistic Reuters angle for April 2 is launch-window coverage, second-window coverage, or a significance/explainer piece about the mission.
- It is NOT confirmed in the context that NASA fixed the launch exactly on April 2.
- It is also NOT confirmed in the context that an April 1 launch attempt failed due to weather.
""",
        "user_prompt": """Publication date: April 2, 2026.
Outlet: Reuters.
Language: English.
Topic: NASA Artemis II / SLS Moon mission.
Specifics: Reuters wire style. Use only the provided facts. Preserve uncertainty if the launch timing remains within a window.
Generate a realistic headline and lead."""
    },
]

# ─────────────────────────────────────────────
# 4. HELPERS
# ─────────────────────────────────────────────
def chat_completion(system_prompt: str, user_prompt: str, temperature: float = 0.25, max_tokens: int = 500) -> dict:
    response = requests.post(
        OPENROUTER_URL,
        headers=HEADERS,
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.9,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def generate_draft(forecast: dict) -> tuple[str, int]:
    user_message = (
        f"Outlet: {forecast['outlet']}\n"
        f"Language: {forecast['language']}\n"
        f"Tone: {forecast['tone']}\n\n"
        f"Context:\n{forecast['context']}\n\n"
        f"Assignment:\n{forecast['user_prompt']}"
    )
    data = chat_completion(GENERATION_SYSTEM_PROMPT, user_message, temperature=0.25, max_tokens=500)
    text = data["choices"][0]["message"]["content"]
    tokens = data.get("usage", {}).get("total_tokens", 0)
    return text, tokens


def rewrite_draft(forecast: dict, draft: str) -> tuple[str, int]:
    user_message = (
        f"Outlet: {forecast['outlet']}\n"
        f"Language: {forecast['language']}\n"
        f"Tone: {forecast['tone']}\n\n"
        f"Context:\n{forecast['context']}\n\n"
        f"Draft to repair:\n{draft}\n\n"
        f"Please rewrite the draft so it strictly follows the context and the outlet style."
    )
    data = chat_completion(REWRITE_SYSTEM_PROMPT, user_message, temperature=0.1, max_tokens=500)
    text = data["choices"][0]["message"]["content"]
    tokens = data.get("usage", {}).get("total_tokens", 0)
    return text, tokens


# ─────────────────────────────────────────────
# 5. MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    results = []

    for fc in forecasts:
        print(f"\n{'=' * 65}")
        print(f"  #{fc['id']}  {fc['outlet']}  ({fc['language']})")
        print("=" * 65)

        try:
            draft_text, draft_tokens = generate_draft(fc)
            final_text, rewrite_tokens = rewrite_draft(fc, draft_text)

            total_tokens = draft_tokens + rewrite_tokens

            result = {
                "id": fc["id"],
                "outlet": fc["outlet"],
                "language": fc["language"],
                "model": MODEL,
                "tone": fc["tone"],
                "context": fc["context"].strip(),
                "user_prompt": fc["user_prompt"].strip(),
                "draft_forecast": draft_text,
                "forecast": final_text,
                "tokens_used": total_tokens,
                "generated_at": datetime.now().isoformat(),
            }

            results.append(result)
            print(final_text)
            print(f"\n[Total tokens: {total_tokens}]")

        except requests.HTTPError as e:
            print(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            print(f"Error: {e}")

    output_path = "forecasts_april2_2026.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nAll forecasts saved to {output_path}")
