// frontend/src/app/n/[narrative]/page.tsx
import { getParents } from "@/lib/api";
import ParentsClient from "./ParentsClient";

export default async function NarrativePage({
  params,
}: {
  params: Promise<{ narrative: string }>;
}) {
  const { narrative } = await params;
  const initial = await getParents(narrative, { limit: 25 });
  return <ParentsClient initial={initial} />;
}
