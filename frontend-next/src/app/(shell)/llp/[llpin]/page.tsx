import type { Metadata } from "next";
import CompanyDetail from "@/views/CompanyDetail";
import { companyDescription, fetchCompanyForSeo, organizationJsonLd } from "@/lib/server-api";

export const revalidate = 604800;

type LlpPageProps = {
  params: Promise<{ llpin: string }>;
};

export async function generateMetadata({ params }: LlpPageProps): Promise<Metadata> {
  const { llpin } = await params;
  const company = await fetchCompanyForSeo(llpin);
  const title = `${company.name || llpin} LLP Profile`;
  const description = companyDescription(company);

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      type: "profile",
    },
  };
}

export default async function LlpPage({ params }: LlpPageProps) {
  const { llpin } = await params;
  const company = await fetchCompanyForSeo(llpin);
  const jsonLd = organizationJsonLd(company);

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <section className="sr-only" aria-label="LLP profile summary">
        <h1>{company.name}</h1>
        <p>{companyDescription(company)}</p>
      </section>
      <CompanyDetail />
    </>
  );
}
