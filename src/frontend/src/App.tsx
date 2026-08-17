import {
  type FormEvent,
  type KeyboardEvent,
  useEffect,
  useId,
  useState,
} from "react";

import { ApiError, getMeals, searchSchools } from "./api/client";
import type { MealPage, School } from "./api/types";

type RequestState = "idle" | "loading" | "error";

function toIsoDate(date: Date): string {
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 10);
}

function initialDates(): { dateFrom: string; dateTo: string } {
  const today = new Date();
  const end = new Date(today);
  end.setDate(end.getDate() + 6);
  return { dateFrom: toIsoDate(today), dateTo: toIsoDate(end) };
}

function dateError(dateFrom: string, dateTo: string): string {
  if (!dateFrom || !dateTo) return "시작일과 종료일을 모두 선택해 주세요.";
  const start = new Date(`${dateFrom}T00:00:00`);
  const end = new Date(`${dateTo}T00:00:00`);
  if (start > end) return "시작일은 종료일보다 늦을 수 없습니다.";
  const days = Math.round((end.getTime() - start.getTime()) / 86_400_000) + 1;
  if (days > 31) return "급식은 한 번에 최대 31일까지 조회할 수 있습니다.";
  return "";
}

export default function App() {
  const defaults = initialDates();
  const [query, setQuery] = useState("");
  const [schools, setSchools] = useState<School[]>([]);
  const [selectedSchool, setSelectedSchool] = useState<School | null>(null);
  const [dateFrom, setDateFrom] = useState(defaults.dateFrom);
  const [dateTo, setDateTo] = useState(defaults.dateTo);
  const [meals, setMeals] = useState<MealPage | null>(null);
  const [searchState, setSearchState] = useState<RequestState>("idle");
  const [mealState, setMealState] = useState<RequestState>("idle");
  const [message, setMessage] = useState("");
  const [activeIndex, setActiveIndex] = useState(-1);
  const resultsId = useId();
  const dateErrorId = useId();
  const validationMessage = dateError(dateFrom, dateTo);

  useEffect(() => {
    if (activeIndex >= schools.length) setActiveIndex(schools.length - 1);
  }, [activeIndex, schools.length]);

  async function runSearch() {
    const normalized = query.trim();
    if (!normalized) {
      setMessage("학교 이름을 한 글자 이상 입력해 주세요.");
      return;
    }
    setSearchState("loading");
    setMessage("");
    setSchools([]);
    setActiveIndex(-1);
    try {
      const result = await searchSchools(normalized);
      setSchools(result.items);
      setSearchState("idle");
      if (result.items.length === 0) {
        setMessage("검색 결과가 없습니다. 학교명이나 지역을 확인해 주세요.");
      }
    } catch (error) {
      setSearchState("error");
      setMessage(
        error instanceof ApiError
          ? error.message
          : "학교를 검색하지 못했습니다. 다시 시도해 주세요.",
      );
    }
  }

  function handleSearch(event: FormEvent) {
    event.preventDefault();
    void runSearch();
  }

  function selectSchool(school: School) {
    setSelectedSchool(school);
    setSchools([]);
    setActiveIndex(-1);
    setMeals(null);
    setMealState("idle");
    setMessage("");
  }

  function handleSearchKeys(event: KeyboardEvent<HTMLInputElement>) {
    if (schools.length === 0) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((index) => (index + 1) % schools.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((index) => (index <= 0 ? schools.length - 1 : index - 1));
    } else if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      selectSchool(schools[activeIndex]);
    } else if (event.key === "Escape") {
      setSchools([]);
      setActiveIndex(-1);
    }
  }

  async function runMeals() {
    if (!selectedSchool || validationMessage) return;
    setMealState("loading");
    setMessage("");
    setMeals(null);
    try {
      const result = await getMeals(
        selectedSchool.officeCode,
        selectedSchool.schoolCode,
        dateFrom,
        dateTo,
      );
      result.items.sort((a, b) => a.date.localeCompare(b.date));
      setMeals(result);
      setMealState("idle");
      if (result.items.length === 0) {
        setMessage("선택한 기간에 등록된 중식이 없습니다.");
      }
    } catch (error) {
      setMealState("error");
      setMessage(
        error instanceof ApiError
          ? error.message
          : "급식을 불러오지 못했습니다. 다시 시도해 주세요.",
      );
    }
  }

  function handleMeals(event: FormEvent) {
    event.preventDefault();
    void runMeals();
  }

  const step = meals ? 3 : selectedSchool ? 2 : 1;

  return (
    <>
      <header className="site-header">
        <div className="brand">급식 배틀</div>
        <span>우리 학교 오늘의 중식</span>
      </header>
      <main>
        <section className="hero" aria-labelledby="page-title">
          <p className="eyebrow">SCHOOL LUNCH FINDER</p>
          <h1 id="page-title">학교 급식, 세 단계면 충분해요.</h1>
          <p>학교를 찾고 날짜를 선택하면 중식 메뉴를 한눈에 보여드립니다.</p>
        </section>

        <ol className="steps" aria-label="급식 조회 진행 단계">
          {["학교 찾기", "날짜 선택", "급식 확인"].map((label, index) => {
            const number = index + 1;
            const state = number < step ? "complete" : number === step ? "active" : "";
            return (
              <li key={label} className={state} aria-current={number === step ? "step" : undefined}>
                <span>{number < step ? "✓" : number}</span>
                {label}
              </li>
            );
          })}
        </ol>

        <section className="panel" aria-labelledby="school-title">
          <div className="section-heading">
            <span className="section-number">01</span>
            <div>
              <h2 id="school-title">학교 찾기</h2>
              <p>학교 이름의 일부를 입력해도 검색할 수 있어요.</p>
            </div>
          </div>
          <form onSubmit={handleSearch} className="search-form">
            <label htmlFor="school-query">학교 이름</label>
            <div className="input-row">
              <input
                id="school-query"
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  setMessage("");
                }}
                onKeyDown={handleSearchKeys}
                placeholder="예: 한빛고등학교"
                autoComplete="off"
                role="combobox"
                aria-autocomplete="list"
                aria-controls={schools.length ? resultsId : undefined}
                aria-expanded={schools.length > 0}
                aria-activedescendant={
                  activeIndex >= 0 ? `${resultsId}-${activeIndex}` : undefined
                }
              />
              <button type="submit" disabled={searchState === "loading"}>
                {searchState === "loading" ? "검색 중…" : "학교 검색"}
              </button>
            </div>
            {schools.length > 0 && (
              <ul id={resultsId} className="school-results" role="listbox">
                {schools.map((school, index) => (
                  <li
                    id={`${resultsId}-${index}`}
                    key={`${school.officeCode}-${school.schoolCode}`}
                    role="option"
                    aria-selected={index === activeIndex}
                  >
                    <button type="button" onClick={() => selectSchool(school)}>
                      <strong>{school.name}</strong>
                      <span>{school.region} · {school.schoolType}</span>
                      <small>{school.address}</small>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </form>
          {selectedSchool && (
            <div className="selected-school">
              <div>
                <span className="status-dot" aria-hidden="true" />
                <strong>{selectedSchool.name}</strong>
                <small>{selectedSchool.region} · {selectedSchool.schoolType}</small>
              </div>
              <button type="button" className="text-button" onClick={() => {
                setSelectedSchool(null);
                setMeals(null);
              }}>
                학교 변경
              </button>
            </div>
          )}
        </section>

        <section className={`panel ${selectedSchool ? "" : "disabled-panel"}`} aria-labelledby="date-title">
          <div className="section-heading">
            <span className="section-number">02</span>
            <div>
              <h2 id="date-title">날짜 선택</h2>
              <p>{selectedSchool ? "최대 31일까지 조회할 수 있어요." : "학교를 먼저 선택해 주세요."}</p>
            </div>
          </div>
          <form onSubmit={handleMeals}>
            <fieldset disabled={!selectedSchool || mealState === "loading"}>
              <div className="date-grid">
                <label>
                  시작일
                  <input
                    type="date"
                    value={dateFrom}
                    onChange={(event) => {
                      setDateFrom(event.target.value);
                      setMeals(null);
                    }}
                    aria-describedby={validationMessage ? dateErrorId : undefined}
                  />
                </label>
                <span aria-hidden="true">→</span>
                <label>
                  종료일
                  <input
                    type="date"
                    value={dateTo}
                    onChange={(event) => {
                      setDateTo(event.target.value);
                      setMeals(null);
                    }}
                    aria-describedby={validationMessage ? dateErrorId : undefined}
                  />
                </label>
                <button type="submit" disabled={Boolean(validationMessage)}>
                  {mealState === "loading" ? "조회 중…" : "급식 조회"}
                </button>
              </div>
            </fieldset>
            {selectedSchool && validationMessage && (
              <p id={dateErrorId} className="field-error" role="alert">{validationMessage}</p>
            )}
          </form>
        </section>

        <div className="live-region" aria-live="polite" aria-atomic="true">
          {message && (
            <div className={`notice ${searchState === "error" || mealState === "error" ? "error" : ""}`}>
              <p>{message}</p>
              {(searchState === "error" || mealState === "error") && (
                <button
                  type="button"
                  className="text-button"
                  onClick={() =>
                    mealState === "error"
                      ? void runMeals()
                      : void runSearch()
                  }
                >
                  다시 시도
                </button>
              )}
            </div>
          )}
        </div>

        {meals && meals.items.length > 0 && (
          <section className="meal-section" aria-labelledby="meal-title">
            <div className="section-heading">
              <span className="section-number">03</span>
              <div>
                <h2 id="meal-title">{selectedSchool?.name} 중식</h2>
                <p>{dateFrom} ~ {dateTo} · 날짜순</p>
              </div>
            </div>
            <div className="meal-list">
              {meals.items.map((meal) => (
                <article className="meal-card" key={meal.date}>
                  <time dateTime={meal.date}>
                    <strong>{new Intl.DateTimeFormat("ko-KR", {
                      month: "long",
                      day: "numeric",
                      weekday: "short",
                      timeZone: "UTC",
                    }).format(new Date(`${meal.date}T00:00:00Z`))}</strong>
                    <span>중식</span>
                  </time>
                  <ul>
                    {meal.dishes.map((dish) => <li key={dish}>{dish}</li>)}
                  </ul>
                  {(meal.calories || meal.nutrition) && (
                    <details>
                      <summary>영양 정보</summary>
                      {meal.calories && <p>{meal.calories}</p>}
                      {meal.nutrition && <p>{meal.nutrition}</p>}
                    </details>
                  )}
                </article>
              ))}
            </div>
          </section>
        )}
      </main>
      <footer>급식 정보는 NEIS 공개 데이터를 기반으로 제공됩니다.</footer>
    </>
  );
}
