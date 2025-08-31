import { render, screen } from "@testing-library/react";
import Page from "../src/app/page";

// Mock the API module
jest.mock("../src/lib/api", () => ({
  getNarratives: jest.fn(() =>
    Promise.resolve({
      items: ["dogs", "ai"],
      lastRefresh: 1704067200,
    }),
  ),
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
  it("renders the main page content", async () => {
    render(await Page());

    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(screen.getByText("Narratives (24h)")).toBeInTheDocument();
  });

  it("displays narrative links", async () => {
    render(await Page());

    expect(screen.getByText("dogs")).toBeInTheDocument();
    expect(screen.getByText("ai")).toBeInTheDocument();
  });

  it("shows last refresh timestamp", async () => {
    render(await Page());

    expect(screen.getByText(/Last refresh:/)).toBeInTheDocument();
  });
});
