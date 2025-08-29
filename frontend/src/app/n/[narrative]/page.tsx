import { getParents } from "@/lib/api"
import ParentsClient from "./ParentsClient"

export default async function NarrativePage({ params }: { params: { narrative: string } }) {
  const initial = await getParents(params.narrative, { limit: 25 })
  return <ParentsClient initial={initial} />
}
