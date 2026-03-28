# hse-centaur-forecast
Прогнозирование заголовков СМИ на 2 апреля 2026 — конкурс лаборатории Молодежная политика ВШЭ

## Что делает этот код
Python-скрипт генерирует 5 краткосрочных прогнозов новостных публикаций на 2 апреля 2026 года для разных СМИ.

## Темы
1. World Autism Awareness Day
2. One year after Trump’s tariffs of April 2, 2025
3. Day of Unity of the Peoples of Belarus and Russia
4. UEFA Women’s Champions League quarter-final second legs
5. NASA Artemis II / SLS launch window

## Какая модель использовалась
openai/gpt-4o via OpenRouter

## Как работает
Для каждой темы используется отдельно подготовленный фактологический контекст из открытых источников.
Скрипт отправляет запрос к LLM, получает черновой прогноз, затем прогоняет второй этап редактирования для улучшения языка, стиля и соответствия фактам.

## Файл
- `forecast_april2_2026.py` — основной скрипт

## Как запускать
Нужно задать переменную окружения `OPENROUTER_API_KEY`, затем запустить:

```bash
python forecast_april2_2026.py
