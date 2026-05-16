from typing import List, Optional

import pandas as pd
from pydantic import BaseModel, Field

from config.constants import (
    COL_COLUMN_COMMENT,
    COL_COLUMN_NAME,
    COL_COLUMN_TYPE,
    COL_SUBS_CODE,
    COL_TABLE,
    COL_TABLE_COMMENT,
    REQUIRED_COLUMNS,
)


class FieldSchema(BaseModel):
    column_name: str
    column_comment: str = ""
    column_type: str


class TableSchema(BaseModel):
    table: str
    subs_code: str
    table_comment: str = ""
    fields: List[FieldSchema] = Field(default_factory=list)


class LoadResult(BaseModel):
    tables: List[TableSchema]
    total_fields: int


def load_excel(file_path: str) -> LoadResult:
    """Parse an Excel file and return structured table metadata."""
    df = pd.read_excel(file_path)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if df[COL_TABLE].isnull().any():
        raise ValueError("Column 'table' contains null values")
    if df[COL_COLUMN_NAME].isnull().any():
        raise ValueError("Column 'column_name' contains null values")

    fill_map = {
        COL_SUBS_CODE: "",
        COL_TABLE_COMMENT: "",
        COL_COLUMN_COMMENT: "",
        COL_COLUMN_TYPE: "STRING",
    }
    for col, default in fill_map.items():
        if col in df.columns:
            df[col] = df[col].fillna(default)

    tables: List[TableSchema] = []
    grouped = df.groupby(COL_TABLE, sort=False)

    for table_name, group in grouped:
        fields = []
        for _, row in group.iterrows():
            fields.append(FieldSchema(
                column_name=str(row[COL_COLUMN_NAME]).strip(),
                column_comment=str(row.get(COL_COLUMN_COMMENT, "")).strip(),
                column_type=str(row.get(COL_COLUMN_TYPE, "STRING")).strip(),
            ))

        first_row = group.iloc[0]
        tables.append(TableSchema(
            table=str(table_name).strip(),
            subs_code=str(first_row.get(COL_SUBS_CODE, "")).strip(),
            table_comment=str(first_row.get(COL_TABLE_COMMENT, "")).strip(),
            fields=fields,
        ))

    total_fields = sum(len(t.fields) for t in tables)
    return LoadResult(tables=tables, total_fields=total_fields)
