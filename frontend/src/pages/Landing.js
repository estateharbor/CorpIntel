import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Building2, Search, BarChart3, Bell, Download, ArrowRight, ShieldCheck, Zap, MapPin, CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { getHealth, getSummary } from "@/lib/api";
import { formatNumber } from "@/lib/format";

const HERO_IMG = "https://images.unsplash.com/photo-1578993074370-5865598d5b1e?crop=entropy&cs=srgb&fm=jpg&q=85&w=1200";

const FEATURES = [
  { icon: Search, title: "Powerful Search", desc: "Filter MMR companies by city, sector, status, capital and incorporation date in milliseconds." },
  { icon: BarChart3, title: "Live Analytics", desc: "Registration trends, sector mix, capital distribution and area-wise density heatmaps." },
  { icon: Bell, title: "Smart Alerts", desc: "Get notified when new companies register in your target city + sector." },
  { icon: Download, title: "Export Anywhere", desc: "Download intelligence as CSV, formatted Excel (sheet per city) or PDF reports." },
];

const TIERS = [
  { name: "Free", price: "₹0", note: "20 searches/day, view only" },
  { name: "Starter", price: "₹999", note: "Unlimited search, 50 exports/mo", highlight: false },
  { name: "Pro", price: "₹2,499", note: "Everything + contact data + API", highlight: true },
];

export default function Landing() {
  const { data: health } = useQuery({ queryKey: ["health"], queryFn: getHealth });
  const { data: summary } = useQuery({ queryKey: ["summary-landing"], queryFn: () => getSummary("All") });
  const total = health?.companies ?? summary?.total ?? 0;

  return (
    <div className="min-h-screen bg-background">
      {/* Nav */}
      <header className="flex items-center justify-between gap-2 px-3 mb:px-4 sm:px-8 h-16 border-b">
        <div className="flex min-w-0 items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Building2 className="h-5 w-5" />
          </div>
          <span className="truncate font-heading font-bold text-base mb:text-lg">CorpIntel India</span>
        </div>
        <div className="flex shrink-0 items-center gap-1 mb:gap-2">
          <ThemeToggle />
          <Button variant="ghost" asChild className="hidden sm:inline-flex"><Link to="/pricing">Pricing</Link></Button>
          <Button variant="ghost" asChild className="hidden mb:inline-flex px-2 mb:px-3"><Link to="/login" data-testid="landing-signin">Sign in</Link></Button>
          <Button asChild className="bg-accent text-accent-foreground hover:brightness-95 px-2 mb:px-3">
            <Link to="/dashboard" data-testid="landing-launch-app">Launch app</Link>
          </Button>
        </div>
      </header>

      {/* Hero */}
      <section className="px-4 sm:px-8 py-12 lg:py-20">
        <div className="mx-auto max-w-[1200px] grid lg:grid-cols-2 gap-10 items-center">
          <div>
            <Badge className="bg-accent/15 text-accent-foreground border border-accent/30 mb-4">
              <MapPin className="h-3.5 w-3.5 mr-1 text-accent" /> Mumbai · Navi Mumbai · Thane
            </Badge>
            <h1 className="font-heading text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.05]">
              India's Most Complete <span className="text-accent">Company Intelligence</span> Platform
            </h1>
            <p className="mt-5 text-base md:text-lg text-muted-foreground max-w-xl">
              Discover, analyze, and track companies across the Mumbai Metropolitan Region — powered by live MCA-grade data, AI sector classification, and real-time alerts.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Button asChild size="lg" className="bg-accent text-accent-foreground hover:brightness-95" data-testid="landing-hero-primary-cta">
                <Link to="/dashboard">Start Free — No Credit Card <ArrowRight className="ml-2 h-4 w-4" /></Link>
              </Button>
              <Button asChild size="lg" variant="outline"><Link to="/search">Explore companies</Link></Button>
            </div>
            <div className="mt-6 flex items-center gap-4 text-sm text-muted-foreground">
              <span className="flex items-center gap-1.5"><ShieldCheck className="h-4 w-4 text-success" /> Trusted data</span>
              <span className="flex items-center gap-1.5"><Zap className="h-4 w-4 text-accent" /> Instant search</span>
            </div>
          </div>
          <div className="relative">
            <div className="overflow-hidden rounded-2xl border shadow-soft">
              <img src={HERO_IMG} alt="Mumbai skyline" className="h-[340px] w-full object-cover" />
            </div>
            <Card data-testid="landing-live-counter" className="absolute -bottom-6 left-6 right-6 p-4 shadow-med">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-muted-foreground">Companies tracked</div>
                  <div className="font-heading text-3xl font-bold tabular-nums">{formatNumber(total)}</div>
                </div>
                <Badge className="bg-success/15 text-success border border-success/30">
                  <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Updated today
                </Badge>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="px-4 sm:px-8 py-16 mt-6">
        <div className="mx-auto max-w-[1200px]">
          <h2 className="font-heading text-2xl sm:text-3xl font-bold text-center">Everything you need to win in the MMR market</h2>
          <div data-testid="landing-feature-grid" className="mt-10 grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {FEATURES.map((f) => {
              const Icon = f.icon;
              return (
                <Card key={f.title} className="p-5 hover:shadow-soft hover:border-accent/40 transition-shadow transition-colors">
                  <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary/10 text-primary dark:bg-white/5 dark:text-foreground">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="mt-4 font-heading font-semibold">{f.title}</h3>
                  <p className="mt-1.5 text-sm text-muted-foreground">{f.desc}</p>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Pricing preview */}
      <section className="px-4 sm:px-8 py-12">
        <div data-testid="landing-pricing-preview" className="mx-auto max-w-[1000px] grid sm:grid-cols-3 gap-5">
          {TIERS.map((t) => (
            <Card key={t.name} className={`p-6 ${t.highlight ? "border-accent ring-1 ring-accent/40" : ""}`}>
              {t.highlight && <Badge className="bg-accent text-accent-foreground mb-2">Most popular</Badge>}
              <div className="font-heading font-semibold">{t.name}</div>
              <div className="mt-2 font-heading text-3xl font-bold">{t.price}<span className="text-sm text-muted-foreground font-normal">/mo</span></div>
              <p className="mt-2 text-sm text-muted-foreground">{t.note}</p>
            </Card>
          ))}
        </div>
        <div className="text-center mt-6">
          <Button asChild variant="outline"><Link to="/pricing">See full pricing</Link></Button>
        </div>
      </section>

      {/* CTA band */}
      <section className="px-4 sm:px-8 py-14">
        <div className="mx-auto max-w-[1100px] rounded-2xl bg-primary text-primary-foreground p-10 text-center">
          <h2 className="font-heading text-2xl sm:text-3xl font-bold">Start exploring company intelligence today</h2>
          <p className="mt-3 text-primary-foreground/80">Free to start. Upgrade anytime for exports, contact data and API access.</p>
          <Button asChild size="lg" className="mt-6 bg-accent text-accent-foreground hover:brightness-95">
            <Link to="/dashboard">Launch the platform <ArrowRight className="ml-2 h-4 w-4" /></Link>
          </Button>
        </div>
      </section>

      <footer className="border-t px-4 sm:px-8 py-8 text-center text-sm text-muted-foreground">
        © {new Date().getFullYear()} CorpIntel India · Built for Mumbai, Navi Mumbai & Thane.
      </footer>
    </div>
  );
}
