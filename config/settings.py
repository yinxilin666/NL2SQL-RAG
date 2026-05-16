from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "deepseek-r1:8b"
    embed_model: str = "nomic-embed-text"
    chromadb_path: str = "data/chromadb"
    bm25_index_path: str = "data/bm25_index/bm25.pkl"
    excel_input_path: str = "data/input/schema.xlsx"
    top_k: int = 8
    llm_temperature: float = 0.1

    model_config = {"env_file": ".env"}
