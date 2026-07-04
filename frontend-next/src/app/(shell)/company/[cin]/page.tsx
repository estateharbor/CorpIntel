import type { Metadata } from "next";
import CompanyDetail from "@/views/CompanyDetail";
import { companyDescription, fetchCompanyForSeo, organizationJsonLd } from "@/lib/server-api";

export const revalidate = 604800;

type CompanyPageProps = {
  params: Promise<{ cin: string }>;
};

export async function generateMetadata({ params }: CompanyPageProps): Promise<Metadata> {
  const { cin } = await params;
  const company = await fetchCompanyForSeo(cin);
  const title = `${company.name || cin} Company Profile`;
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

export default async function CompanyPage({ params }: CompanyPageProps) {
  const { cin } = await params;
  const company = await fetchCompanyForSeo(cin);
  const jsonLd = organizationJsonLd(company);

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <section className="sr-only" aria-label="Company profile summary">
        <h1>{company.name}</h1>
        <p>{companyDescription(company)}</p>
      </section>
      <CompanyDetail />
    </>
  );
}
