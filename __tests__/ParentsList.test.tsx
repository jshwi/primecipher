import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ParentsList from "../src/app/n/[narrative]/_components/ParentsList";
import type { ParentItem } from "../src/lib/api";

// Mock the API_BASE config
jest.mock("../src/lib/config", () => ({
  API_BASE: "http://localhost:8000",
}));

// Mock fetch globally
global.fetch = jest.fn();
const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

describe("ParentsList", () => {
  const mockItems: ParentItem[] = [
    {
      parent: "Bitcoin",
      matches: 10,
      score: 0.95,
      symbol: "BTC",
      sources: ["coingecko"],
    },
    {
      parent: "Ethereum",
      matches: 8,
      score: 0.88,
      symbol: "ETH",
      sources: ["dexscreener"],
    },
    {
      parent: "Solana",
      matches: 6,
      score: 0.75,
      symbol: "SOL",
      sources: ["coingecko", "dexscreener"],
    },
    {
      parent: "Cardano",
      matches: 4,
      score: 0.65,
      symbol: "ADA",
      sources: [],
    },
  ];

  const mockInitial = {
    items: mockItems,
    nextCursor: null,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Debug Mode", () => {
    it("displays source badges when debug=true", () => {
      render(
        <ParentsList narrative="crypto" initial={mockInitial} debug={true} />,
      );

      // Check for source badges
      expect(screen.getByText("C")).toBeInTheDocument(); // Bitcoin - coingecko only
      expect(screen.getByText("D")).toBeInTheDocument(); // Ethereum - dexscreener only
      expect(screen.getByText("C+D")).toBeInTheDocument(); // Solana - both
      expect(screen.getByText("—")).toBeInTheDocument(); // Cardano - no sources
    });

    it("hides source badges when debug=false", () => {
      render(
        <ParentsList narrative="crypto" initial={mockInitial} debug={false} />,
      );

      // Check that source badges are not present
      expect(screen.queryByText("C")).not.toBeInTheDocument();
      expect(screen.queryByText("D")).not.toBeInTheDocument();
      expect(screen.queryByText("C+D")).not.toBeInTheDocument();
      expect(screen.queryByText("—")).not.toBeInTheDocument();
    });

    it("defaults to debug=false when debug prop is not provided", () => {
      render(<ParentsList narrative="crypto" initial={mockInitial} />);

      // Check that source badges are not present
      expect(screen.queryByText("C")).not.toBeInTheDocument();
      expect(screen.queryByText("D")).not.toBeInTheDocument();
      expect(screen.queryByText("C+D")).not.toBeInTheDocument();
    });

    it("includes debug parameter in load more requests when debug=true", async () => {
      const mockResponse = {
        items: [
          {
            parent: "Polygon",
            matches: 3,
            score: 0.6,
            sources: ["coingecko"],
          },
        ],
        nextCursor: null,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response);

      render(
        <ParentsList
          narrative="crypto"
          initial={{ items: mockItems, nextCursor: "next-page" }}
          debug={true}
        />,
      );

      const loadMoreButton = screen.getByText("Load more");
      fireEvent.click(loadMoreButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining("debug=true"),
        );
      });

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/parents/crypto?limit=25&cursor=next-page&debug=true",
      );
    });

    it("excludes debug parameter in load more requests when debug=false", async () => {
      const mockResponse = {
        items: [
          {
            parent: "Polygon",
            matches: 3,
            score: 0.6,
          },
        ],
        nextCursor: null,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response);

      render(
        <ParentsList
          narrative="crypto"
          initial={{ items: mockItems, nextCursor: "next-page" }}
          debug={false}
        />,
      );

      const loadMoreButton = screen.getByText("Load more");
      fireEvent.click(loadMoreButton);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.not.stringContaining("debug=true"),
        );
      });

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/parents/crypto?limit=25&cursor=next-page",
      );
    });
  });

  describe("Source Badge Rendering", () => {
    it("renders 'C' for coingecko-only sources", () => {
      const item: ParentItem = {
        parent: "Test Coin",
        matches: 5,
        sources: ["coingecko"],
      };

      render(
        <ParentsList
          narrative="test"
          initial={{ items: [item], nextCursor: null }}
          debug={true}
        />,
      );

      expect(screen.getByText("C")).toBeInTheDocument();
    });

    it("renders 'D' for dexscreener-only sources", () => {
      const item: ParentItem = {
        parent: "Test Coin",
        matches: 5,
        sources: ["dexscreener"],
      };

      render(
        <ParentsList
          narrative="test"
          initial={{ items: [item], nextCursor: null }}
          debug={true}
        />,
      );

      expect(screen.getByText("D")).toBeInTheDocument();
    });

    it("renders 'C+D' for both sources", () => {
      const item: ParentItem = {
        parent: "Test Coin",
        matches: 5,
        sources: ["coingecko", "dexscreener"],
      };

      render(
        <ParentsList
          narrative="test"
          initial={{ items: [item], nextCursor: null }}
          debug={true}
        />,
      );

      expect(screen.getByText("C+D")).toBeInTheDocument();
    });

    it("renders '—' for empty or missing sources", () => {
      const itemEmpty: ParentItem = {
        parent: "Test Coin 1",
        matches: 5,
        sources: [],
      };

      const itemUndefined: ParentItem = {
        parent: "Test Coin 2",
        matches: 3,
      };

      render(
        <ParentsList
          narrative="test"
          initial={{ items: [itemEmpty, itemUndefined], nextCursor: null }}
          debug={true}
        />,
      );

      const dashElements = screen.getAllByText("—");
      expect(dashElements).toHaveLength(2);
    });

    it("renders empty string for unknown sources", () => {
      const item: ParentItem = {
        parent: "Test Coin",
        matches: 5,
        sources: ["unknown-source"],
      };

      render(
        <ParentsList
          narrative="test"
          initial={{ items: [item], nextCursor: null }}
          debug={true}
        />,
      );

      expect(screen.getByText("—")).toBeInTheDocument();
    });
  });

  describe("Non-Debug Mode Behavior", () => {
    it("displays all parent information without source badges", () => {
      render(
        <ParentsList narrative="crypto" initial={mockInitial} debug={false} />,
      );

      // Check that parent names are displayed
      expect(screen.getByText("Bitcoin")).toBeInTheDocument();
      expect(screen.getByText("Ethereum")).toBeInTheDocument();
      expect(screen.getByText("Solana")).toBeInTheDocument();
      expect(screen.getByText("Cardano")).toBeInTheDocument();

      // Check that matches and scores are displayed
      expect(screen.getByText("Matches: 10")).toBeInTheDocument();
      expect(screen.getByText("Score: 0.9500")).toBeInTheDocument();

      // Check that symbols are displayed
      expect(screen.getByText("BTC")).toBeInTheDocument();
      expect(screen.getByText("ETH")).toBeInTheDocument();
    });

    it("handles load more without debug parameter", async () => {
      const mockResponse = {
        items: [
          {
            parent: "New Coin",
            matches: 2,
            score: 0.5,
          },
        ],
        nextCursor: null,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response);

      render(
        <ParentsList
          narrative="crypto"
          initial={{ items: mockItems.slice(0, 2), nextCursor: "next-page" }}
          debug={false}
        />,
      );

      const loadMoreButton = screen.getByText("Load more");
      fireEvent.click(loadMoreButton);

      await waitFor(() => {
        expect(screen.getByText("New Coin")).toBeInTheDocument();
      });

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:8000/parents/crypto?limit=25&cursor=next-page",
      );
    });
  });

  describe("Error Handling", () => {
    it("handles fetch errors in debug mode", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      render(
        <ParentsList
          narrative="crypto"
          initial={{ items: mockItems, nextCursor: "next-page" }}
          debug={true}
        />,
      );

      const loadMoreButton = screen.getByText("Load more");
      fireEvent.click(loadMoreButton);

      await waitFor(() => {
        expect(screen.getByText("Network error")).toBeInTheDocument();
      });
    });

    it("handles HTTP errors in debug mode", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      } as Response);

      render(
        <ParentsList
          narrative="crypto"
          initial={{ items: mockItems, nextCursor: "next-page" }}
          debug={true}
        />,
      );

      const loadMoreButton = screen.getByText("Load more");
      fireEvent.click(loadMoreButton);

      await waitFor(() => {
        expect(screen.getByText("Failed to load: 500")).toBeInTheDocument();
      });
    });

    it("handles 400 errors with invalid cursor message", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
      } as Response);

      render(
        <ParentsList
          narrative="crypto"
          initial={{ items: mockItems, nextCursor: "next-page" }}
          debug={true}
        />,
      );

      const loadMoreButton = screen.getByText("Load more");
      fireEvent.click(loadMoreButton);

      await waitFor(() => {
        expect(screen.getByText("Invalid cursor")).toBeInTheDocument();
      });
    });

    it("handles non-Error exceptions", async () => {
      mockFetch.mockRejectedValueOnce("String error");

      render(
        <ParentsList
          narrative="crypto"
          initial={{ items: mockItems, nextCursor: "next-page" }}
          debug={true}
        />,
      );

      const loadMoreButton = screen.getByText("Load more");
      fireEvent.click(loadMoreButton);

      await waitFor(() => {
        expect(screen.getByText("Failed to load more")).toBeInTheDocument();
      });
    });
  });

  describe("Edge Cases", () => {
    it("handles items with unexpected structure", () => {
      const unexpectedItems: ParentItem[] = [
        {
          parent: "Test",
          matches: 5,
          // Missing expected structure
        } as any,
      ];

      render(
        <ParentsList
          narrative="test"
          initial={{ items: unexpectedItems, nextCursor: null }}
          debug={true}
        />,
      );

      // Should render fallback JSON display
      expect(screen.getByText(/Test/)).toBeInTheDocument();
    });

    it("handles load more when no nextCursor", () => {
      render(
        <ParentsList
          narrative="crypto"
          initial={{ items: mockItems, nextCursor: null }}
          debug={true}
        />,
      );

      // Should not show load more button
      expect(screen.queryByText("Load more")).not.toBeInTheDocument();
    });

    it("handles load more when already loading", async () => {
      mockFetch.mockImplementationOnce(
        () => new Promise(() => {}), // Never resolves
      );

      render(
        <ParentsList
          narrative="crypto"
          initial={{ items: mockItems, nextCursor: "next-page" }}
          debug={true}
        />,
      );

      const loadMoreButton = screen.getByText("Load more");
      fireEvent.click(loadMoreButton);

      // Button should be disabled and show loading state
      expect(loadMoreButton).toBeDisabled();
      expect(screen.getByText("Loading…")).toBeInTheDocument();

      // Second click should not trigger another request
      fireEvent.click(loadMoreButton);
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it("handles items with price and marketCap", () => {
      const itemsWithPrice: ParentItem[] = [
        {
          parent: "Bitcoin",
          matches: 10,
          price: 50000,
          marketCap: 1000000000000,
        },
      ];

      render(
        <ParentsList
          narrative="crypto"
          initial={{ items: itemsWithPrice, nextCursor: null }}
          debug={false}
        />,
      );

      expect(screen.getByText("$50000.00")).toBeInTheDocument();
      expect(screen.getByText("$1.0T")).toBeInTheDocument();
    });

    it("handles items with only price", () => {
      const itemsWithPriceOnly: ParentItem[] = [
        {
          parent: "Bitcoin",
          matches: 10,
          price: 0.001,
        },
      ];

      render(
        <ParentsList
          narrative="crypto"
          initial={{ items: itemsWithPriceOnly, nextCursor: null }}
          debug={false}
        />,
      );

      expect(screen.getByText("$1.00e-3")).toBeInTheDocument();
    });

    it("handles items with only marketCap", () => {
      const itemsWithMarketCapOnly: ParentItem[] = [
        {
          parent: "Bitcoin",
          matches: 10,
          marketCap: 5000000,
        },
      ];

      render(
        <ParentsList
          narrative="crypto"
          initial={{ items: itemsWithMarketCapOnly, nextCursor: null }}
          debug={false}
        />,
      );

      expect(screen.getByText("$5.0M")).toBeInTheDocument();
    });

    it("handles items with URL", () => {
      const itemsWithUrl: ParentItem[] = [
        {
          parent: "Bitcoin",
          matches: 10,
          url: "https://example.com",
        },
      ];

      render(
        <ParentsList
          narrative="crypto"
          initial={{ items: itemsWithUrl, nextCursor: null }}
          debug={false}
        />,
      );

      const link = screen.getByRole("link");
      expect(link).toHaveAttribute("href", "https://example.com");
      expect(link).toHaveAttribute("target", "_blank");
      expect(link).toHaveAttribute("rel", "noopener noreferrer");
    });

    it("handles items with symbol", () => {
      const itemsWithSymbol: ParentItem[] = [
        {
          parent: "Bitcoin",
          matches: 10,
          symbol: "BTC",
        },
      ];

      render(
        <ParentsList
          narrative="crypto"
          initial={{ items: itemsWithSymbol, nextCursor: null }}
          debug={false}
        />,
      );

      expect(screen.getByText("BTC")).toBeInTheDocument();
    });

    it("handles items with score", () => {
      const itemsWithScore: ParentItem[] = [
        {
          parent: "Bitcoin",
          matches: 10,
          score: 0.95,
        },
      ];

      render(
        <ParentsList
          narrative="crypto"
          initial={{ items: itemsWithScore, nextCursor: null }}
          debug={false}
        />,
      );

      expect(screen.getByText("Score: 0.9500")).toBeInTheDocument();
    });

    it("handles mouse hover events on links", () => {
      const itemsWithUrl: ParentItem[] = [
        {
          parent: "Bitcoin",
          matches: 10,
          url: "https://example.com",
        },
      ];

      render(
        <ParentsList
          narrative="crypto"
          initial={{ items: itemsWithUrl, nextCursor: null }}
          debug={false}
        />,
      );

      const link = screen.getByRole("link");

      // Test mouse enter
      fireEvent.mouseEnter(link);
      expect(link).toHaveStyle("text-decoration: underline");

      // Test mouse leave
      fireEvent.mouseLeave(link);
      expect(link).toHaveStyle("text-decoration: none");
    });

    it("handles different price formatting ranges", () => {
      const itemsWithDifferentPrices: ParentItem[] = [
        {
          parent: "High Price",
          matches: 10,
          price: 1000, // >= 1
        },
        {
          parent: "Medium Price",
          matches: 10,
          price: 0.1, // >= 0.01
        },
        {
          parent: "Low Price",
          matches: 10,
          price: 0.001, // < 0.01
        },
      ];

      render(
        <ParentsList
          narrative="crypto"
          initial={{ items: itemsWithDifferentPrices, nextCursor: null }}
          debug={false}
        />,
      );

      expect(screen.getByText("$1000.00")).toBeInTheDocument();
      expect(screen.getByText("$0.1000")).toBeInTheDocument();
      expect(screen.getByText("$1.00e-3")).toBeInTheDocument();
    });

    it("handles different market cap formatting ranges", () => {
      const itemsWithDifferentMarketCaps: ParentItem[] = [
        {
          parent: "Trillion",
          matches: 10,
          marketCap: 2000000000000, // >= 1e12
        },
        {
          parent: "Billion",
          matches: 10,
          marketCap: 5000000000, // >= 1e9
        },
        {
          parent: "Million",
          matches: 10,
          marketCap: 75000000, // >= 1e6
        },
        {
          parent: "Thousand",
          matches: 10,
          marketCap: 50000, // >= 1e3
        },
        {
          parent: "Small",
          matches: 10,
          marketCap: 500, // < 1e3
        },
      ];

      render(
        <ParentsList
          narrative="crypto"
          initial={{ items: itemsWithDifferentMarketCaps, nextCursor: null }}
          debug={false}
        />,
      );

      expect(screen.getByText("$2.0T")).toBeInTheDocument();
      expect(screen.getByText("$5.0B")).toBeInTheDocument();
      expect(screen.getByText("$75.0M")).toBeInTheDocument();
      expect(screen.getByText("$50.0K")).toBeInTheDocument();
      expect(screen.getByText("$500")).toBeInTheDocument();
    });

    it("handles items with null/undefined price and marketCap", () => {
      const itemsWithNullValues: ParentItem[] = [
        {
          parent: "Bitcoin",
          matches: 10,
          price: null,
          marketCap: undefined,
        },
      ];

      render(
        <ParentsList
          narrative="crypto"
          initial={{ items: itemsWithNullValues, nextCursor: null }}
          debug={false}
        />,
      );

      // Should not show price/marketCap section
      expect(screen.queryByText("$")).not.toBeInTheDocument();
    });
  });
});
