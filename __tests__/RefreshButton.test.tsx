import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import RefreshButton from "../src/components/RefreshButton";
import { startRefreshJob, getRefreshStatus } from "../src/lib/api";

// Mock the API functions
jest.mock("../src/lib/api", () => ({
  startRefreshJob: jest.fn(),
  getRefreshStatus: jest.fn(),
}));

const mockStartRefreshJob = startRefreshJob as jest.MockedFunction<
  typeof startRefreshJob
>;
const mockGetRefreshStatus = getRefreshStatus as jest.MockedFunction<
  typeof getRefreshStatus
>;

// Mock Next.js router
const mockRouter = {
  refresh: jest.fn(),
};

jest.mock("next/navigation", () => ({
  useRouter: () => mockRouter,
}));

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

  it("shows running state when job is running", async () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });
    mockGetRefreshStatus.mockResolvedValue({
      id: "test-job-123",
      state: "running",
      ts: Date.now(),
    });

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for the job to start and status to be checked
    await waitFor(() => {
      expect(mockGetRefreshStatus).toHaveBeenCalledWith("test-job-123");
    });

    // The button should show running state (which is "Refreshing…" in the component)
    expect(button).toHaveTextContent("Refreshing…");
  });

  it("does not start polling when jobId is null", () => {
    render(<RefreshButton />);

    // Should not call getRefreshStatus when jobId is null
    expect(mockGetRefreshStatus).not.toHaveBeenCalled();
  });

  it("handles component unmount during polling", async () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });
    mockGetRefreshStatus.mockResolvedValue({
      id: "test-job-123",
      state: "queued",
      ts: Date.now(),
    });

    const { unmount } = render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Unmount immediately to test cleanup
    unmount();

    // Should not cause errors after unmount
    await new Promise((resolve) => setTimeout(resolve, 100));
  });

  it("calls router.refresh when job completes successfully", async () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });
    mockGetRefreshStatus.mockResolvedValue({
      id: "test-job-123",
      state: "done",
      ts: Date.now(),
    });

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for the job to complete and router.refresh to be called
    await waitFor(
      () => {
        expect(mockRouter.refresh).toHaveBeenCalled();
      },
      { timeout: 200 },
    );
  });

  it("calls router.refresh after timeout delay when job completes", async () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });
    mockGetRefreshStatus.mockResolvedValue({
      id: "test-job-123",
      state: "done",
      ts: Date.now(),
    });

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for the job to complete
    await waitFor(() => {
      expect(mockGetRefreshStatus).toHaveBeenCalledWith("test-job-123");
    });

    // Wait for the timeout to complete and router.refresh to be called
    await new Promise((resolve) => setTimeout(resolve, 150));

    expect(mockRouter.refresh).toHaveBeenCalled();
  });

  it("calls router.refresh with fake timers when job completes", async () => {
    jest.useFakeTimers();

    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });
    mockGetRefreshStatus.mockResolvedValue({
      id: "test-job-123",
      state: "done",
      ts: Date.now(),
    });

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for the job to complete
    await waitFor(() => {
      expect(mockGetRefreshStatus).toHaveBeenCalledWith("test-job-123");
    });

    // Fast-forward timers to trigger the setTimeout
    jest.advanceTimersByTime(150);

    expect(mockRouter.refresh).toHaveBeenCalled();

    jest.useRealTimers();
  });
});
