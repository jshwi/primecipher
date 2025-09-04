import { render, screen } from "@testing-library/react";
import Page from "../src/app/page";

// Mock the API module
jest.mock("../src/lib/api", () => ({
  getNarratives: jest.fn(),
}));

// Mock Next.js Link component
jest.mock("next/link", () => ({
  __esModule: true,
  default: ({ children, href, ...props }: any) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

describe("Main Page", () => {
  const mockGetNarratives = require("../src/lib/api").getNarratives;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the main page content", async () => {
    mockGetNarratives.mockResolvedValue({
      items: ["dogs", "ai"],
      lastRefresh: 1704067200,
    });

    render(await Page());

    expect(screen.getByText("Narratives (24h)")).toBeInTheDocument();
    expect(screen.getByText("dogs")).toBeInTheDocument();
    expect(screen.getByText("ai")).toBeInTheDocument();
  });

  it("displays narrative links", async () => {
    mockGetNarratives.mockResolvedValue({
      items: ["dogs", "ai"],
      lastRefresh: 1704067200,
    });

    render(await Page());

    expect(screen.getByText("dogs")).toBeInTheDocument();
    expect(screen.getByText("ai")).toBeInTheDocument();
  });

  it("shows stale banner with fresh status", async () => {
    mockGetNarratives.mockResolvedValue({
      items: ["dogs", "ai"],
      lastRefresh: 1704067200,
      stale: false,
      lastUpdated: 1704067200,
    });

    render(await Page());

    expect(screen.getByText(/Fresh as of/)).toBeInTheDocument();
  });

  it("handles empty narratives array", async () => {
    mockGetNarratives.mockResolvedValue({
      items: [],
      lastRefresh: null,
      stale: true,
      lastUpdated: null,
    });

    render(await Page());

    // Use a more flexible text matcher
    expect(screen.getByText(/No narratives yet/)).toBeInTheDocument();
    expect(
      screen.getByText(/backend\/seeds\/narratives\.seed\.json/),
    ).toBeInTheDocument();
  });

  it("handles narratives with count data format", async () => {
    mockGetNarratives.mockResolvedValue({
      items: [
        { narrative: "dogs", count: 5 },
        { narrative: "ai", count: 3 },
      ],
      lastRefresh: 1704067200,
      stale: false,
      lastUpdated: 1704067200,
    });

    render(await Page());

    expect(screen.getByText("dogs")).toBeInTheDocument();
    expect(screen.getByText("ai")).toBeInTheDocument();
  });

  it("handles mixed data format (strings and objects)", async () => {
    mockGetNarratives.mockResolvedValue({
      items: ["dogs", { narrative: "ai", count: 3 }, "blockchain"],
      lastRefresh: 1704067200,
      stale: false,
      lastUpdated: 1704067200,
    });

    render(await Page());

    expect(screen.getByText("dogs")).toBeInTheDocument();
    expect(screen.getByText("ai")).toBeInTheDocument();
    expect(screen.getByText("blockchain")).toBeInTheDocument();
  });

  it("filters out invalid narrative items", async () => {
    mockGetNarratives.mockResolvedValue({
      items: [
        "dogs",
        { narrative: null, count: 3 },
        { narrative: "", count: 2 },
        "ai",
        { narrative: undefined, count: 1 },
      ],
      lastRefresh: 1704067200,
      stale: false,
      lastUpdated: 1704067200,
    });

    render(await Page());

    expect(screen.getByText("dogs")).toBeInTheDocument();
    expect(screen.getByText("ai")).toBeInTheDocument();
    expect(screen.queryByText("null")).not.toBeInTheDocument();
    expect(screen.queryByText("undefined")).not.toBeInTheDocument();
  });

  it("handles missing lastRefresh field", async () => {
    mockGetNarratives.mockResolvedValue({
      items: ["dogs", "ai"],
      stale: true,
      lastUpdated: null,
    });

    render(await Page());

    expect(screen.getByText("dogs")).toBeInTheDocument();
    expect(screen.getByText("ai")).toBeInTheDocument();
    expect(screen.getByText(/Data may be stale/)).toBeInTheDocument();
  });

  it("handles null lastRefresh value", async () => {
    mockGetNarratives.mockResolvedValue({
      items: ["dogs", "ai"],
      lastRefresh: null,
      stale: true,
      lastUpdated: null,
    });

    render(await Page());

    expect(screen.getByText("dogs")).toBeInTheDocument();
    expect(screen.getByText("ai")).toBeInTheDocument();
    expect(screen.getByText(/Data may be stale/)).toBeInTheDocument();
  });

  it("handles zero timestamp for lastRefresh", async () => {
    mockGetNarratives.mockResolvedValue({
      items: ["dogs", "ai"],
      lastRefresh: 0,
      stale: true,
      lastUpdated: null,
    });

    render(await Page());

    expect(screen.getByText("dogs")).toBeInTheDocument();
    expect(screen.getByText("ai")).toBeInTheDocument();
    expect(screen.getByText(/Data may be stale/)).toBeInTheDocument();
  });

  it("displays refresh button", async () => {
    mockGetNarratives.mockResolvedValue({
      items: ["dogs", "ai"],
      lastRefresh: 1704067200,
      stale: false,
      lastUpdated: 1704067200,
    });

    render(await Page());

    expect(
      screen.getByRole("button", { name: /refresh/i }),
    ).toBeInTheDocument();
  });

  it("renders narrative links with proper hrefs", async () => {
    mockGetNarratives.mockResolvedValue({
      items: ["dogs", "ai"],
      lastRefresh: 1704067200,
      stale: false,
      lastUpdated: 1704067200,
    });

    render(await Page());

    const dogsLink = screen.getByText("dogs").closest("a");
    const aiLink = screen.getByText("ai").closest("a");

    expect(dogsLink).toHaveAttribute("href", "/n/dogs");
    expect(aiLink).toHaveAttribute("href", "/n/ai");
  });

  it("handles non-array items data gracefully", async () => {
    mockGetNarratives.mockResolvedValue({
      items: "not an array",
      lastRefresh: 1704067200,
      stale: true,
      lastUpdated: null,
    });

    render(await Page());

    // Should show empty state when items is not an array
    expect(screen.getByText(/No narratives yet/)).toBeInTheDocument();
  });

  it("handles undefined items data gracefully", async () => {
    mockGetNarratives.mockResolvedValue({
      lastRefresh: 1704067200,
      stale: true,
      lastUpdated: null,
    });

    render(await Page());

    // Should show empty state when items is undefined
    expect(screen.getByText(/No narratives yet/)).toBeInTheDocument();
  });

  it("handles null items data gracefully", async () => {
    mockGetNarratives.mockResolvedValue({
      items: null,
      lastRefresh: 1704067200,
      stale: true,
      lastUpdated: null,
    });

    render(await Page());

    // Should show empty state when items is null
    expect(screen.getByText(/No narratives yet/)).toBeInTheDocument();
  });

  it("handles API error and shows error message", async () => {
    mockGetNarratives.mockRejectedValue(new Error("API connection failed"));

    render(await Page());

    expect(
      screen.getByText(/Backend unavailable: API connection failed/),
    ).toBeInTheDocument();
    expect(screen.getByText(/No narratives yet/)).toBeInTheDocument();
  });

  it("handles non-Error object in catch block", async () => {
    mockGetNarratives.mockRejectedValue("String error");

    render(await Page());

    expect(
      screen.getByText(/Backend unavailable: Failed to fetch data/),
    ).toBeInTheDocument();
    expect(screen.getByText(/No narratives yet/)).toBeInTheDocument();
  });

  it("handles undefined error in catch block", async () => {
    mockGetNarratives.mockRejectedValue(undefined);

    render(await Page());

    expect(
      screen.getByText(/Backend unavailable: Failed to fetch data/),
    ).toBeInTheDocument();
    expect(screen.getByText(/No narratives yet/)).toBeInTheDocument();
  });

  it("handles null error in catch block", async () => {
    mockGetNarratives.mockRejectedValue(null);

    render(await Page());

    expect(
      screen.getByText(/Backend unavailable: Failed to fetch data/),
    ).toBeInTheDocument();
    expect(screen.getByText(/No narratives yet/)).toBeInTheDocument();
  });
});
