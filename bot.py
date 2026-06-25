def ai_translate(text):

    prompt = f"""
Translate Persian ↔ German.

If word:
- translation
- article (if noun)
- plural (if noun)
- pronunciation in English phonetic + Persian phonetic

If sentence:
- full translation
- pronunciation of main words

NO examples
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "German teacher"},
            {"role": "user", "content": prompt + "\n" + text}
        ]
    )

    return res.choices[0].message.content
