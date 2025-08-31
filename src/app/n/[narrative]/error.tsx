"use client";

export default function NarrativeError({ error }: { error: Error }) {
  return (
    <div
      style={{
        background: "#fee",
        color: "#900",
        padding: 12,
        borderRadius: 8,
      }}
    >
      Failed to load narrative: {error.message}
    </div>
  );
}
