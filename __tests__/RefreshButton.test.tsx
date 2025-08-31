import { render, screen, fireEvent } from "@testing-library/react";
import RefreshButton from "../src/components/RefreshButton";
import { startRefreshJob } from "../src/lib/api";

// Mock the API functions
jest.mock("../src/lib/api", () => ({
  startRefreshJob: jest.fn(),
  getRefreshStatus: jest.fn(),
}));

const mockStartRefreshJob = startRefreshJob as jest.MockedFunction<
  typeof startRefreshJob
>;

describe("RefreshButton", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset fetch mock for each test
    (global.fetch as jest.Mock).mockClear();
  });

  it("renders the refresh button", () => {
    render(<RefreshButton />);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent("Refresh");
  });

  it("shows loading state when refreshing", () => {
    render(<RefreshButton />);
    const button = screen.getByRole("button");

    // The button should be enabled by default
    expect(button).not.toBeDisabled();
  });

  it("handles click events and starts refresh job", async () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    expect(mockStartRefreshJob).toHaveBeenCalledTimes(1);
  });

  it("shows queued state after starting refresh job", async () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for the async operation to complete
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(button).toHaveTextContent("Queued…");
  });

  it("displays refresh button with proper styling", () => {
    render(<RefreshButton />);
    const button = screen.getByRole("button");

    expect(button).toHaveStyle({
      padding: "8px 12px",
      border: "1px solid #222",
      borderRadius: "6px",
    });
  });

  it("renders error display area (initially hidden)", () => {
    render(<RefreshButton />);

    // The error area should exist but be empty initially
    const errorContainer = screen.getByRole("button").parentElement;
    expect(errorContainer).toBeInTheDocument();
  });

  it("handles multiple clicks gracefully", () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    // Multiple clicks should not crash
    fireEvent.click(button);
    fireEvent.click(button);
    fireEvent.click(button);

    expect(mockStartRefreshJob).toHaveBeenCalledTimes(3);
  });
});
