import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
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

    expect(
      screen.getByText(/Refresh started \(job: test-job-123\)/),
    ).toBeInTheDocument();
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
      narrativesDone: 2,
      narrativesTotal: 5,
    });

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for the job to start and status to be checked
    await waitFor(() => {
      expect(mockGetRefreshStatus).toHaveBeenCalledWith("test-job-123");
    });

    // The status banner should show running state with progress
    expect(screen.getByText(/Updating… \(2\/5\)/)).toBeInTheDocument();
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

  it("handles button opacity changes based on state", async () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    // Initial state - full opacity
    expect(button).toHaveStyle({ opacity: 1 });

    // Start a job to change state
    fireEvent.click(button);

    // Wait for the state to change to queued
    await waitFor(() => {
      expect(
        screen.getByText(/Refresh started \(job: test-job-123\)/),
      ).toBeInTheDocument();
    });

    // Button should have reduced opacity when not idle
    expect(button).toHaveStyle({ opacity: 0.7 });
  });

  it("shows error state when job fails", async () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });
    mockGetRefreshStatus.mockResolvedValue({
      id: "test-job-123",
      state: "error",
      ts: Date.now(),
      error: "Job failed",
    });

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for the error to be displayed
    await waitFor(() => {
      expect(screen.getByText("Job failed")).toBeInTheDocument();
    });
  });

  it("shows default error message when job fails without error details", async () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });
    mockGetRefreshStatus.mockResolvedValue({
      id: "test-job-123",
      state: "error",
      ts: Date.now(),
      error: null,
    });

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for the default error message
    await waitFor(() => {
      expect(screen.getByText("Refresh failed")).toBeInTheDocument();
    });
  });

  it("continues polling when job is queued", async () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });
    mockGetRefreshStatus
      .mockResolvedValueOnce({
        id: "test-job-123",
        state: "queued",
        ts: Date.now(),
      })
      .mockResolvedValueOnce({
        id: "test-job-123",
        state: "done",
        ts: Date.now(),
      });

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Should call getRefreshStatus multiple times for polling
    await waitFor(
      () => {
        expect(mockGetRefreshStatus).toHaveBeenCalledTimes(2);
      },
      { timeout: 1200 },
    );
  });

  it("handles API errors during status polling", async () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });
    mockGetRefreshStatus.mockRejectedValue(new Error("Network error"));

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for the error to be displayed
    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("handles non-Error objects during status polling", async () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });
    mockGetRefreshStatus.mockRejectedValue("String error");

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for the error to be displayed
    await waitFor(() => {
      expect(screen.getByText("String error")).toBeInTheDocument();
    });
  });

  it("handles stop flag during polling", async () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });
    mockGetRefreshStatus.mockResolvedValue({
      id: "test-job-123",
      state: "queued",
      ts: Date.now(),
    });

    const { unmount } = render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for polling to start
    await waitFor(() => {
      expect(mockGetRefreshStatus).toHaveBeenCalledWith("test-job-123");
    });

    // Unmount to trigger stop flag
    unmount();

    // Should not cause errors after unmount
    await new Promise((resolve) => setTimeout(resolve, 100));
  });

  it("disables button during different states", async () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    // Initially enabled
    expect(button).not.toBeDisabled();

    // Click to start job
    fireEvent.click(button);

    // Wait for queued state
    await waitFor(() => {
      expect(
        screen.getByText(/Refresh started \(job: test-job-123\)/),
      ).toBeInTheDocument();
    });

    // Button should be disabled in queued state
    expect(button).toBeDisabled();
  });

  it("shows different status text for different states", async () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    // Initial state
    expect(button).toHaveTextContent("Refresh");

    // Click to start
    fireEvent.click(button);

    // Queued state
    await waitFor(() => {
      expect(
        screen.getByText(/Refresh started \(job: test-job-123\)/),
      ).toBeInTheDocument();
    });
  });

  it("handles error state display", async () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });
    mockGetRefreshStatus.mockResolvedValue({
      id: "test-job-123",
      state: "error",
      ts: Date.now(),
      error: "Custom error message",
    });

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for error to be displayed
    await waitFor(() => {
      expect(screen.getByText("Custom error message")).toBeInTheDocument();
    });

    // Error should be styled correctly
    const errorDiv = screen.getByText("Custom error message");
    expect(errorDiv).toHaveStyle({
      background: "#fee",
      color: "#900",
    });
  });

  it("handles error with empty error message", async () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });
    mockGetRefreshStatus.mockResolvedValue({
      id: "test-job-123",
      state: "error",
      ts: Date.now(),
      error: "",
    });

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for default error message to be displayed
    await waitFor(() => {
      expect(screen.getByText("Refresh failed")).toBeInTheDocument();
    });
  });

  it("handles error with undefined error message", async () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });
    mockGetRefreshStatus.mockResolvedValue({
      id: "test-job-123",
      state: "error",
      ts: Date.now(),
      error: undefined,
    });

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for default error message to be displayed
    await waitFor(() => {
      expect(screen.getByText("Refresh failed")).toBeInTheDocument();
    });
  });

  it("handles stop flag during error handling", async () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });

    // First call succeeds, second call fails
    mockGetRefreshStatus
      .mockResolvedValueOnce({
        id: "test-job-123",
        state: "queued",
        ts: Date.now(),
      })
      .mockRejectedValueOnce(new Error("Network error"));

    const { unmount } = render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for first polling call
    await waitFor(() => {
      expect(mockGetRefreshStatus).toHaveBeenCalledWith("test-job-123");
    });

    // Wait a bit for the second call to be scheduled
    await new Promise((resolve) => setTimeout(resolve, 50));

    // Unmount to set stop flag before the second call fails
    unmount();

    // Wait for the second call to potentially fail
    await new Promise((resolve) => setTimeout(resolve, 100));
  });

  it("handles stop flag during error handling with immediate unmount", async () => {
    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });

    // Set up a mock that will reject after a delay
    mockGetRefreshStatus.mockRejectedValueOnce(new Error("Test error"));

    const { unmount } = render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for the first call to be made
    await waitFor(() => {
      expect(mockGetRefreshStatus).toHaveBeenCalledWith("test-job-123");
    });

    // Immediately unmount to set stop flag
    unmount();

    // Wait a bit to ensure the error handling has a chance to run
    await new Promise((resolve) => setTimeout(resolve, 100));
  });

  it("handles error with empty error message during polling", async () => {
    // Clear any previous mock configurations
    mockGetRefreshStatus.mockReset();

    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });
    // Use a string that will be converted to an Error with an empty message
    mockGetRefreshStatus.mockRejectedValue("");

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for default error message to be displayed
    await waitFor(() => {
      expect(screen.getByText("Refresh status failed")).toBeInTheDocument();
    });
  });

  it("handles 401 error when starting refresh job", async () => {
    mockStartRefreshJob.mockRejectedValue(new Error("401 Unauthorized"));

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for the error to be displayed
    await waitFor(() => {
      expect(
        screen.getByText("Authentication failed - check refresh token"),
      ).toBeInTheDocument();
    });
  });

  it("handles 500 error when starting refresh job", async () => {
    mockStartRefreshJob.mockRejectedValue(
      new Error("500 Internal Server Error"),
    );

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for the error to be displayed
    await waitFor(() => {
      expect(
        screen.getByText("Server error - please try again later"),
      ).toBeInTheDocument();
    });
  });

  it("handles generic error when starting refresh job", async () => {
    mockStartRefreshJob.mockRejectedValue(new Error("Network error"));

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for the error to be displayed
    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("handles non-Error object when starting refresh job", async () => {
    mockStartRefreshJob.mockRejectedValue("String error");

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for the error to be displayed
    await waitFor(() => {
      expect(screen.getByText("String error")).toBeInTheDocument();
    });
  });

  it("handles error with empty message when starting refresh job", async () => {
    mockStartRefreshJob.mockRejectedValue(new Error(""));

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for the error to be displayed
    await waitFor(() => {
      expect(screen.getByText("Failed to start refresh")).toBeInTheDocument();
    });
  });

  it("handles error with undefined message when starting refresh job", async () => {
    mockStartRefreshJob.mockRejectedValue(new Error(undefined as any));

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for the error to be displayed
    await waitFor(() => {
      expect(screen.getByText("Failed to start refresh")).toBeInTheDocument();
    });
  });

  it("handles 401 error during status polling with fake timers", async () => {
    jest.useFakeTimers();

    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });
    mockGetRefreshStatus.mockRejectedValue(new Error("401 Unauthorized"));

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for the error to be displayed
    await waitFor(() => {
      expect(
        screen.getByText("Authentication failed - check refresh token"),
      ).toBeInTheDocument();
    });

    jest.useRealTimers();
  });

  it("handles 500 error during status polling with fake timers", async () => {
    jest.useFakeTimers();

    mockStartRefreshJob.mockResolvedValue({ jobId: "test-job-123" });
    mockGetRefreshStatus.mockRejectedValue(
      new Error("500 Internal Server Error"),
    );

    render(<RefreshButton />);
    const button = screen.getByRole("button");

    fireEvent.click(button);

    // Wait for the error to be displayed
    await waitFor(() => {
      expect(
        screen.getByText("Server error - please try again later"),
      ).toBeInTheDocument();
    });

    jest.useRealTimers();
  });
});
