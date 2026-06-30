import React from "react";
import { useQuery } from "@tanstack/react-query";import {
  Database, ShieldCheck, Clock, Copy, Terminal, RefreshCw, AlertTriangle,
  CheckCircle2, Cookie, ListChecks, Activity, Ban, CircleSlash, Hourglass,
} from "lucide-react";
import { toast } from "sonner";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { KpiSkeleton, ChartSkeleton } from "@/components/Skeletons";
import { DataUploadCard } from "@/components/admin/DataUploadCard";
import { getEnrichmentProgress } from "@/lib/api";
import { formatNumber, formatDate } from "@/lib/format";
import { ADMIN_ENRICHMENT as T } from "@/constants/testIds";

const HARD_STOP_REASONS = new Set(["captcha", "session_expired", "consecutive_failures"]);

function stopReasonMeta(reason) {
  switch (reason) {
    case "captcha":
      return { label: "CAPTCHA detected", tone: "danger", icon: Ban };
    case "session_expired":
      return { label: "Session expired", tone: "danger", icon: CircleSlash };
    case "consecutive_failures":
      return { label: "Circuit breaker", tone: "danger", icon: AlertTriangle };
    case "time_budget_reached":
      return { label: "Time budget reached", tone: "info", icon: Hourglass };
    case "empty_queue":
      return { label: "Queue empty", tone: "success", icon: CheckCircle2 };
    case "batch_complete":
    case "completed":
      return { label: "Completed", tone: "success", icon: CheckCircle2 };
    case "running":
      return { label: "Running", tone: "info", icon: Activity };
    default:
      return { label: reason || "—", tone: "neutral", icon: Activity };
  }
}

const TONE_CLASSES = {
  success: "bg-[hsl(152_55%_95%)] text-[hsl(152_55%_26%)] dark:bg-[hsl(152_55%_18%)] dark:text-[hsl(152_55%_70%)]",
  danger: "bg-[hsl(0_72%_95%)] text-[hsl(0_72%_40%)] dark:bg-[hsl(0_62%_18%)] dark:text-[hsl(0_62%_72%)]",
  info: "bg-[hsl(199_78%_94%)] text-[hsl(199_78%_30%)] dark:bg-[hsl(199_78%_18%)] dark:text-[hsl(199_78%_70%)]",
  warning: "bg-[hsl(38_90%_94%)] text-[hsl(38_90%_34%)] dark:bg-[hsl(38_90%_18%)] dark:text-[hsl(38_90%_70%)]",
  neutral: "bg-muted text-muted-foreground",
};

const KpiCard = ({ icon: Icon, label, value, sub, tone = "neutral", testid }) => (
  <Card className="p-4" data-testid={testid}>
    <div className="flex items-center justify-between">
      <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</span>
      <span className={`flex h-7 w-7 items-center justify-center rounded-md ${TONE_CLASSES[tone]}`}>
        <Icon className="h-4 w-4" />
      </span>
    </div>
    <div className="mt-2 font-heading text-2xl sm:text-3xl font-bold tabular-nums">{value}</div>
    {sub ? <div className="mt-1 text-xs text-muted-foreground">{sub}</div> : null}
  </Card>
);

function CommandRow({ label, command, testid }) {
  const copy = async () => {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(command);
      } else {
        throw new Error("clipboard-unavailable");
      }
      toast.success(`${label} copied`);
    } catch (e) {
      // Fallback for non-secure contexts / denied permission
      try {
        const ta = document.createElement("textarea");
        ta.value = command;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
        toast.success(`${label} copied`);
      } catch (err) {
        toast.error("Couldn't copy automatically — please select and copy manually");
      }
    }
  };
  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
        <Terminal className="h-3.5 w-3.5" /> {label}
      </div>
      <div className="flex items-stretch gap-2">
        <code className="flex-1 min-w-0 overflow-x-auto rounded-lg border bg-[hsl(214_55%_10%)] px-3 py-2.5 font-mono text-xs text-[hsl(210_40%_92%)] whitespace-pre">
          {command}
        </code>
        <Button
          variant="outline"
          size="icon"
          className="shrink-0"
          onClick={copy}
          aria-label={`Copy ${label}`}
          data-testid={testid}
        >
          <Copy className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

const STEPS = [
  {
    title: "Log into MCA manually in your browser",
    body: "Open mca.gov.in, sign in, and solve any CAPTCHA yourself. The runner never bypasses challenges — a valid human session is required.",
  },
  {
    title: "Copy your fresh session cookie",
    body: "From DevTools → Application → Cookies (or the Network tab request headers), copy the full session cookie string for mca.gov.in.",
  },
  {
    title: "Inject the cookie as an environment variable",
    body: "Export MCA_SESSION_COOKIE in the same shell you will run the script from. A fresh cookie is required for every session.",
  },
  {
    title: "Run exactly one session, then stop",
    body: "Run the session command below. It processes a bounded batch within a 110-minute budget and stops automatically. It will NOT loop.",
  },
  {
    title: "Respect the guardrails",
    body: "Max 3 sessions/day with a minimum 3-hour gap. If you see a CAPTCHA / session-expired STOP, get a brand-new cookie before re-running.",
  },
];

export default function AdminEnrichment() {
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["enrichment-progress"],
    queryFn: getEnrichmentProgress,
    refetchInterval: 30000,
  });

  const p = data?.progress;
  const g = data?.governance;
  const cmds = data?.commands || {};
  const last = data?.last_session;
  const recent = data?.recent_sessions || [];

  const lastStop = last?.stop_reason;
  const showStopBanner = lastStop && HARD_STOP_REASONS.has(lastStop);
  const stopMeta = lastStop ? stopReasonMeta(lastStop) : null;

  return (
    <div className="space-y-6" data-testid={T.page}>
      {/* Header */}
      <div className="flex items-end justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-heading text-2xl font-bold flex items-center gap-2">
            <Database className="h-6 w-6 text-accent" /> MCA Enrichment
          </h1>
          <p className="text-sm text-muted-foreground">
            Human-in-the-loop batch runner · {data?.cohort_description || "priority cohort"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="gap-1.5">
            <ShieldCheck className="h-3.5 w-3.5 text-[hsl(152_55%_36%)]" />
            Auto-scraping disabled
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            data-testid={T.refreshButton}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isFetching ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {isError && (
        <Card className="p-4 border-destructive/40 flex items-center gap-2 text-sm">
          <AlertTriangle className="h-4 w-4 text-destructive" />
          Could not load enrichment progress. Please refresh.
        </Card>
      )}

      {/* Data upload (Companies & LLPs) */}
      <DataUploadCard onUploaded={() => refetch()} />

      {/* Hard-stop banner */}
      {showStopBanner && stopMeta && (
        <Card
          className={`p-4 flex items-start gap-3 border-0 ${TONE_CLASSES.danger}`}
          data-testid={T.stopReasonBanner}
        >
          <stopMeta.icon className="h-5 w-5 mt-0.5 shrink-0" />
          <div className="text-sm">
            <div className="font-semibold">Last session stopped: {stopMeta.label}</div>
            <div className="opacity-90">
              MCA likely challenged or expired the session. Get a brand-new MCA_SESSION_COOKIE
              before starting another session — do not re-run with the old cookie.
            </div>
          </div>
        </Card>
      )}

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading ? (
          <>
            <KpiSkeleton /><KpiSkeleton /><KpiSkeleton /><KpiSkeleton />
          </>
        ) : (
          <>
            <KpiCard
              icon={Database} label="Remaining" value={formatNumber(p?.remaining)}
              sub={`${formatNumber(p?.not_yet_attempted)} not yet attempted`}
              tone="info" testid={T.kpiRemaining}
            />
            <KpiCard
              icon={CheckCircle2} label="Enriched" value={formatNumber(p?.enriched)}
              sub={`of ${formatNumber(p?.total)} priority companies`}
              tone="success" testid={T.kpiEnriched}
            />
            <KpiCard
              icon={AlertTriangle} label="Failed (retryable)" value={formatNumber(p?.attempted_failed)}
              sub={`${formatNumber(p?.permanently_failed)} permanently failed`}
              tone="warning" testid={T.kpiFailed}
            />
            <KpiCard
              icon={Activity} label="Sessions today"
              value={`${g?.sessions_today ?? 0}/${g?.max_sessions_per_day ?? 3}`}
              sub={`min ${g?.min_gap_hours ?? 3}h gap · ${g?.time_budget_minutes ?? 110}m budget`}
              tone="neutral" testid={T.kpiSessionsToday}
            />
          </>
        )}
      </div>

      {/* Progress */}
      <Card className="p-5" data-testid={T.progressBar}>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-heading text-sm font-semibold">Enrichment progress</h3>
          <span className="text-sm font-medium tabular-nums">{p?.progress_pct ?? 0}%</span>
        </div>
        {isLoading ? (
          <ChartSkeleton h={12} />
        ) : (
          <>
            <Progress value={p?.progress_pct || 0} className="h-3" />
            <div className="mt-2 flex justify-between text-xs text-muted-foreground">
              <span>{formatNumber(p?.enriched)} enriched</span>
              <span>{formatNumber(p?.remaining)} remaining</span>
            </div>
          </>
        )}
      </Card>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Governance status */}
        <Card className="p-5" data-testid={T.governanceStatus}>
          <h3 className="font-heading text-sm font-semibold mb-4 flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-accent" /> Session governance
          </h3>

          {isLoading ? (
            <ChartSkeleton h={140} />
          ) : g?.can_start_now ? (
            <div className={`rounded-lg p-3 flex items-center gap-2 text-sm font-medium ${TONE_CLASSES.success}`}>
              <CheckCircle2 className="h-4 w-4" />
              Ready — you may start a session now.
            </div>
          ) : (
            <div className={`rounded-lg p-3 flex items-start gap-2 text-sm font-medium ${TONE_CLASSES.warning}`}>
              <Clock className="h-4 w-4 mt-0.5" />
              <span>
                On cooldown. Next session allowed at{" "}
                <span className="font-semibold">{g?.next_available_ist || "—"}</span>.
              </span>
            </div>
          )}

          <div className="mt-4 space-y-2.5 text-sm">
            <Row label="Sessions used today" value={`${g?.sessions_today ?? 0} / ${g?.max_sessions_per_day ?? 3}`} />
            <Row label="Minimum gap between sessions" value={`${g?.min_gap_hours ?? 3} hours`} />
            <Row
              label="Hours since last session"
              value={g?.hours_since_last_session != null ? `${g.hours_since_last_session} h` : "—"}
            />
            <Row label="Batch size per session" value={`${formatNumber(g?.batch_size)} companies`} />
            <Row label="Time budget per session" value={`${g?.time_budget_minutes ?? 110} minutes`} />
            <Row label="Circuit breaker" value={`${g?.max_consecutive_failures ?? 5} consecutive failures`} />
          </div>
        </Card>

        {/* Copy command helper */}
        <Card className="p-5">
          <h3 className="font-heading text-sm font-semibold mb-1 flex items-center gap-2">
            <Terminal className="h-4 w-4 text-accent" /> Run a session
          </h3>
          <p className="text-xs text-muted-foreground mb-4">
            Inject a fresh cookie, then run one of the commands below in the backend shell.
          </p>
          <div className="space-y-4">
            <CommandRow
              label="1 · Set your fresh MCA session cookie"
              command={cmds.set_cookie || "export MCA_SESSION_COOKIE='<paste-cookie>'"}
              testid={T.copyCookieCommand}
            />
            <CommandRow
              label="2 · Run one enrichment session"
              command={cmds.run_session || "cd /app/backend/services && python run_enrichment_session.py"}
              testid={T.copyRunCommand}
            />
            <Separator />
            <CommandRow
              label="Retry previously-failed companies (counts as a session)"
              command={cmds.retry_failed || "cd /app/backend/services && python retry_failed_enrichment.py"}
              testid={T.copyRetryCommand}
            />
          </div>
        </Card>
      </div>

      {/* Instruction panel */}
      <Card className="p-5" data-testid={T.instructionPanel}>
        <h3 className="font-heading text-sm font-semibold mb-4 flex items-center gap-2">
          <ListChecks className="h-4 w-4 text-accent" /> How to run a safe session
        </h3>
        <ol className="space-y-4">
          {STEPS.map((s, i) => (
            <li key={i} className="flex gap-3">
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent text-accent-foreground text-xs font-bold tabular-nums">
                {i + 1}
              </span>
              <div>
                <div className="text-sm font-medium">{s.title}</div>
                <div className="text-sm text-muted-foreground">{s.body}</div>
              </div>
            </li>
          ))}
        </ol>
        <div className="mt-4 rounded-lg border border-dashed p-3 flex items-start gap-2 text-xs text-muted-foreground">
          <Cookie className="h-4 w-4 mt-0.5 shrink-0 text-accent" />
          Cookies expire quickly. If a run stops with “session expired” or “CAPTCHA”, that is the
          safety system working — fetch a new cookie and try again later within the daily limit.
        </div>
      </Card>

      {/* Recent sessions */}
      <Card className="p-2 sm:p-4" data-testid={T.recentSessionsTable}>
        <h3 className="font-heading text-sm font-semibold p-2 flex items-center gap-2">
          <Activity className="h-4 w-4 text-accent" /> Recent sessions
        </h3>
        {isLoading ? (
          <ChartSkeleton h={160} />
        ) : recent.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <CircleSlash className="h-8 w-8 text-muted-foreground/50 mb-2" />
            <p className="text-sm font-medium">No sessions run yet</p>
            <p className="text-xs text-muted-foreground">
              Sessions appear here once you run the enrichment script manually.
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Started</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Enriched</TableHead>
                <TableHead className="text-right">Failed</TableHead>
                <TableHead className="text-right">Minutes</TableHead>
                <TableHead>Stop reason</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recent.map((s, i) => {
                const meta = stopReasonMeta(s.stop_reason || s.status);
                const Icon = meta.icon;
                return (
                  <TableRow key={s.session_id || i}>
                    <TableCell className="text-sm">{formatDate(s.started_at)}</TableCell>
                    <TableCell className="capitalize text-sm">{s.type || "enrichment"}</TableCell>
                    <TableCell className="text-right tabular-nums">{formatNumber(s.enriched_count)}</TableCell>
                    <TableCell className="text-right tabular-nums">{formatNumber(s.failed_count)}</TableCell>
                    <TableCell className="text-right tabular-nums">{s.elapsed_minutes ?? 0}</TableCell>
                    <TableCell>
                      <span className={`inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium ${TONE_CLASSES[meta.tone]}`}>
                        <Icon className="h-3 w-3" /> {meta.label}
                      </span>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  );
}

const Row = ({ label, value }) => (
  <div className="flex items-center justify-between">
    <span className="text-muted-foreground">{label}</span>
    <span className="font-medium tabular-nums">{value}</span>
  </div>
);
