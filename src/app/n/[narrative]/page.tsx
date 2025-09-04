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
        <div>
          <h1 style={{ fontSize: 24, margin: 0 }}>{narrative}</h1>
          <p
            style={{
              fontSize: 14,
              color: "var(--fg-muted)",
              margin: "8px 0 0 0",
            }}
          >
            {initial.items.length} parents loaded
          </p>
        </div>
      </div>
      <ParentsList narrative={narrative} initial={initial} />
    </div>
  );
}
