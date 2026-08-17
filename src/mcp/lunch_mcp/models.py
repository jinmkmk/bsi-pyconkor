"""Structured MCP tool result models."""

from datetime import date

from pydantic import BaseModel, Field


class School(BaseModel):
    name: str
    office_name: str
    office_code: str
    school_code: str
    region: str
    school_type: str
    address: str


class SchoolSearchResult(BaseModel):
    schools: list[School]
    total_count: int = Field(ge=1)


class Meal(BaseModel):
    date: date
    dishes: list[str]
    calories: str | None = None
    nutrition: str | None = None


class LunchResult(BaseModel):
    school_name: str
    office_code: str
    school_code: str
    date_from: date
    date_to: date
    meals: list[Meal]
