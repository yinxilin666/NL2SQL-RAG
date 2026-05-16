# Excel columns
COL_TABLE = "table"
COL_SUBS_CODE = "subs_code"
COL_TABLE_COMMENT = "table_comment"
COL_COLUMN_NAME = "column_name"
COL_COLUMN_COMMENT = "column_comment"
COL_COLUMN_TYPE = "column_type"

REQUIRED_COLUMNS = [
    COL_TABLE, COL_SUBS_CODE, COL_TABLE_COMMENT,
    COL_COLUMN_NAME, COL_COLUMN_COMMENT, COL_COLUMN_TYPE,
]

# Chunk types
CHUNK_TYPE_TABLE = "table"
CHUNK_TYPE_FIELD = "field"
CHUNK_TYPE_RELATIONSHIP = "relationship"

# Retrieval defaults
DEFAULT_TOP_K = 8
RRF_K = 60
VECTOR_WEIGHT = 0.6
BM25_WEIGHT = 0.4

# Collection name
COLLECTION_NAME = "table_schema"
