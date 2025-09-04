// frontend/src/app/n/[narrative]/page.tsx
import { getParents } from "@/lib/api";
import ParentsList from "./_components/ParentsList";

export default async function NarrativePage({
  params,
}: {
  params: Promise<{ narrative: string }>;
}) {
  const { narrative } = await params;
  const initial = await getParents(narrative, { limit: 25 });
  return (
    <div style={{ padding: "20px" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
        }}
      >
        <h1 style={{ fontSize: 24, margin: 0 }}>{narrative}</h1>
      </div>
      <ParentsList narrative={narrative} initial={initial} />
    </div>
  );
}
