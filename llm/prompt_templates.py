from typing import List

from config.constants import CHUNK_TYPE_FIELD, CHUNK_TYPE_RELATIONSHIP, CHUNK_TYPE_TABLE

SYSTEM_PROMPT = """You are a Hive SQL expert. Given database schema context, generate a valid HiveQL SELECT query that answers the user's question.

**HiveQL Dialect Rules:**
1. Use CONCAT(a, b, c) for string concatenation, not || or +
2. Date functions: DATE_ADD(date, n_days), DATE_SUB(date, n_days), DATEDIFF(end, start), TO_DATE(str)
3. Current date uses CURRENT_DATE, not GETDATE() or NOW()
4. Extract date parts: YEAR(date), MONTH(date), DAY(date), HOUR(ts), MINUTE(ts)
5. Type casting: CAST(expr AS TYPE). The ::TYPE shorthand is NOT supported.
6. NULL handling: COALESCE(expr, default) or NVL(expr, default)
7. Conditional: CASE WHEN ... THEN ... ELSE ... END
8. Window functions: ROW_NUMBER() OVER(PARTITION BY ... ORDER BY ...)
9. Top-N: SELECT * FROM (SELECT ..., ROW_NUMBER() OVER(...) rn FROM ...) t WHERE rn <= N
10. LIMIT goes at the very end of the query
11. Use explicit JOIN ... ON for table joins
12. LATERAL VIEW EXPLODE(array_col) alias AS col_alias for arrays/maps
13. No ILIKE, SIMILAR TO, ARRAY_AGG, STRING_AGG, UNNEST

**Output Rules:**
- Generate ONLY SELECT statements. Never INSERT, UPDATE, DELETE, DROP, TRUNCATE, ALTER.
- Use table aliases: FROM orders o, LEFT JOIN customers c ON ...
- Quote identifiers with backticks only when they contain special characters.
- If the question is ambiguous, make a reasonable assumption and note it in an SQL comment.
- If NO relevant schema is found, output: -- Unable to generate SQL: no matching schema found
"""

FEW_SHOT_EXAMPLES = """
=== Example 1 ===
User: List all orders from last month with customer names.
Schema context:
  Table: orders | Fields: order_id (BIGINT), customer_id (STRING), order_date (DATE), total_amount (DECIMAL(10,2)), status (STRING)
  Table: customers | Fields: customer_id (STRING), customer_name (STRING), region (STRING)
<think>
I need orders from last month. Using CURRENT_DATE, I calculate: first day of last month = DATE_ADD(LAST_DAY(DATE_ADD(CURRENT_DATE, -2)), 1), last day of last month = LAST_DAY(DATE_ADD(CURRENT_DATE, -1)). Join orders with customers on customer_id. LEFT JOIN is safer in case customer_id is missing in customers.
</think>
<sql>
SELECT o.order_id, c.customer_name, o.order_date, o.total_amount
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date >= DATE_ADD(LAST_DAY(DATE_ADD(CURRENT_DATE, -2)), 1)
  AND o.order_date < DATE_ADD(LAST_DAY(DATE_ADD(CURRENT_DATE, -1)), 1);
</sql>

=== Example 2 ===
User: Count how many users registered each day this week.
Schema context:
  Table: user_info | Fields: user_id (BIGINT), mobile (STRING), register_time (TIMESTAMP), status (STRING)
<think>
This week means from the most recent Monday to today. I need to group by DATE(register_time) and count DISTINCT user_id. Use DATE() to extract the date part from TIMESTAMP.
</think>
<sql>
SELECT DATE(register_time) AS reg_date, COUNT(DISTINCT user_id) AS user_cnt
FROM user_info
WHERE register_time >= DATE_SUB(CURRENT_DATE, PMOD(DATEDIFF(CURRENT_DATE, '1900-01-01') - 1, 7))
  AND register_time < DATE_ADD(CURRENT_DATE, 1)
GROUP BY DATE(register_time)
ORDER BY reg_date;
</sql>
"""


def build_prompt(
    user_query: str,
    retrieved_chunks: List[dict],
    few_shot: bool = True,
) -> str:
    tables_seen: set[str] = set()
    schema_lines: list[str] = []

    for chunk in retrieved_chunks:
        meta = chunk.get("metadata", {})
        chunk_type = meta.get("chunk_type", "")

        if chunk_type == CHUNK_TYPE_TABLE:
            if meta["table"] not in tables_seen:
                tables_seen.add(meta["table"])
                schema_lines.append(chunk["text"])
        elif chunk_type == CHUNK_TYPE_FIELD:
            schema_lines.append(chunk["text"])

    schema_context = "\n\n".join(schema_lines) if schema_lines else "(No schema found for this query)"

    rel_lines = [
        c["text"] for c in retrieved_chunks
        if c.get("metadata", {}).get("chunk_type") == CHUNK_TYPE_RELATIONSHIP
    ]
    relationship_context = "\n".join(rel_lines) if rel_lines else "No cross-table relationships identified."

    prompt_parts = [SYSTEM_PROMPT]

    if few_shot:
        prompt_parts.append(FEW_SHOT_EXAMPLES)

    prompt_parts.append(f"""
=== SCHEMA CONTEXT ===
{schema_context}

=== RELATIONSHIP HINTS ===
{relationship_context}

=== USER QUESTION ===
{user_query}

=== INSTRUCTION ===
First, reason step-by-step inside <think> tags. Then output the final SQL inside a single <sql> tag.

<think>
- Identify which tables and fields are relevant.
- Determine the join conditions.
- Determine the filter and aggregation logic.
- Consider Hive-specific syntax.
</think>
<sql>
-- Your HiveQL query here
</sql>
""")

    return "\n".join(prompt_parts)
