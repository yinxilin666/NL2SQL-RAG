from fastapi import APIRouter, Depends

from api.dependencies import get_table_rules
from config.table_rules import TableRules

router = APIRouter(prefix="/api/rules", tags=["rules"])


@router.get("")
async def list_rules(table_rules: TableRules = Depends(get_table_rules)):
    return {"rules": table_rules.get_all_rules()}
