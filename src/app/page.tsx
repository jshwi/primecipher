import HomeClient from "@/components/HomeClient";

export default async function Page() {
  // Default to heatmap view, but the client component will handle localStorage override
  const initialView: "heatmap" | "narratives" = "heatmap";

  return <HomeClient initialView={initialView} />;
}
