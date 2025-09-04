import { render, screen, act } from "@testing-library/react";
import StaleBanner from "../src/components/StaleBanner";

// Mock timers for testing time-based functionality
jest.useFakeTimers();

describe("StaleBanner", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("renders stale banner when stale is true", () => {
    const lastUpdated = Math.floor(Date.now() / 1000) - 300; // 5 minutes ago
    render(<StaleBanner stale={true} lastUpdated={lastUpdated} />);

    expect(screen.getByText(/Data may be stale/)).toBeInTheDocument();
    expect(screen.getByText(/5m ago/)).toBeInTheDocument();
  });

  it("renders fresh banner when stale is false", () => {
    const lastUpdated = Math.floor(Date.now() / 1000) - 300; // 5 minutes ago
    render(<StaleBanner stale={false} lastUpdated={lastUpdated} />);

    expect(screen.getByText(/Fresh as of/)).toBeInTheDocument();
    expect(screen.getByText(/5m ago/)).toBeInTheDocument();
  });

  it("shows 'just now' for recent timestamps", () => {
    const lastUpdated = Math.floor(Date.now() / 1000) - 30; // 30 seconds ago
    render(<StaleBanner stale={true} lastUpdated={lastUpdated} />);

    expect(screen.getByText(/just now/)).toBeInTheDocument();
  });

  it("shows 'unknown' when lastUpdated is null", () => {
    render(<StaleBanner stale={true} lastUpdated={null} />);

    expect(screen.getByText(/unknown/)).toBeInTheDocument();
  });

  it("shows 'unknown' when lastUpdated is undefined", () => {
    render(<StaleBanner stale={true} lastUpdated={undefined} />);

    expect(screen.getByText(/unknown/)).toBeInTheDocument();
  });

  it("shows 'unknown' when lastUpdated is 0", () => {
    render(<StaleBanner stale={true} lastUpdated={0} />);

    expect(screen.getByText(/unknown/)).toBeInTheDocument();
  });

  it("formats time correctly for minutes", () => {
    const lastUpdated = Math.floor(Date.now() / 1000) - 120; // 2 minutes ago
    render(<StaleBanner stale={true} lastUpdated={lastUpdated} />);

    expect(screen.getByText(/2m ago/)).toBeInTheDocument();
  });

  it("formats time correctly for hours", () => {
    const lastUpdated = Math.floor(Date.now() / 1000) - 7200; // 2 hours ago
    render(<StaleBanner stale={true} lastUpdated={lastUpdated} />);

    expect(screen.getByText(/2h ago/)).toBeInTheDocument();
  });

  it("formats time correctly for days", () => {
    const lastUpdated = Math.floor(Date.now() / 1000) - 172800; // 2 days ago
    render(<StaleBanner stale={true} lastUpdated={lastUpdated} />);

    expect(screen.getByText(/2d ago/)).toBeInTheDocument();
  });

  it("updates time display every minute", () => {
    const lastUpdated = Math.floor(Date.now() / 1000) - 60; // 1 minute ago
    render(<StaleBanner stale={true} lastUpdated={lastUpdated} />);

    expect(screen.getByText(/1m ago/)).toBeInTheDocument();

    // Advance time by 30 seconds
    act(() => {
      jest.advanceTimersByTime(30000);
    });

    // Should still show 1m ago
    expect(screen.getByText(/1m ago/)).toBeInTheDocument();

    // Advance time by another 30 seconds (total 1 minute)
    act(() => {
      jest.advanceTimersByTime(30000);
    });

    // Should now show 2m ago
    expect(screen.getByText(/2m ago/)).toBeInTheDocument();
  });

  it("clears interval on unmount", () => {
    const clearIntervalSpy = jest.spyOn(global, "clearInterval");
    const lastUpdated = Math.floor(Date.now() / 1000) - 60;
    const { unmount } = render(
      <StaleBanner stale={true} lastUpdated={lastUpdated} />,
    );

    unmount();

    expect(clearIntervalSpy).toHaveBeenCalled();
    clearIntervalSpy.mockRestore();
  });

  it("does not set interval when lastUpdated is null", () => {
    const setIntervalSpy = jest.spyOn(global, "setInterval");
    render(<StaleBanner stale={true} lastUpdated={null} />);

    expect(setIntervalSpy).not.toHaveBeenCalled();
    setIntervalSpy.mockRestore();
  });

  it("does not set interval when lastUpdated is undefined", () => {
    const setIntervalSpy = jest.spyOn(global, "setInterval");
    render(<StaleBanner stale={true} lastUpdated={undefined} />);

    expect(setIntervalSpy).not.toHaveBeenCalled();
    setIntervalSpy.mockRestore();
  });

  it("does not set interval when lastUpdated is 0", () => {
    const setIntervalSpy = jest.spyOn(global, "setInterval");
    render(<StaleBanner stale={true} lastUpdated={0} />);

    expect(setIntervalSpy).not.toHaveBeenCalled();
    setIntervalSpy.mockRestore();
  });

  it("handles edge case of exactly 60 seconds", () => {
    const lastUpdated = Math.floor(Date.now() / 1000) - 60; // exactly 1 minute
    render(<StaleBanner stale={true} lastUpdated={lastUpdated} />);

    expect(screen.getByText(/1m ago/)).toBeInTheDocument();
  });

  it("handles edge case of exactly 3600 seconds", () => {
    const lastUpdated = Math.floor(Date.now() / 1000) - 3600; // exactly 1 hour
    render(<StaleBanner stale={true} lastUpdated={lastUpdated} />);

    expect(screen.getByText(/1h ago/)).toBeInTheDocument();
  });

  it("handles edge case of exactly 86400 seconds", () => {
    const lastUpdated = Math.floor(Date.now() / 1000) - 86400; // exactly 1 day
    render(<StaleBanner stale={true} lastUpdated={lastUpdated} />);

    expect(screen.getByText(/1d ago/)).toBeInTheDocument();
  });

  it("handles very old timestamps", () => {
    const lastUpdated = Math.floor(Date.now() / 1000) - 2592000; // 30 days ago
    render(<StaleBanner stale={true} lastUpdated={lastUpdated} />);

    expect(screen.getByText(/30d ago/)).toBeInTheDocument();
  });

  it("handles future timestamps gracefully", () => {
    const lastUpdated = Math.floor(Date.now() / 1000) + 60; // 1 minute in the future
    render(<StaleBanner stale={true} lastUpdated={lastUpdated} />);

    // Should show "just now" for future timestamps
    expect(screen.getByText(/just now/)).toBeInTheDocument();
  });

  it("updates when lastUpdated prop changes", () => {
    const { rerender } = render(
      <StaleBanner stale={true} lastUpdated={null} />,
    );

    expect(screen.getByText(/unknown/)).toBeInTheDocument();

    const newTimestamp = Math.floor(Date.now() / 1000) - 120; // 2 minutes ago
    rerender(<StaleBanner stale={true} lastUpdated={newTimestamp} />);

    expect(screen.getByText(/2m ago/)).toBeInTheDocument();
  });

  it("clears old interval when lastUpdated changes", () => {
    const clearIntervalSpy = jest.spyOn(global, "clearInterval");
    const lastUpdated1 = Math.floor(Date.now() / 1000) - 60;
    const { rerender } = render(
      <StaleBanner stale={true} lastUpdated={lastUpdated1} />,
    );

    const lastUpdated2 = Math.floor(Date.now() / 1000) - 120;
    rerender(<StaleBanner stale={true} lastUpdated={lastUpdated2} />);

    expect(clearIntervalSpy).toHaveBeenCalled();
    clearIntervalSpy.mockRestore();
  });
});
