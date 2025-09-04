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
    <main>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <h1 style={{ fontSize: 22, margin: "8px 0 12px" }}>{narrative}</h1>
      </div>
      <ParentsList narrative={narrative} initial={initial} />
    </main>
  );
}
