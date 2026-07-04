import { notFound } from "next/navigation";

export const API_REVALIDATE_SECONDS = 604800;

export function backendUrl() {
  return (
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    "http://localhost:8001"
  ).replace(/\/$/, "");
}

export async function fetchCompanyForSeo(identifier: string) {
  const res = await fetch(`${backendUrl()}/api/v1/companies/${encodeURIComponent(identifier)}`, {
    next: { revalidate: API_REVALIDATE_SECONDS },
  });
  if (res.status === 404) {
    notFound();
  }
  if (!res.ok) {
    throw new Error(`Failed to load company ${identifier}`);
  }
  return res.json();
}

export function companyDescription(company: Record<string, any>) {
  const bits = [
    company.name,
    company.city,
    company.sector,
    company.status,
  ].filter(Boolean);
  return `${bits.join(" · ")}. View registration details, capital, directors, filings, and related companies on CorpIntel India.`;
}

export function organizationJsonLd(company: Record<string, any>) {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: company.name,
    identifier: company.cin || company.llpin || company.identifier,
    address: company.registered_office_address || company.address,
    foundingDate: company.date_of_incorporation,
    legalName: company.name,
    taxID: company.gstin,
    url: `${process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"}/company/${company.cin || company.llpin || company.identifier}`,
  };
}
