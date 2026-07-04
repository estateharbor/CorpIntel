import type { Metadata } from "next";
import Link from "next/link";

const SECTORS: Record<string, string> = {
  technology: "Technology",
  finance: "Finance",
  manufacturing: "Manufacturing",
  healthcare: "Healthcare",
  "real-estate": "Real Estate",
  logistics: "Logistics",
};

type SectorPageProps = {
  params: Promise<{ slug: string }>;
};

export function generateStaticParams() {
  return Object.keys(SECTORS).map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: SectorPageProps): Promise<Metadata> {
  const { slug } = await params;
  const sector = SECTORS[slug] || "Sector";
  return {
    title: `${sector} Companies in MMR`,
    description: `Discover ${sector.toLowerCase()} companies across Mumbai, Navi Mumbai, and Thane with CorpIntel India.`,
  };
}

export default async function SectorLandingPage({ params }: SectorPageProps) {
  const { slug } = await params;
  const sector = SECTORS[slug] || "Sector";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-bold">{sector} Companies in MMR</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Track companies, LLPs, capital patterns, and incorporation activity in the {sector.toLowerCase()} sector.
        </p>
      </div>
      <div className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
        <p className="text-sm text-muted-foreground">
          Jump into the searchable directory to refine by city, status, entity type, date range, and capital.
        </p>
        <Link
          href={`/search?sector=${encodeURIComponent(sector)}`}
          className="mt-4 inline-flex rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground"
        >
          Search {sector}
        </Link>
      </div>
    </div>
  );
}
