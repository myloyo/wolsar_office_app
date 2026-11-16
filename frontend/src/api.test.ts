import { afterEach, describe, expect, it, vi } from "vitest";
import { api, ApiError } from "./api";
afterEach(() => vi.unstubAllGlobals());
describe("session API", () => {
  it("sends the CSRF cookie and same-origin credentials on mutations", async () => {
    vi.stubGlobal("document", { cookie: "other=x; wolsar_csrf=csrf%2Dtoken" });
    const fetch = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => ({ id: 1 }) });
    vi.stubGlobal("fetch", fetch);

    const result = await api("/tasks", 1, "POST", { title: "test" });

    expect(result).toEqual({ id: 1 });
    expect(fetch).toHaveBeenCalledWith(
      "/api/tasks",
      expect.objectContaining({
        credentials: "same-origin",
        method: "POST",
        headers: expect.objectContaining({ "X-CSRF-Token": "csrf-token" }),
      }),
    );
  });
  it("prompts a fresh login on expired session without replacing server errors", async () => {
    vi.stubGlobal("document", { cookie: "" });
    const dispatchEvent = vi.fn();
    vi.stubGlobal("window", { dispatchEvent });
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue({
          ok: false,
          status: 401,
          json: async () => ({ detail: "Session expired" }),
        }),
    );

    const request = api("/tasks", 1);

    await expect(request).rejects.toMatchObject({
      status: 401,
      message: "Session expired",
    });
    expect(dispatchEvent.mock.calls[0][0].type).toBe("auth-expired");
  });
  it("does not trigger the global expiry flow for rejected login codes", async () => {
    vi.stubGlobal("document", { cookie: "" });
    const dispatchEvent = vi.fn();
    vi.stubGlobal("window", { dispatchEvent });
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue({ ok: false, status: 401, json: async () => null }),
    );

    const request = api("/auth/verify-code", 1, "POST", {});

    await expect(request).rejects.toBeInstanceOf(ApiError);
    expect(dispatchEvent).not.toHaveBeenCalled();
  });
});
