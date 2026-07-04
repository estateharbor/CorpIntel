"use client";

import React, { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, Trash2, Plus, Inbox } from "lucide-react";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { listAlerts, createAlert, deleteAlert, toggleAlert, getSectors } from "@/lib/api";
import { CITIES, formatINR } from "@/lib/format";

function Chip({ active, onClick, children, testid }) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={testid}
      className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${active ? "bg-accent text-accent-foreground border-accent" : "bg-background hover:bg-muted"}`}
    >
      {children}
    </button>
  );
}

export default function Alerts() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["alerts"], queryFn: listAlerts });
  const { data: sectorsData } = useQuery({ queryKey: ["sectors-alerts"], queryFn: () => getSectors("All", 20) });
  const sectorOptions = (sectorsData?.sectors || []).map((s) => s.sector).filter(Boolean);

  const [name, setName] = useState("");
  const [cities, setCities] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [minCapital, setMinCapital] = useState("");
  const [frequency, setFrequency] = useState("weekly");
  const [saving, setSaving] = useState(false);

  const toggle = (arr, setArr, v) => setArr(arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v]);

  const submit = async (e) => {
    e.preventDefault();
    if (!name.trim()) { toast.error("Give your alert a name"); return; }
    setSaving(true);
    try {
      await createAlert({ name, cities, sectors, min_capital: minCapital ? Number(minCapital) : null, frequency });
      toast.success("Alert created");
      setName(""); setCities([]); setSectors([]); setMinCapital("");
      qc.invalidateQueries({ queryKey: ["alerts"] });
    } catch (err) { toast.error("Could not create alert"); } finally { setSaving(false); }
  };

  const remove = async (id) => { await deleteAlert(id); toast.success("Alert deleted"); qc.invalidateQueries({ queryKey: ["alerts"] }); };
  const flip = async (id) => { await toggleAlert(id); qc.invalidateQueries({ queryKey: ["alerts"] }); };

  const alerts = data?.alerts || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-2xl font-bold">Alerts</h1>
        <p className="text-sm text-muted-foreground">Get notified when new companies register in your target market</p>
      </div>

      <div className="grid lg:grid-cols-5 gap-6">
        <Card className="p-6 lg:col-span-2" data-testid="alerts-create-form">
          <h3 className="font-heading font-semibold mb-4 flex items-center gap-2"><Plus className="h-4 w-4 text-accent" /> Create alert</h3>
          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-1.5">
              <Label>Alert name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. New FinTech in Navi Mumbai" data-testid="alerts-name-input" />
            </div>
            <div className="space-y-2">
              <Label>Cities</Label>
              <div className="flex flex-wrap gap-2">
                {CITIES.map((c) => <Chip key={c} active={cities.includes(c)} onClick={() => toggle(cities, setCities, c)} testid={`alerts-city-${c.replace(/\s/g, '-').toLowerCase()}`}>{c}</Chip>)}
              </div>
            </div>
            <div className="space-y-2">
              <Label>Sectors</Label>
              <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto thin-scroll">
                {sectorOptions.map((s) => <Chip key={s} active={sectors.includes(s)} onClick={() => toggle(sectors, setSectors, s)}>{s}</Chip>)}
              </div>
            </div>
            <div className="grid grid-cols-1 xs:grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Min paid-up capital (₹)</Label>
                <Input type="number" value={minCapital} onChange={(e) => setMinCapital(e.target.value)} placeholder="0" />
              </div>
              <div className="space-y-1.5">
                <Label>Frequency</Label>
                <Select value={frequency} onValueChange={setFrequency}>
                  <SelectTrigger data-testid="alerts-frequency-select"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="daily">Daily</SelectItem>
                    <SelectItem value="weekly">Weekly</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Button type="submit" className="w-full" disabled={saving} data-testid="alerts-submit-button">Create alert</Button>
          </form>
        </Card>

        <Card className="p-6 lg:col-span-3" data-testid="alerts-table">
          <h3 className="font-heading font-semibold mb-4 flex items-center gap-2"><Bell className="h-4 w-4 text-accent" /> My alerts</h3>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : alerts.length === 0 ? (
            <div className="text-center py-10">
              <Inbox className="mx-auto h-10 w-10 text-muted-foreground" />
              <p className="mt-2 text-sm text-muted-foreground">No alerts yet. Create your first alert to start tracking new companies.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {alerts.map((a) => (
                <div key={a.id} className="flex flex-col items-start gap-3 rounded-lg border p-3 xs:flex-row xs:items-center">
                  <div className="min-w-0 flex-1">
                    <div className="font-medium truncate">{a.name}</div>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {(a.cities || []).map((c) => <Badge key={c} variant="secondary" className="text-[10px]">{c}</Badge>)}
                      {(a.sectors || []).map((s) => <Badge key={s} variant="outline" className="text-[10px]">{s}</Badge>)}
                      {a.min_capital ? <Badge variant="outline" className="text-[10px]">{formatINR(a.min_capital)}+</Badge> : null}
                      <Badge className="text-[10px] bg-primary/10 text-primary dark:bg-white/5 dark:text-foreground capitalize">{a.frequency}</Badge>
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">{a.match_count || 0} matches tracked</div>
                  </div>
                  <div className="flex w-full items-center justify-end gap-2 xs:w-auto">
                    <Switch checked={a.active !== false} onCheckedChange={() => flip(a.id)} data-testid={`alert-toggle-${a.id}`} />
                    <Button variant="ghost" size="icon" onClick={() => remove(a.id)} data-testid={`alert-delete-${a.id}`}><Trash2 className="h-4 w-4 text-destructive" /></Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
