import json
from pathlib import Path
from typing import Optional


class TableRules:
    """Load and query table-specific rules from a JSON config file.

    JSON format:
        {"rules": [{"table": "xxx", "condition": "xxx", "description": "xxx"}]}
    """

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self._rules: list[dict] = []
        self._by_table: dict[str, list[dict]] = {}
        self._load()

    def _load(self):
        if not self.file_path.exists():
            self._rules = []
            self._by_table = {}
            return
        with open(self.file_path, encoding="utf-8") as f:
            data = json.load(f)
        self._rules = data.get("rules", [])
        self._by_table = {}
        for rule in self._rules:
            table = rule["table"].lower()
            self._by_table.setdefault(table, []).append(rule)

    def get_rules_for_tables(self, tables: list[str]) -> list[dict]:
        """Return rules that match any of the given table names."""
        matched: list[dict] = []
        seen: set[str] = set()
        for t in tables:
            for rule in self._by_table.get(t.lower(), []):
                key = f"{rule['table']}:{rule['condition']}"
                if key not in seen:
                    seen.add(key)
                    matched.append(rule)
        return matched

    def get_all_rules(self) -> list[dict]:
        return list(self._rules)

    def reload(self):
        self._load()
