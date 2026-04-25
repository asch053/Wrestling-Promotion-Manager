from pydantic import BaseModel

class Contract(BaseModel):
    appearance_fee: int
    weekly_salary: int
    merch_cut_percentage: float
