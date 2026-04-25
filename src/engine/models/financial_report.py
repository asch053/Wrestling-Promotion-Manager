from pydantic import BaseModel
from typing import Dict

class FinancialReport(BaseModel):
    total_revenue: int
    total_expenses: int
    net_profit: int
    revenue_breakdown: Dict[str, int]
    expense_breakdown: Dict[str, int]
