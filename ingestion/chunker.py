import re
from typing import Dict, List

from config.constants import CHUNK_TYPE_FIELD, CHUNK_TYPE_RELATIONSHIP, CHUNK_TYPE_TABLE
from ingestion.loader import TableSchema


def build_table_chunk(table: TableSchema) -> dict:
    fields_summary = "\n".join(
        f"  - {f.column_name} ({f.column_type}): {f.column_comment or '(no comment)'}"
        for f in table.fields
    )
    text = (
        f" Table: {table.table}\n"
        f"Subsystem: {table.subs_code}\n"
        f"Description: {table.table_comment or '(no description)'}\n"
        f"Fields ({len(table.fields)}):\n{fields_summary}"
    )
    return {
        "id": f"table::{table.table}",
        "text": text,
        "metadata": {
            "chunk_type": CHUNK_TYPE_TABLE,
            "table": table.table,
            "subs_code": table.subs_code,
        },
    }


def build_field_chunks(table: TableSchema) -> list[dict]:
    chunks = []
    for f in table.fields:
        text = (
            f"The field `{f.column_name}` in table `{table.table}` "
            f"(subsystem: {table.subs_code}) is of type {f.column_type}. "
            f"It represents: {f.column_comment or '(no description)'}."
        )
        chunks.append({
            "id": f"field::{table.table}::{f.column_name}",
            "text": text,
            "metadata": {
                "chunk_type": CHUNK_TYPE_FIELD,
                "table": table.table,
                "column_name": f.column_name,
                "column_type": f.column_type,
                "subs_code": table.subs_code,
            },
        })
    return chunks


def _normalize(name: str) -> str:
    n = name.lower().strip()
    n = re.sub(r"_(id|cd|nm|no|dt|dttm|flag|cnt|amt|key|code)$", "", n)
    return n


def build_relationship_chunks(tables: list[TableSchema]) -> list[dict]:
    """Heuristic cross-table relationship hints based on field name similarity."""
    chunks: list[dict] = []
    norm_map: Dict[str, list[tuple[str, str]]] = {}

    for t in tables:
        for f in t.fields:
            norm = _normalize(f.column_name)
            norm_map.setdefault(norm, []).append((t.table, f.column_name))

    for norm, occurrences in norm_map.items():
        unique_tables = list({t for t, _ in occurrences})
        if len(unique_tables) < 2:
            continue

        for i in range(len(unique_tables)):
            for j in range(i + 1, len(unique_tables)):
                cols_a = [c for t, c in occurrences if t == unique_tables[i]]
                cols_b = [c for t, c in occurrences if t == unique_tables[j]]
                text = (
                    f"Relationship hint: tables `{unique_tables[i]}` and "
                    f"`{unique_tables[j]}` may be joinable on a field related to "
                    f"'{norm}' (columns: {cols_a} <-> {cols_b})."
                )
                chunks.append({
                    "id": f"rel::{unique_tables[i]}::{unique_tables[j]}::{norm}",
                    "text": text,
                    "metadata": {
                        "chunk_type": CHUNK_TYPE_RELATIONSHIP,
                        "table_a": unique_tables[i],
                        "table_b": unique_tables[j],
                        "normalized_field": norm,
                    },
                })

    return chunks


def chunk_all(tables: list[TableSchema]) -> list[dict]:
    """Produce all chunks (table-level + field-level + relationships)."""
    all_chunks: list[dict] = []
    for t in tables:
        all_chunks.append(build_table_chunk(t))
        all_chunks.extend(build_field_chunks(t))
    all_chunks.extend(build_relationship_chunks(tables))
    return all_chunks
