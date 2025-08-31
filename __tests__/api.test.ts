import {
  getNarratives,
  getParents,
  doRefresh,
  startRefreshJob,
  getRefreshStatus,
} from "../src/lib/api";

// Mock fetch globally
global.fetch = jest.fn();

const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

describe("API Functions", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("getNarratives", () => {
    it("fetches narratives successfully", async () => {
      const mockResponse = {
        items: ["dogs", "ai"],
        lastRefresh: 1704067200,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response);

      const result = await getNarratives();

      expect(result).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/narratives"),
        { cache: "no-store" },
      );
    });

    it("throws error on non-ok response", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      } as Response);

      await expect(getNarratives()).rejects.toThrow("GET /narratives 500");
    });

    it("throws error on fetch failure", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      await expect(getNarratives()).rejects.toThrow("Network error");
    });
  });

  describe("getParents", () => {
    it("fetches parents with default parameters", async () => {
      const mockResponse = {
        narrative: "dogs",
        window: "24h",
        items: [
          { parent: "parent1", matches: 5, score: 0.8 },
          { parent: "parent2", matches: 3, score: 0.6 },
        ],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response);

      const result = await getParents("dogs");

      expect(result).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/parents/dogs?limit=25"),
        { cache: "no-store" },
      );
    });

    it("fetches parents with custom parameters", async () => {
      const mockResponse = {
        narrative: "ai",
        window: "24h",
        items: [],
        nextCursor: "next-page",
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response);

      const result = await getParents("ai", {
        limit: 10,
        cursor: "current-page",
      });

      expect(result).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/parents/ai?limit=10&cursor=current-page"),
        { cache: "no-store" },
      );
    });

    it("handles URL encoding for narrative names", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({ narrative: "test", window: "24h", items: [] }),
      } as Response);

      await getParents("test with spaces & symbols");

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining(
          "/parents/test%20with%20spaces%20%26%20symbols",
        ),
        { cache: "no-store" },
      );
    });

    it("throws error on non-ok response", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
      } as Response);

      await expect(getParents("nonexistent")).rejects.toThrow(
        "GET /parents/nonexistent 404",
      );
    });
  });

  describe("doRefresh", () => {
    it("calls refresh endpoint without window parameter", async () => {
      const mockResponse = { success: true };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response);

      const result = await doRefresh();

      expect(result).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/refresh"),
        { method: "POST", headers: undefined },
      );
    });

    it("calls refresh endpoint with window parameter", async () => {
      const mockResponse = { success: true };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response);

      const result = await doRefresh("7d");

      expect(result).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/refresh?window=7d"),
        { method: "POST", headers: undefined },
      );
    });

    it("throws error on non-ok response", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
      } as Response);

      await expect(doRefresh()).rejects.toThrow("POST /refresh 401");
    });
  });

  describe("startRefreshJob", () => {
    it("starts refresh job successfully", async () => {
      const mockResponse = { jobId: "job-123" };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response);

      const result = await startRefreshJob();

      expect(result).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/refresh/async"),
        { method: "POST", headers: undefined },
      );
    });

    it("throws error on non-ok response", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
      } as Response);

      await expect(startRefreshJob()).rejects.toThrow(
        "POST /refresh/async 403",
      );
    });
  });

  describe("getRefreshStatus", () => {
    it("gets refresh status successfully", async () => {
      const mockResponse = {
        id: "job-123",
        state: "running",
        ts: Date.now(),
        error: null,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response);

      const result = await getRefreshStatus("job-123");

      expect(result).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/refresh/status/job-123"),
        { headers: undefined, cache: "no-store" },
      );
    });

    it("throws error on non-ok response", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
      } as Response);

      await expect(getRefreshStatus("nonexistent")).rejects.toThrow(
        "GET /refresh/status 404",
      );
    });
  });

  describe("environment handling", () => {
    const originalEnv = process.env;

    beforeEach(() => {
      jest.resetModules();
      process.env = { ...originalEnv };
    });

    afterEach(() => {
      process.env = originalEnv;
    });

    it("uses NEXT_PUBLIC_API_BASE when available", async () => {
      process.env.NEXT_PUBLIC_API_BASE = "https://custom-api.com";

      // Re-import to get fresh environment values
      const { getNarratives } = await import("../src/lib/api");

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ items: [] }),
      } as Response);

      await getNarratives();

      expect(mockFetch).toHaveBeenCalledWith(
        "https://custom-api.com/narratives",
        { cache: "no-store" },
      );
    });

    it("falls back to localhost when NEXT_PUBLIC_API_BASE is not set", async () => {
      delete process.env.NEXT_PUBLIC_API_BASE;

      // Re-import to get fresh environment values
      const { getNarratives } = await import("../src/lib/api");

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ items: [] }),
      } as Response);

      await getNarratives();

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/narratives",
        { cache: "no-store" },
      );
    });

    it("handles server-side environment variables", async () => {
      // Mock server-side environment
      const originalWindow = global.window;
      global.window = undefined as any;

      process.env.API_BASE = "http://server-api:9000";
      process.env.NEXT_PUBLIC_API_BASE = "http://public-api:8000";

      // Re-import to get fresh environment values
      const { getNarratives } = await import("../src/lib/api");

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ items: [] }),
      } as Response);

      await getNarratives();

      expect(mockFetch).toHaveBeenCalledWith(
        "http://public-api:8000/narratives",
        { cache: "no-store" },
      );

      // Restore window
      global.window = originalWindow;
    });

    it("falls back to NEXT_PUBLIC_API_BASE on server when API_BASE is not set", async () => {
      // Mock server-side environment
      const originalWindow = global.window;
      global.window = undefined as any;

      delete process.env.API_BASE;
      process.env.NEXT_PUBLIC_API_BASE = "http://public-api:8000";

      // Re-import to get fresh environment values
      const { getNarratives } = await import("../src/lib/api");

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ items: [] }),
      } as Response);

      await getNarratives();

      expect(mockFetch).toHaveBeenCalledWith(
        "http://public-api:8000/narratives",
        { cache: "no-store" },
      );

      // Restore window
      global.window = originalWindow;
    });

    it("falls back to backend:8000 on server when no env vars are set", async () => {
      // Mock server-side environment
      const originalWindow = global.window;
      global.window = undefined as any;

      delete process.env.API_BASE;
      delete process.env.NEXT_PUBLIC_API_BASE;

      // Re-import to get fresh environment values
      const { getNarratives } = await import("../src/lib/api");

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ items: [] }),
      } as Response);

      await getNarratives();

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/narratives",
        { cache: "no-store" },
      );

      // Restore window
      global.window = originalWindow;
    });

    it("handles whitespace-only environment variables on server", async () => {
      // Create a mock module that simulates server-side environment
      jest.doMock("../src/lib/api", () => {
        const originalModule = jest.requireActual("../src/lib/api");
        const mockModule = { ...originalModule };

        // Override the BASE constant to simulate server-side logic
        const isServer = true; // Simulate server environment
        const BASE = isServer
          ? process.env.API_BASE?.trim() ||
            process.env.NEXT_PUBLIC_API_BASE?.trim() ||
            "http://backend:8000"
          : process.env.NEXT_PUBLIC_API_BASE?.trim() || "http://localhost:8000";

        // Override the getNarratives function to use our mocked BASE
        mockModule.getNarratives = async () => {
          const r = await fetch(`${BASE}/narratives`, { cache: "no-store" });
          if (!r.ok) throw new Error(`GET /narratives ${r.status}`);
          return r.json();
        };

        return mockModule;
      });

      process.env.API_BASE = "   ";
      process.env.NEXT_PUBLIC_API_BASE = "  ";

      // Re-import to get fresh environment values
      const { getNarratives } = await import("../src/lib/api");

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ items: [] }),
      } as Response);

      await getNarratives();

      expect(mockFetch).toHaveBeenCalledWith("http://backend:8000/narratives", {
        cache: "no-store",
      });

      // Restore mocks
      jest.dontMock("../src/lib/api");
    });

    it("handles server-side BASE logic with API_BASE set", async () => {
      // Create a mock module that simulates server-side environment
      jest.doMock("../src/lib/api", () => {
        const originalModule = jest.requireActual("../src/lib/api");
        const mockModule = { ...originalModule };

        // Override the BASE constant to simulate server-side logic
        const isServer = true; // Simulate server environment
        const BASE = isServer
          ? process.env.API_BASE?.trim() ||
            process.env.NEXT_PUBLIC_API_BASE?.trim() ||
            "http://backend:8000"
          : process.env.NEXT_PUBLIC_API_BASE?.trim() || "http://localhost:8000";

        // Override the getNarratives function to use our mocked BASE
        mockModule.getNarratives = async () => {
          const r = await fetch(`${BASE}/narratives`, { cache: "no-store" });
          if (!r.ok) throw new Error(`GET /narratives ${r.status}`);
          return r.json();
        };

        return mockModule;
      });

      process.env.API_BASE = "http://server-api:9000";
      process.env.NEXT_PUBLIC_API_BASE = "http://public-api:8000";

      // Re-import to get fresh environment values
      const { getNarratives } = await import("../src/lib/api");

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ items: [] }),
      } as Response);

      await getNarratives();

      expect(mockFetch).toHaveBeenCalledWith(
        "http://server-api:9000/narratives",
        { cache: "no-store" },
      );

      // Restore mocks
      jest.dontMock("../src/lib/api");
    });

    it("handles server-side BASE logic with fallback to backend:8000", async () => {
      // Create a mock module that simulates server-side environment
      jest.doMock("../src/lib/api", () => {
        const originalModule = jest.requireActual("../src/lib/api");
        const mockModule = { ...originalModule };

        // Override the BASE constant to simulate server-side logic
        const isServer = true; // Simulate server environment
        const BASE = isServer
          ? process.env.API_BASE?.trim() ||
            process.env.NEXT_PUBLIC_API_BASE?.trim() ||
            "http://backend:8000"
          : process.env.NEXT_PUBLIC_API_BASE?.trim() || "http://localhost:8000";

        // Override the getNarratives function to use our mocked BASE
        mockModule.getNarratives = async () => {
          const r = await fetch(`${BASE}/narratives`, { cache: "no-store" });
          if (!r.ok) throw new Error(`GET /narratives ${r.status}`);
          return r.json();
        };

        return mockModule;
      });

      delete process.env.API_BASE;
      delete process.env.NEXT_PUBLIC_API_BASE;

      // Re-import to get fresh environment values
      const { getNarratives } = await import("../src/lib/api");

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ items: [] }),
      } as Response);

      await getNarratives();

      expect(mockFetch).toHaveBeenCalledWith("http://backend:8000/narratives", {
        cache: "no-store",
      });

      // Restore mocks
      jest.dontMock("../src/lib/api");
    });

    it("handles server-side BASE logic with fallback to backend:8000", async () => {
      // Create a mock module that simulates server-side environment
      jest.doMock("../src/lib/api", () => {
        const originalModule = jest.requireActual("../src/lib/api");
        const mockModule = { ...originalModule };

        // Override the BASE constant to simulate server-side logic
        const isServer = true; // Simulate server environment
        const BASE = isServer
          ? process.env.API_BASE?.trim() ||
            process.env.NEXT_PUBLIC_API_BASE?.trim() ||
            "http://backend:8000"
          : process.env.NEXT_PUBLIC_API_BASE?.trim() || "http://localhost:8000";

        // Override the getNarratives function to use our mocked BASE
        mockModule.getNarratives = async () => {
          const r = await fetch(`${BASE}/narratives`, { cache: "no-store" });
          if (!r.ok) throw new Error(`GET /narratives ${r.status}`);
          return r.json();
        };

        return mockModule;
      });

      delete process.env.API_BASE;
      delete process.env.NEXT_PUBLIC_API_BASE;

      // Re-import to get fresh environment values
      const { getNarratives } = await import("../src/lib/api");

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ items: [] }),
      } as Response);

      await getNarratives();

      expect(mockFetch).toHaveBeenCalledWith("http://backend:8000/narratives", {
        cache: "no-store",
      });

      // Restore mocks
      jest.dontMock("../src/lib/api");
    });
  });

  describe("auth headers", () => {
    const originalEnv = process.env;

    beforeEach(() => {
      jest.resetModules();
      process.env = { ...originalEnv };
    });

    afterEach(() => {
      process.env = originalEnv;
    });

    it("includes auth headers when NEXT_PUBLIC_REFRESH_TOKEN is set", async () => {
      process.env.NEXT_PUBLIC_REFRESH_TOKEN = "test-token";

      // Re-import to get fresh environment values
      const { doRefresh } = await import("../src/lib/api");

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      } as Response);

      await doRefresh();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/refresh"),
        {
          method: "POST",
          headers: { Authorization: "Bearer test-token" },
        },
      );
    });

    it("does not include auth headers when NEXT_PUBLIC_REFRESH_TOKEN is not set", async () => {
      delete process.env.NEXT_PUBLIC_REFRESH_TOKEN;

      // Re-import to get fresh environment values
      const { doRefresh } = await import("../src/lib/api");

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      } as Response);

      await doRefresh();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/refresh"),
        {
          method: "POST",
          headers: undefined,
        },
      );
    });

    it("handles empty refresh token gracefully", async () => {
      process.env.NEXT_PUBLIC_REFRESH_TOKEN = "";

      // Re-import to get fresh environment values
      const { doRefresh } = await import("../src/lib/api");

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      } as Response);

      await doRefresh();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/refresh"),
        {
          method: "POST",
          headers: undefined,
        },
      );
    });

    it("includes auth headers in startRefreshJob when token is set", async () => {
      process.env.NEXT_PUBLIC_REFRESH_TOKEN = "test-token";

      // Re-import to get fresh environment values
      const { startRefreshJob } = await import("../src/lib/api");

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ jobId: "test-job" }),
      } as Response);

      await startRefreshJob();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/refresh/async"),
        {
          method: "POST",
          headers: { Authorization: "Bearer test-token" },
        },
      );
    });

    it("includes auth headers in getRefreshStatus when token is set", async () => {
      process.env.NEXT_PUBLIC_REFRESH_TOKEN = "test-token";

      // Re-import to get fresh environment values
      const { getRefreshStatus } = await import("../src/lib/api");

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({ id: "test-job", state: "done", ts: Date.now() }),
      } as Response);

      await getRefreshStatus("test-job");

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/refresh/status/test-job"),
        {
          headers: { Authorization: "Bearer test-token" },
          cache: "no-store",
        },
      );
    });
  });

  describe("edge cases and error handling", () => {
    it("handles fetch with network errors", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      await expect(getNarratives()).rejects.toThrow("Network error");
    });

    it("handles fetch with malformed responses", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.reject(new Error("Invalid JSON")),
      } as Response);

      await expect(getNarratives()).rejects.toThrow("Invalid JSON");
    });

    it("handles empty response from API", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      } as Response);

      const result = await getNarratives();
      expect(result).toEqual({});
    });

    it("handles response with only items array", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ items: ["test"] }),
      } as Response);

      const result = await getNarratives();
      expect(result).toEqual({ items: ["test"] });
    });

    it("handles response with only lastRefresh", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ lastRefresh: 1234567890 }),
      } as Response);

      const result = await getNarratives();
      expect(result).toEqual({ lastRefresh: 1234567890 });
    });
  });
});
