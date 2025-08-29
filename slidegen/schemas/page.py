from pydantic import BaseModel


class Pager(BaseModel):
    per_page: int
    page: int
    pages: int
    total: int
