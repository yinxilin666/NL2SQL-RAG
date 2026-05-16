import re
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    is_valid: bool = True
    warnings: list[str] = field(default_factory=list)


FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
    (r"\bILIKE\b", "ILIKE is not supported in Hive; use LIKE or LOWER(col) LIKE"),
    (r"\bSIMILAR\s+TO\b", "SIMILAR TO is not supported in Hive"),
    (r"\bARRAY_AGG\b", "ARRAY_AGG not supported; use COLLECT_LIST instead"),
    (r"\bSTRING_AGG\b", "STRING_AGG not supported; use CONCAT_WS with COLLECT_LIST"),
    (r"\bLISTAGG\b", "LISTAGG not supported in Hive"),
    (r"\bUNNEST\b", "UNNEST is not Hive syntax; use LATERAL VIEW EXPLODE"),
    (r"\bGETDATE\b", "GETDATE() not supported; use CURRENT_DATE"),
    (r"::\w+", "PostgreSQL-style cast (::type) not supported; use CAST(expr AS type)"),
    (r"\bSERIAL\b", "SERIAL pseudo-type not supported in Hive"),
    (r"\bIDENTITY\b", "IDENTITY not supported in Hive"),
    (r"\bNOW\(\)", "NOW() not standard in Hive; use CURRENT_TIMESTAMP"),
    (r"\bIIF\b", "IIF not supported; use CASE WHEN ... THEN ... ELSE ... END"),
    (r"\bDECODE\b", "DECODE not supported; use CASE WHEN"),
    (r"\|\|", "|| string concatenation may not work in Hive; use CONCAT() instead"),
]


def validate_hive_sql(sql: str | None) -> ValidationResult:
    if sql is None:
        return ValidationResult(is_valid=False, warnings=["No SQL generated"])

    warnings = []
    for pattern, message in FORBIDDEN_PATTERNS:
        if re.search(pattern, sql, re.IGNORECASE):
            warnings.append(message)

    return ValidationResult(
        is_valid=len(warnings) == 0,
        warnings=warnings,
    )
