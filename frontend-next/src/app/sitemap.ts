import type { MetadataRoute } from "next";

const staticRoutes = [
  "",
  "/search",
  "/dashboard",
  "/analytics",
  "/pricing",
  "/city/mumbai",
  "/city/navi-mumbai",
  "/city/thane",
  "/sector/technology",
  "/sector/finance",
  "/sector/manufacturing",
  "/sector/healthcare",
  "/sector/real-estate",
  "/sector/logistics",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
  return staticRoutes.map((route) => ({
    url: `${siteUrl}${route}`,
    lastModified: new Date(),
    changeFrequency: route === "" || route === "/search" ? "daily" : "weekly",
    priority: route === "" ? 1 : 0.7,
  }));
}
