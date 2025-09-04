import { render, screen } from "@testing-library/react";
import Page from "../src/app/page";

// Mock the API module
jest.mock("../src/lib/api", () => ({
  getNarratives: jest.fn(),
  getHeatmap: jest.fn(),
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

// Mock the HomeClient component
jest.mock("../src/components/HomeClient", () => {
  return function MockHomeClient({ initialView }: { initialView: string }) {
    return (
      <div data-testid="home-client">
        <h1>PrimeCipher Dashboard</h1>
        <div>Initial View: {initialView}</div>
      </div>
    );
  };
});

describe("Main Page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the main page content", async () => {
    render(await Page({ searchParams: {} }));

    expect(screen.getByText("PrimeCipher Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Initial View: heatmap")).toBeInTheDocument();
  });

  it("passes correct initial view to HomeClient", async () => {
    render(await Page({ searchParams: {} }));

    expect(screen.getByText("Initial View: heatmap")).toBeInTheDocument();
  });

  it("handles narratives view from searchParams", async () => {
    render(await Page({ searchParams: { view: "narratives" } }));

    expect(screen.getByText("PrimeCipher Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Initial View: narratives")).toBeInTheDocument();
  });
});
