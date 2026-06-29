import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Copy, RefreshCw, Eye, EyeOff, KeyRound, CreditCard, Bookmark, Bell, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { listSaved, listAlerts, regenerateApiKey, checkoutStatus } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { formatNumber } from "@/lib/format";

const EXPORT_LIMITS = { free: 0, starter: 50, pro: -1, enterprise: -1 };

export default function Settings() {
  const { user, refresh } = useAuth();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const [revealKey, setRevealKey] = useState(false);
  const [apiKey, setApiKey] = useState(user?.api_key || "");
  const [regen, setRegen] = useState(false);
  const [verifying, setVerifying] = useState(false);

  const { data: saved } = useQuery({ queryKey: ["saved"], queryFn: listSaved });
  const { data: alerts } = useQuery({ queryKey: ["alerts-settings"], queryFn: listAlerts });

  // Handle Stripe checkout return
  useEffect(() => {
    const sessionId = params.get("session_id");
    if (!sessionId) return;
    let attempts = 0;
    setVerifying(true);
    const poll = async () => {
      try {
        const res = await checkoutStatus(sessionId);
        if (res.payment_status === "paid") {
          await refresh();
          toast.success("Payment successful — your plan has been upgraded!");
          setVerifying(false);
          setParams({}, { replace: true });
          return;
        }
        if (res.status === "expired") { toast.error("Payment session expired"); setVerifying(false); setParams({}, { replace: true }); return; }
      } catch (e) { /* ignore */ }
      attempts += 1;
      if (attempts < 6) setTimeout(poll, 2000);
      else { setVerifying(false); setParams({}, { replace: true }); }
    };
    poll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const copyKey = () => { navigator.clipboard.writeText(apiKey || ""); toast.success("API key copied"); };
  const doRegen = async () => {
    setRegen(true);
    try { const r = await regenerateApiKey(); setApiKey(r.api_key); toast.success("API key regenerated"); }
    catch (e) { toast.error(e?.response?.data?.detail || "Could not regenerate key"); }
    finally { setRegen(false); }
  };

  const limit = EXPORT_LIMITS[user?.plan || "free"];
  const used = user?.exports_used || 0;
  const unlimited = limit === -1;
  const isPro = ["pro", "enterprise"].includes(user?.plan);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold">Settings</h1>
        <p className="text-sm text-muted-foreground">Manage your account, plan and integrations</p>
      </div>

      {verifying && (
        <Card className="p-4 flex items-center gap-2 border-accent/40">
          <Loader2 className="h-4 w-4 animate-spin text-accent" /> Verifying your payment…
        </Card>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        <Card className="p-6" data-testid="settings-account-card">
          <h3 className="font-heading font-semibold mb-4">Account</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between"><span className="text-muted-foreground">Name</span><span className="font-medium">{user?.name}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Email</span><span className="font-medium">{user?.email}</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Sign-in method</span><span className="font-medium capitalize">{user?.auth_provider}</span></div>
          </div>
        </Card>

        <Card className="p-6" data-testid="settings-plan-status">
          <h3 className="font-heading font-semibold mb-4 flex items-center gap-2"><CreditCard className="h-4 w-4 text-accent" /> Plan & usage</h3>
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-muted-foreground">Current plan</span>
            <Badge className="bg-accent text-accent-foreground capitalize">{user?.plan}</Badge>
          </div>
          <div className="space-y-1">
            <div className="flex justify-between text-sm"><span className="text-muted-foreground">Exports this month</span><span className="tabular-nums">{unlimited ? `${used} · ∞` : `${used}/${limit}`}</span></div>
            <Progress value={unlimited ? 100 : limit === 0 ? 0 : Math.min(100, (used / limit) * 100)} />
          </div>
          <div className="flex justify-between text-sm mt-3"><span className="text-muted-foreground">Searches today</span><span className="tabular-nums">{formatNumber(user?.searches_used || 0)}</span></div>
          <Button className="mt-4 w-full bg-accent text-accent-foreground hover:brightness-95" onClick={() => navigate("/pricing")} data-testid="settings-upgrade-button">
            {isPro ? "Manage plan" : "Upgrade plan"}
          </Button>
        </Card>
      </div>

      {/* API key */}
      <Card className="p-6">
        <h3 className="font-heading font-semibold mb-4 flex items-center gap-2"><KeyRound className="h-4 w-4 text-accent" /> API access</h3>
        {isPro ? (
          <div className="flex items-center gap-2 flex-wrap">
            <Input readOnly value={revealKey ? (apiKey || "—") : "•".repeat(Math.min(32, (apiKey || "").length || 24))} className="font-mono text-xs max-w-md" />
            <Button variant="outline" size="icon" onClick={() => setRevealKey((v) => !v)}>{revealKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}</Button>
            <Button variant="outline" size="icon" onClick={copyKey} data-testid="settings-api-key-copy-button"><Copy className="h-4 w-4" /></Button>
            <Button variant="outline" onClick={doRegen} disabled={regen} data-testid="settings-api-key-regen"><RefreshCw className={`h-4 w-4 mr-2 ${regen ? "animate-spin" : ""}`} /> Regenerate</Button>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">API access is available on the Pro plan. <button className="text-accent underline" onClick={() => navigate("/pricing")}>Upgrade to Pro</button>.</p>
        )}
      </Card>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="font-heading font-semibold mb-4 flex items-center gap-2"><Bookmark className="h-4 w-4 text-accent" /> Saved searches</h3>
          {(saved?.saved_searches || []).length === 0 ? (
            <p className="text-sm text-muted-foreground">No saved searches yet.</p>
          ) : (
            <div className="space-y-2">
              {saved.saved_searches.map((s) => (
                <div key={s.id} className="flex items-center justify-between rounded-lg border p-3 text-sm">
                  <span className="font-medium truncate">{s.name}</span>
                  <Button variant="ghost" size="sm" onClick={() => navigate("/search")}>Open</Button>
                </div>
              ))}
            </div>
          )}
        </Card>
        <Card className="p-6">
          <h3 className="font-heading font-semibold mb-4 flex items-center gap-2"><Bell className="h-4 w-4 text-accent" /> Alerts</h3>
          {(alerts?.alerts || []).length === 0 ? (
            <p className="text-sm text-muted-foreground">No alerts. <button className="text-accent underline" onClick={() => navigate("/alerts")}>Create one</button>.</p>
          ) : (
            <div className="space-y-2">
              {alerts.alerts.map((a) => (
                <div key={a.id} className="flex items-center justify-between rounded-lg border p-3 text-sm">
                  <span className="font-medium truncate">{a.name}</span>
                  <Badge variant="secondary" className="capitalize">{a.frequency}</Badge>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
