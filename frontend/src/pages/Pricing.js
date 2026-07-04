import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Check, X, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { createCheckout, verifyRazorpayPayment } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const TIERS = [
  { id: "free", name: "Free", price: "₹0", period: "/mo", cta: "Start free", features: ["20 searches/day", "View company profiles", "Basic analytics", "No exports", "No contact data"] },
  { id: "starter", name: "Starter", price: "₹999", period: "/mo", cta: "Upgrade to Starter", features: ["Unlimited search", "50 exports/month", "Email alerts", "Full analytics", "No contact data"] },
  { id: "pro", name: "Pro", price: "₹2,499", period: "/mo", highlight: true, cta: "Upgrade to Pro", features: ["Everything in Starter", "Unlimited exports", "Contact data (GSTIN, phone, email)", "API access", "Slack alerts"] },
  { id: "enterprise", name: "Enterprise", price: "Custom", period: "", cta: "Contact sales", features: ["Everything in Pro", "White-label", "Bulk API", "Dedicated support", "Custom data feeds"] },
];

const COMPARE = [
  ["Searches per day", "20", "Unlimited", "Unlimited", "Unlimited"],
  ["Exports per month", "0", "50", "Unlimited", "Unlimited"],
  ["Contact data", false, false, true, true],
  ["API access", false, false, true, true],
  ["Email alerts", false, true, true, true],
  ["White-label", false, false, false, true],
];

const FAQ = [
  { q: "Where does the data come from?", a: "We aggregate open Government of India company master data (data.gov.in / MCA) and enrich it with AI sector classification. Live ingestion activates when a data.gov.in API key is configured." },
  { q: "Can I cancel anytime?", a: "Yes. Subscriptions are month-to-month and you can manage or cancel them anytime from Settings." },
  { q: "What is contact data?", a: "Pro plans unlock GSTIN, phone, email, website and LinkedIn for companies where available." },
  { q: "Do you cover cities beyond Mumbai?", a: "We focus on the Mumbai Metropolitan Region (Mumbai, Navi Mumbai, Thane) and are expanding to more Indian cities." },
];

export default function Pricing() {
  const { user, refresh } = useAuth();
  const navigate = useNavigate();
  const [busy, setBusy] = useState("");

  const upgrade = async (tier) => {
    if (tier === "free") { navigate("/dashboard"); return; }
    if (tier === "enterprise") { toast.info("Our team will reach out — contact sales@corpintel.in"); return; }
    if (!user) { toast.error("Please sign in to upgrade"); navigate("/login"); return; }
    setBusy(tier);
    try {
      const res = await createCheckout(tier);
      await openRazorpayCheckout(res);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not start checkout");
    } finally { setBusy(""); }
  };

  const loadRazorpay = () =>
    new Promise((resolve, reject) => {
      if (window.Razorpay) { resolve(); return; }
      const existing = document.querySelector("script[data-razorpay-checkout]");
      if (existing) {
        existing.addEventListener("load", resolve, { once: true });
        existing.addEventListener("error", reject, { once: true });
        return;
      }
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.async = true;
      script.dataset.razorpayCheckout = "true";
      script.onload = resolve;
      script.onerror = reject;
      document.body.appendChild(script);
    });

  const openRazorpayCheckout = async (order) => {
    await loadRazorpay();
    const options = {
      key: order.key_id,
      amount: order.amount_paise,
      currency: order.currency,
      name: "CorpIntel India",
      description: order.description,
      order_id: order.order_id,
      prefill: order.prefill || {},
      theme: { color: "#F4A620" },
      handler: async (response) => {
        try {
          await verifyRazorpayPayment(response);
          await refresh();
          toast.success("Payment verified. Your plan has been upgraded.");
          navigate("/settings");
        } catch (err) {
          toast.error(err?.response?.data?.detail || "Payment verification failed");
        }
      },
      modal: {
        ondismiss: () => toast.info("Payment cancelled"),
      },
    };
    const checkout = new window.Razorpay(options);
    checkout.open();
  };

  const cell = (v) => v === true ? <Check className="h-4 w-4 text-success mx-auto" /> : v === false ? <X className="h-4 w-4 text-muted-foreground mx-auto" /> : <span className="tabular-nums">{v}</span>;

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="font-heading text-3xl font-bold">Simple, transparent pricing</h1>
        <p className="mt-2 text-muted-foreground">Start free. Upgrade when you need exports, contact data and API access.</p>
      </div>

      <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-5">
        {TIERS.map((t) => (
          <Card key={t.id} className={`p-6 flex flex-col ${t.highlight ? "border-accent ring-1 ring-accent/40" : ""}`} data-testid={`pricing-tier-${t.id}`}>
            {t.highlight && <Badge className="bg-accent text-accent-foreground w-fit mb-2"><Sparkles className="h-3 w-3 mr-1" /> Most popular</Badge>}
            <div className="font-heading font-semibold text-lg">{t.name}</div>
            <div className="mt-2 font-heading text-3xl font-bold">{t.price}<span className="text-sm font-normal text-muted-foreground">{t.period}</span></div>
            <ul className="mt-4 space-y-2 flex-1">
              {t.features.map((f) => (
                <li key={f} className="flex items-start gap-2 text-sm"><Check className="h-4 w-4 text-success mt-0.5 shrink-0" /> {f}</li>
              ))}
            </ul>
            <Button
              className={`mt-6 w-full ${t.highlight ? "bg-accent text-accent-foreground hover:brightness-95" : ""}`}
              variant={t.highlight ? "default" : "outline"}
              onClick={() => upgrade(t.id)}
              disabled={busy === t.id || user?.plan === t.id}
              data-testid={`pricing-upgrade-${t.id}`}
            >
              {busy === t.id ? <Loader2 className="h-4 w-4 animate-spin" /> : user?.plan === t.id ? "Current plan" : t.cta}
            </Button>
          </Card>
        ))}
      </div>

      <Card className="p-2 sm:p-4" data-testid="pricing-compare-table">
        <h3 className="font-heading font-semibold p-2">Compare plans</h3>
        <Table>
          <TableHeader><TableRow><TableHead>Feature</TableHead><TableHead className="text-center">Free</TableHead><TableHead className="text-center">Starter</TableHead><TableHead className="text-center">Pro</TableHead><TableHead className="text-center">Enterprise</TableHead></TableRow></TableHeader>
          <TableBody>
            {COMPARE.map((row, i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">{row[0]}</TableCell>
                <TableCell className="text-center">{cell(row[1])}</TableCell>
                <TableCell className="text-center">{cell(row[2])}</TableCell>
                <TableCell className="text-center">{cell(row[3])}</TableCell>
                <TableCell className="text-center">{cell(row[4])}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      <div className="max-w-2xl mx-auto w-full">
        <h3 className="font-heading font-semibold mb-2 text-center">Frequently asked questions</h3>
        <Accordion type="single" collapsible>
          {FAQ.map((f, i) => (
            <AccordionItem key={i} value={`faq-${i}`}>
              <AccordionTrigger className="text-sm text-left">{f.q}</AccordionTrigger>
              <AccordionContent className="text-sm text-muted-foreground">{f.a}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </div>
  );
}
