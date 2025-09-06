import { render, screen } from "@testing-library/react";
import NarrativePage from "../src/app/n/[narrative]/page";

// Mock the API module
jest.mock("../src/lib/api", () => ({
  getParents: jest.fn(),
}));

// Mock the ParentsList component
jest.mock("../src/app/n/[narrative]/_components/ParentsList", () => {
  return function MockParentsList({
    narrative,
    initial,
    debug,
  }: {
    narrative: string;
    initial: any;
    debug?: boolean;
  }) {
    return (
      <div data-testid="parents-list">
        <div>Narrative: {narrative}</div>
        <div>Items: {initial.items.length}</div>
        <div>Debug: {debug ? "true" : "false"}</div>
      </div>
    );
  };
});

const mockGetParents = require("../src/lib/api").getParents;

describe("NarrativePage", () => {
  const mockParentsResponse = {
    narrative: "test-narrative",
    window: "24h",
    items: [
      { parent: "Bitcoin", matches: 10, sources: ["coingecko"] },
      { parent: "Ethereum", matches: 8, sources: ["dexscreener"] },
    ],
    nextCursor: null,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockGetParents.mockResolvedValue(mockParentsResponse);
  });

  it("renders narrative page without debug mode", async () => {
    const params = Promise.resolve({ narrative: "test-narrative" });
    const searchParams = Promise.resolve({});

    const component = await NarrativePage({ params, searchParams });
    render(component);

    expect(screen.getByText("test-narrative")).toBeInTheDocument();
    expect(screen.getByText("2 parents loaded")).toBeInTheDocument();
    expect(screen.queryByText("• Debug mode")).not.toBeInTheDocument();
    expect(screen.getByText("Debug: false")).toBeInTheDocument();

    expect(mockGetParents).toHaveBeenCalledWith("test-narrative", {
      limit: 25,
      debug: false,
    });
  });

  it("renders narrative page with debug mode when debug=1", async () => {
    const params = Promise.resolve({ narrative: "test-narrative" });
    const searchParams = Promise.resolve({ debug: "1" });

    const component = await NarrativePage({ params, searchParams });
    render(component);

    expect(screen.getByText("test-narrative")).toBeInTheDocument();
    expect(screen.getByText("2 parents loaded")).toBeInTheDocument();
    expect(screen.getByText("• Debug mode")).toBeInTheDocument();
    expect(screen.getByText("Debug: true")).toBeInTheDocument();

    expect(mockGetParents).toHaveBeenCalledWith("test-narrative", {
      limit: 25,
      debug: true,
    });
  });

  it("does not enable debug mode when debug=0", async () => {
    const params = Promise.resolve({ narrative: "test-narrative" });
    const searchParams = Promise.resolve({ debug: "0" });

    const component = await NarrativePage({ params, searchParams });
    render(component);

    expect(screen.getByText("test-narrative")).toBeInTheDocument();
    expect(screen.queryByText("• Debug mode")).not.toBeInTheDocument();
    expect(screen.getByText("Debug: false")).toBeInTheDocument();

    expect(mockGetParents).toHaveBeenCalledWith("test-narrative", {
      limit: 25,
      debug: false,
    });
  });

  it("does not enable debug mode when debug=true (string)", async () => {
    const params = Promise.resolve({ narrative: "test-narrative" });
    const searchParams = Promise.resolve({ debug: "true" });

    const component = await NarrativePage({ params, searchParams });
    render(component);

    expect(screen.getByText("test-narrative")).toBeInTheDocument();
    expect(screen.queryByText("• Debug mode")).not.toBeInTheDocument();
    expect(screen.getByText("Debug: false")).toBeInTheDocument();

    expect(mockGetParents).toHaveBeenCalledWith("test-narrative", {
      limit: 25,
      debug: false,
    });
  });

  it("passes correct narrative to ParentsList", async () => {
    const params = Promise.resolve({ narrative: "crypto-narrative" });
    const searchParams = Promise.resolve({ debug: "1" });

    const component = await NarrativePage({ params, searchParams });
    render(component);

    expect(screen.getByText("Narrative: crypto-narrative")).toBeInTheDocument();
  });

  it("passes initial data to ParentsList", async () => {
    const params = Promise.resolve({ narrative: "test-narrative" });
    const searchParams = Promise.resolve({});

    const component = await NarrativePage({ params, searchParams });
    render(component);

    expect(screen.getByText("Items: 2")).toBeInTheDocument();
  });

  it("handles empty parents response", async () => {
    mockGetParents.mockResolvedValue({
      narrative: "empty-narrative",
      window: "24h",
      items: [],
      nextCursor: null,
    });

    const params = Promise.resolve({ narrative: "empty-narrative" });
    const searchParams = Promise.resolve({});

    const component = await NarrativePage({ params, searchParams });
    render(component);

    expect(screen.getByText("empty-narrative")).toBeInTheDocument();
    expect(screen.getByText("0 parents loaded")).toBeInTheDocument();
    expect(screen.getByText("Items: 0")).toBeInTheDocument();
  });

  it("handles API errors gracefully", async () => {
    mockGetParents.mockRejectedValue(new Error("API Error"));

    const params = Promise.resolve({ narrative: "error-narrative" });
    const searchParams = Promise.resolve({});

    await expect(NarrativePage({ params, searchParams })).rejects.toThrow(
      "API Error",
    );
  });
});
