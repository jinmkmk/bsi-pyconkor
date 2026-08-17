from datetime import date

from pydantic import BaseModel, Field


class School(BaseModel):
    officeCode: str
    schoolCode: str
    name: str
    region: str
    schoolType: str
    address: str


class SchoolSummary(BaseModel):
    officeCode: str
    schoolCode: str
    name: str


class SchoolPage(BaseModel):
    items: list[School]
    totalCount: int = Field(ge=0)
    page: int = Field(ge=1)
    pageSize: int = Field(ge=1)


class Meal(BaseModel):
    date: date
    mealType: str
    dishes: list[str]
    calories: str | None = None
    nutrition: str | None = None


class MealPage(BaseModel):
    school: SchoolSummary
    from_: date = Field(serialization_alias="from")
    to: date
    items: list[Meal]


class ErrorDetail(BaseModel):
    code: str
    message: str
    requestId: str
    fields: dict[str, str] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
