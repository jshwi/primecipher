import { NextRequest, NextResponse } from "next/server";
import { API_BASE, REFRESH_TOKEN } from "@/lib/config";

export async function POST(request: NextRequest) {
  try {
    // Read query parameters with defaults
    const { searchParams } = new URL(request.url);
    const mode = searchParams.get("mode") ?? "dev";
    const window = searchParams.get("window") ?? "24h";

    // Build the backend URL
    const backendUrl = new URL(`${API_BASE}/refresh/async`);
    backendUrl.searchParams.set("mode", mode);
    backendUrl.searchParams.set("window", window);

    // Forward the request to the backend
    const response = await fetch(backendUrl.toString(), {
      method: "POST",
      headers: {
        Authorization: `Bearer ${REFRESH_TOKEN}`,
        "Content-Type": "application/json",
      },
    });

    // Get the response body
    const data = await response.json();

    // Return the backend response with the same status
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("Error proxying refresh request:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
