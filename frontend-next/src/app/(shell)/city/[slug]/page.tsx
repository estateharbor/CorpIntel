import type { Metadata } from "next";
import Link from "next/link";

const CITIES: Record<string, string> = {
  mumbai: "Mumbai",
  "navi-mumbai": "Navi Mumbai",
  thane: "Thane",
};

type CityPageProps = {
  params: Promise<{ slug: string }>;
};

export function generateStaticParams() {
  return Object.keys(CITIES).map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: CityPageProps): Promise<Metadata> {
  const { slug } = await params;
  const city = CITIES[slug] || "MMR";
  return {
    title: `${city} Company Directory`,
    description: `Search and analyze registered companies in ${city} with CorpIntel India.`,
  };
}

export default async function CityLandingPage({ params }: CityPageProps) {
  const { slug } = await params;
  const city = CITIES[slug] || "MMR";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-bold">{city} Company Directory</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          Explore incorporation trends, sectors, paid-up capital, and company profiles for {city}.
        </p>
      </div>
      <div className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
        <p className="text-sm text-muted-foreground">
          Use the live search experience to filter by status, entity type, sector, date range, and capital.
        </p>
        <Link
          href={`/search?city=${encodeURIComponent(city)}`}
          className="mt-4 inline-flex rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground"
        >
          Search {city}
        </Link>
      </div>
    </div>
  );
}
