import type { Meal, MealPage, School, SchoolPage } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  constructor(message: string) {
    super(message);
  }
}

async function request(path: string): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { Accept: "application/json" },
    });
  } catch {
    throw new ApiError(
      "서버에 연결할 수 없습니다. 네트워크를 확인하고 다시 시도해 주세요.",
    );
  }

  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    if (isApiError(body)) {
      throw new ApiError(body.error.message);
    }
    throw new ApiError(
      "요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.",
    );
  }
  return body;
}

function isApiError(
  value: unknown,
): value is { error: { code: string; message: string } } {
  if (typeof value !== "object" || value === null || !("error" in value)) {
    return false;
  }
  const error = value.error;
  return (
    typeof error === "object" &&
    error !== null &&
    "message" in error &&
    typeof error.message === "string" &&
    "code" in error &&
    typeof error.code === "string"
  );
}

export async function searchSchools(query: string): Promise<SchoolPage> {
  const body = await request(
    `/api/schools?query=${encodeURIComponent(query)}&pageSize=20`,
  );
  if (!isSchoolPage(body)) {
    throw new ApiError("학교 검색 응답 형식이 올바르지 않습니다.");
  }
  return body;
}

export async function getMeals(
  officeCode: string,
  schoolCode: string,
  dateFrom: string,
  dateTo: string,
): Promise<MealPage> {
  const params = new URLSearchParams({
    officeCode,
    schoolCode,
    from: dateFrom,
    to: dateTo,
  });
  const body = await request(`/api/meals?${params.toString()}`);
  if (!isMealPage(body)) {
    throw new ApiError("급식 응답 형식이 올바르지 않습니다.");
  }
  return body;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isSchool(value: unknown): value is School {
  return (
    isRecord(value) &&
    ["officeCode", "schoolCode", "name", "region", "schoolType", "address"].every(
      (key) => typeof value[key] === "string",
    )
  );
}

function isSchoolPage(value: unknown): value is SchoolPage {
  return (
    isRecord(value) &&
    Array.isArray(value.items) &&
    value.items.every(isSchool) &&
    typeof value.totalCount === "number" &&
    typeof value.page === "number" &&
    typeof value.pageSize === "number"
  );
}

function isMeal(value: unknown): value is Meal {
  return (
    isRecord(value) &&
    typeof value.date === "string" &&
    value.mealType === "중식" &&
    Array.isArray(value.dishes) &&
    value.dishes.every((dish) => typeof dish === "string") &&
    (value.calories === undefined ||
      value.calories === null ||
      typeof value.calories === "string") &&
    (value.nutrition === undefined ||
      value.nutrition === null ||
      typeof value.nutrition === "string")
  );
}

function isMealPage(value: unknown): value is MealPage {
  return (
    isRecord(value) &&
    isRecord(value.school) &&
    typeof value.school.officeCode === "string" &&
    typeof value.school.schoolCode === "string" &&
    typeof value.school.name === "string" &&
    typeof value.from === "string" &&
    typeof value.to === "string" &&
    Array.isArray(value.items) &&
    value.items.every(isMeal)
  );
}
