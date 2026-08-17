import { expect, test } from "@playwright/test";

test("학교 검색부터 날짜별 급식 확인까지 완료한다", async ({ page }) => {
  await page.route("**/api/schools?*", async (route) => {
    await route.fulfill({
      json: {
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
      },
    });
  });
  await page.route("**/api/meals?*", async (route) => {
    await route.fulfill({
      json: {
        school: {
          officeCode: "B10",
          schoolCode: "7010569",
          name: "예시고등학교",
        },
        from: "2026-08-17",
        to: "2026-08-18",
        items: [{
          date: "2026-08-17",
          mealType: "중식",
          dishes: ["현미밥", "미역국", "배추김치"],
          calories: "650 Kcal",
        }],
      },
    });
  });

  await page.goto("/");
  await page.getByLabel("학교 이름").fill("예시");
  await page.getByRole("button", { name: "학교 검색" }).click();
  await page.getByRole("option").getByRole("button").click();
  await page.getByLabel("시작일").fill("2026-08-17");
  await page.getByLabel("종료일").fill("2026-08-18");
  await page.getByRole("button", { name: "급식 조회" }).click();

  await expect(page.getByRole("heading", { name: "예시고등학교 중식" })).toBeVisible();
  await expect(page.getByText("현미밥")).toBeVisible();
});

test("빈 검색 결과와 잘못된 날짜 범위를 구분한다", async ({ page }) => {
  await page.route("**/api/schools?*", async (route) => {
    const url = new URL(route.request().url());
    await route.fulfill({
      json: url.searchParams.get("query") === "없음"
        ? { items: [], totalCount: 0, page: 1, pageSize: 20 }
        : {
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
          },
    });
  });

  await page.goto("/");
  await page.getByLabel("학교 이름").fill("없음");
  await page.getByRole("button", { name: "학교 검색" }).click();
  await expect(page.getByText(/검색 결과가 없습니다/)).toBeVisible();

  await page.getByLabel("학교 이름").fill("예시");
  await page.getByRole("button", { name: "학교 검색" }).click();
  await page.getByRole("option").getByRole("button").click();
  await page.getByLabel("시작일").fill("2026-08-01");
  await page.getByLabel("종료일").fill("2026-09-01");
  await expect(page.getByRole("alert")).toContainText("최대 31일");
  await expect(page.getByRole("button", { name: "급식 조회" })).toBeDisabled();
});
