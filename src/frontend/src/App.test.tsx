import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const schoolResponse = {
  items: [{
    officeCode: "B10",
    schoolCode: "7010569",
    name: "예시고등학교",
    region: "서울특별시",
    schoolType: "고등학교",
    address: "서울특별시 예시로 1",
  }],
  totalCount: 1,
  page: 1,
  pageSize: 20,
};

describe("App", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn()));
  afterEach(() => vi.unstubAllGlobals());

  it("searches and selects a school with the keyboard", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify(schoolResponse), { status: 200 }),
    );
    const user = userEvent.setup();
    render(<App />);

    const input = screen.getByLabelText("학교 이름");
    await user.type(input, "예시{Enter}");
    expect(await screen.findByText("예시고등학교")).toBeInTheDocument();
    await user.keyboard("{ArrowDown}{Enter}");

    expect(screen.getByText("서울특별시 · 고등학교")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "급식 조회" })).toBeEnabled();
  });

  it("shows empty search results separately from errors", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify({ ...schoolResponse, items: [], totalCount: 0 }), {
        status: 200,
      }),
    );
    const user = userEvent.setup();
    render(<App />);

    await user.type(screen.getByLabelText("학교 이름"), "없음{Enter}");
    expect(
      await screen.findByText("검색 결과가 없습니다. 학교명이나 지역을 확인해 주세요."),
    ).toBeInTheDocument();
  });

  it("validates a date range longer than 31 days", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      new Response(JSON.stringify(schoolResponse), { status: 200 }),
    );
    const user = userEvent.setup();
    render(<App />);

    await user.type(screen.getByLabelText("학교 이름"), "예시{Enter}");
    await user.click(await screen.findByRole("button", { name: /예시고등학교/ }));
    await user.clear(screen.getByLabelText("시작일"));
    await user.type(screen.getByLabelText("시작일"), "2026-08-01");
    await user.clear(screen.getByLabelText("종료일"));
    await user.type(screen.getByLabelText("종료일"), "2026-09-01");

    expect(screen.getByRole("alert")).toHaveTextContent("최대 31일");
    expect(screen.getByRole("button", { name: "급식 조회" })).toBeDisabled();
  });

  it("renders sorted meals and optional nutrition", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(new Response(JSON.stringify(schoolResponse), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        school: schoolResponse.items[0],
        from: "2026-08-17",
        to: "2026-08-18",
        items: [
          { date: "2026-08-18", mealType: "중식", dishes: ["비빔밥"] },
          { date: "2026-08-17", mealType: "중식", dishes: ["현미밥"], calories: "650 Kcal" },
        ],
      }), { status: 200 }));
    const user = userEvent.setup();
    render(<App />);

    await user.type(screen.getByLabelText("학교 이름"), "예시{Enter}");
    await user.click(await screen.findByRole("button", { name: /예시고등학교/ }));
    await user.click(screen.getByRole("button", { name: "급식 조회" }));

    await waitFor(() => expect(screen.getByText("현미밥")).toBeInTheDocument());
    const cards = screen.getAllByRole("article");
    expect(cards[0]).toHaveTextContent("현미밥");
    expect(screen.getByText("영양 정보")).toBeInTheDocument();
  });
});
