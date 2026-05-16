import re
from typing import Optional


def strip_code_fences(text: str) -> str:
    text = re.sub(r"```(?:sql|hive)?\s*\n?", "", text)
    text = re.sub(r"\n?```", "", text)
    return text.strip()


def parse_llm_response(raw_output: str) -> dict:
    """Extract reasoning and SQL from deepseek-r1 output.

    Returns: {'reasoning': str|None, 'sql': str|None, 'raw': str}
    """
    reasoning: Optional[str] = None
    sql: Optional[str] = None

    # Extract reasoning from think/thinking tag
    think_match = re.search(
        r"<(?:think|thinking)>(.*?)</(?:think|thinking)>",
        raw_output,
        re.DOTALL | re.IGNORECASE,
    )
    if think_match:
        reasoning = think_match.group(1).strip()
        cleaned = re.sub(
            r"<(?:think|thinking)>.*?</(?:think|thinking)>",
            "",
            raw_output,
            flags=re.DOTALL | re.IGNORECASE,
        )
    else:
        cleaned = raw_output

    # Extract SQL from sql/query tag
    sql_match = re.search(
        r"<(?:sql|sql_query|query)>(.*?)</(?:sql|sql_query|query)>",
        cleaned,
        re.DOTALL | re.IGNORECASE,
    )
    if sql_match:
        sql = sql_match.group(1).strip()
        sql = strip_code_fences(sql)
    else:
        cleaned = strip_code_fences(cleaned)
        # Fallback: find first SELECT statement
        fallback = re.search(
            r"\b(SELECT|WITH)\b.*?(?:;|$)",
            cleaned,
            re.DOTALL | re.IGNORECASE,
        )
        if fallback:
            sql = fallback.group(0).strip()

    # Detect refusal
    refusal_phrases = [
        "i cannot", "i am unable", "i'm unable", "not appropriate",
        "cannot generate", "unable to generate",
    ]
    if sql is None and any(p in raw_output.lower() for p in refusal_phrases):
        sql = "-- Unable to generate SQL: no matching schema found"

    return {"reasoning": reasoning, "sql": sql, "raw": raw_output}
