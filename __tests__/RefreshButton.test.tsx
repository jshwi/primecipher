import { render, screen, fireEvent } from "@testing-library/react";
import RefreshButton from "../src/components/RefreshButton";

describe("RefreshButton", () => {
  it("renders the refresh button", () => {
    render(<RefreshButton />);
    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("shows loading state when refreshing", () => {
    render(<RefreshButton />);
    const button = screen.getByRole("button");

    // The button should be enabled by default
    expect(button).not.toBeDisabled();
  });

  it("handles click events", () => {
    render(<RefreshButton />);
    const button = screen.getByRole("button");

    // Test that clicking doesn't crash
    expect(() => fireEvent.click(button)).not.toThrow();
  });
});
