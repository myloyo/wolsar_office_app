import { describe, expect, it } from "vitest";
import { planningWeek } from "./date";
describe("Неделя среда–вторник", () => {
  it.each([
    ["2026-11-04", "2026-11-04"],
    ["2026-11-10", "2026-11-04"],
    ["2026-01-01", "2025-12-31"],
  ])("%s → %s", (input, expected) => {
    const week = planningWeek(input);

    expect(week).toBe(expected);
  });
});
