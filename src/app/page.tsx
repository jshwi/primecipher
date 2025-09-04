import HomeClient from "@/components/HomeClient";

interface PageProps {
  searchParams: { view?: string };
}

export default async function Page({ searchParams }: PageProps) {
  // Default to heatmap view, but allow searchParams.view to override
  // The client component will handle localStorage override
  const initialView: "heatmap" | "narratives" =
    searchParams.view === "narratives" ? "narratives" : "heatmap";

  return <HomeClient initialView={initialView} />;
}
