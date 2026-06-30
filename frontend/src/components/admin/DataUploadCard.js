import React, { useEffect, useRef, useState } from "react";
import {
  UploadCloud, FileSpreadsheet, X, CheckCircle2, AlertTriangle, Download,
  Loader2, Building2, Users, Trash2,
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
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { uploadCsv, getUploadStatus, purgeSampleData } from "@/lib/api";
import { DATA_UPLOAD as T } from "@/constants/testIds";

const TEMPLATE_HEADER =
  "identifier,name,status,date_of_incorporation,paid_up_capital,total_contribution,authorized_capital,company_class,principal_activity,roc,address,pin_code,registered_state";
const TEMPLATE_ROWS = [
  'U72900MH2020PTC123456,Example Technologies Private Limited,Active,15-03-2020,500000,,1000000,Private,Computer programming and consultancy,RoC-Mumbai,"Office 12, Tech Park, Andheri, Mumbai - 400053",400053,Maharashtra',
  'AAB-1234,Example Designs LLP,Active,22-07-2021,,250000,,LLP,Design and consultancy services,RoC-Mumbai,"Unit 5, Business Park, Vashi, Navi Mumbai - 400703",400703,Maharashtra',
];

function downloadTemplate() {
  const csv = [TEMPLATE_HEADER, ...TEMPLATE_ROWS].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "corpintel_upload_template.csv";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function formatBytes(n) {
  if (!n) return "0 B";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

const StatPill = ({ icon: Icon, label, value, tone }) => (
  <div className={`flex items-center gap-2 rounded-lg px-3 py-2 ${tone}`}>
    <Icon className="h-4 w-4 shrink-0" />
    <div className="leading-tight">
      <div className="text-base font-bold tabular-nums">{value}</div>
      <div className="text-[11px] opacity-90">{label}</div>
    </div>
  </div>
);

export function DataUploadCard({ onUploaded }) {
  const [file, setFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [job, setJob] = useState(null);        // live job doc (queued/processing)
  const [result, setResult] = useState(null);  // completed job doc
  const [error, setError] = useState(null);     // failed error_message
  const [dragOver, setDragOver] = useState(false);
  const [purging, setPurging] = useState(false);
  const inputRef = useRef(null);
  const pollRef = useRef(null);

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  // Clean up the polling interval on unmount.
  useEffect(() => stopPolling, []);

  const pickFile = (f) => {
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".csv")) {
      toast.error("Please select a .csv file");
      return;
    }
    setFile(f);
    setResult(null);
    setError(null);
    setJob(null);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    pickFile(e.dataTransfer.files?.[0]);
  };

  const clear = () => {
    stopPolling();
    setFile(null);
    setResult(null);
    setError(null);
    setJob(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const startPolling = (jobId) => {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const doc = await getUploadStatus(jobId);
        setJob(doc);
        if (doc.status === "completed") {
          stopPolling();
          setResult(doc);
          setJob(null);
          const added = (doc.inserted_count || 0);
          toast.success(`Upload complete: ${added} added, ${doc.updated_count || 0} updated, ${doc.rejected_count || 0} rejected`);
          if (onUploaded) onUploaded();
        } else if (doc.status === "failed") {
          stopPolling();
          setError(doc.error_message || "Upload processing failed");
          setJob(null);
          toast.error("Upload failed during processing");
        }
      } catch (e) {
        // transient poll error — keep polling
      }
    }, 2500);
  };

  const submit = async () => {
    if (!file) return;
    setSubmitting(true);
    setResult(null);
    setError(null);
    try {
      const res = await uploadCsv(file);
      // Immediately enter background-processing mode (non-blocking).
      setJob({ job_id: res.job_id, status: res.status || "queued",
               total_rows: 0, processed_rows: 0, inserted_count: 0,
               updated_count: 0, rejected_count: 0, duplicate_within_file_count: 0 });
      toast.info("Upload started — processing in the background");
      startPolling(res.job_id);
    } catch (e) {
      const detail = e?.response?.data?.detail || "Upload failed — please check the file and try again";
      toast.error(typeof detail === "string" ? detail : "Upload failed");
    } finally {
      setSubmitting(false);
    }
  };

  const purge = async () => {
    setPurging(true);
    try {
      const res = await purgeSampleData();
      toast.success(`Sample data cleared: ${res.deleted_companies} companies removed`);
      setResult(null);
      if (onUploaded) onUploaded();
    } catch (e) {
      const detail = e?.response?.data?.detail || "Could not clear sample data";
      toast.error(typeof detail === "string" ? detail : "Could not clear sample data");
    } finally {
      setPurging(false);
    }
  };

  const busy = submitting || !!job;          // an upload is in progress
  const pct = job && job.total_rows > 0
    ? Math.min(100, Math.round((job.processed_rows / job.total_rows) * 100))
    : 0;

  return (
    <Card className="p-5" data-testid={T.card}>
      <div className="flex items-start justify-between gap-3 flex-wrap mb-1">
        <div>
          <h3 className="font-heading text-sm font-semibold flex items-center gap-2">
            <UploadCloud className="h-4 w-4 text-accent" /> Upload data · Companies &amp; LLPs
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            CSV with a CIN or LLPIN per row. Existing records are updated (matched by identifier); new ones are added.
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
        <Button
          variant="outline"
          size="sm"
          onClick={downloadTemplate}
          data-testid={T.templateButton}
        >
          <Download className="h-4 w-4 mr-2" /> CSV template
        </Button>
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              disabled={purging}
              className="text-destructive border-destructive/30 hover:bg-destructive/10 hover:text-destructive"
              data-testid={T.purgeButton}
            >
              {purging ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Trash2 className="h-4 w-4 mr-2" />}
              Clear sample data
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Clear all sample data?</AlertDialogTitle>
              <AlertDialogDescription>
                This permanently deletes all demo/sample companies and their directors,
                enrichment and alert records, giving you a clean slate for your own upload.
                Auto-reseeding is disabled so it won't come back. Your uploaded data is not affected.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={purge}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                data-testid={T.purgeConfirmButton}
              >
                Yes, clear sample data
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
        </div>
      </div>

      {/* Dropzone */}
      <label
        htmlFor="data-upload-input"
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        data-testid={T.dropzone}
        className={`mt-3 flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-4 py-8 cursor-pointer transition-colors duration-150 ${
          dragOver ? "border-accent bg-accent/5" : "border-border hover:border-accent/60 hover:bg-muted/40"
        }`}
      >
        <input
          id="data-upload-input"
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          className="sr-only"
          onChange={(e) => pickFile(e.target.files?.[0])}
          data-testid={T.fileInput}
        />
        <UploadCloud className="h-8 w-8 text-muted-foreground mb-2" />
        <p className="text-sm font-medium">Drag &amp; drop your CSV here, or click to browse</p>
        <p className="text-xs text-muted-foreground mt-1">Supports both Companies (CIN) and LLPs (LLPIN) · max 150 MB</p>
      </label>

      {/* Selected file + actions */}
      {file && (
        <div className="mt-3 flex items-center gap-3 rounded-lg border p-3">
          <FileSpreadsheet className="h-5 w-5 text-accent shrink-0" />
          <div className="min-w-0 flex-1">
            <div className="text-sm font-medium truncate">{file.name}</div>
            <div className="text-xs text-muted-foreground">{formatBytes(file.size)}</div>
          </div>
          <Button
            className="bg-accent text-accent-foreground hover:brightness-95"
            size="sm"
            onClick={submit}
            disabled={busy}
            data-testid={T.submitButton}
          >
            {busy ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <UploadCloud className="h-4 w-4 mr-2" />}
            {submitting ? "Starting…" : job ? "Processing…" : "Upload"}
          </Button>
          <Button variant="ghost" size="icon" onClick={clear} disabled={submitting} aria-label="Clear file" data-testid={T.clearButton}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Live background-processing progress */}
      {job && (
        <div className="mt-4 space-y-3" data-testid={T.progress}>
          <Separator />
          <div className="flex items-center justify-between flex-wrap gap-2">
            <span className="text-sm font-medium flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-accent" />
              {job.status === "queued" ? "Queued — starting…" : "Processing in the background…"}
            </span>
            <span className="text-sm tabular-nums text-muted-foreground">
              {(job.processed_rows || 0).toLocaleString()} / {(job.total_rows || 0).toLocaleString()} rows
            </span>
          </div>
          <Progress value={pct} className="h-3" />
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <StatPill icon={Building2} label="Inserted" value={(job.inserted_count || 0).toLocaleString()}
              tone="bg-[hsl(199_78%_94%)] text-[hsl(199_78%_30%)] dark:bg-[hsl(199_78%_18%)] dark:text-[hsl(199_78%_70%)]" />
            <StatPill icon={Building2} label="Updated" value={(job.updated_count || 0).toLocaleString()}
              tone="bg-muted text-muted-foreground" />
            <StatPill icon={Users} label="Duplicates in file" value={(job.duplicate_within_file_count || 0).toLocaleString()}
              tone="bg-[hsl(270_60%_95%)] text-[hsl(270_50%_40%)] dark:bg-[hsl(270_40%_22%)] dark:text-[hsl(270_60%_80%)]" />
            <StatPill icon={AlertTriangle} label="Rejected" value={(job.rejected_count || 0).toLocaleString()}
              tone="bg-[hsl(38_90%_94%)] text-[hsl(38_90%_34%)] dark:bg-[hsl(38_90%_18%)] dark:text-[hsl(38_90%_70%)]" />
          </div>
          <p className="text-xs text-muted-foreground">
            You can keep using the app — this runs in the background. Job ID: <span className="font-mono">{job.job_id}</span>
          </p>
        </div>
      )}

      {/* Failed state */}
      {error && (
        <div className="mt-4 space-y-2">
          <Separator />
          <div className="flex items-start gap-2 rounded-lg p-3 bg-[hsl(0_72%_95%)] text-[hsl(0_72%_40%)] dark:bg-[hsl(0_62%_18%)] dark:text-[hsl(0_62%_72%)]">
            <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
            <div className="text-sm">
              <div className="font-semibold">Upload failed</div>
              <div className="opacity-90 break-words">{error}</div>
            </div>
          </div>
          <Button variant="outline" size="sm" onClick={submit} disabled={!file || busy}>
            <UploadCloud className="h-4 w-4 mr-2" /> Retry upload
          </Button>
        </div>
      )}

      {/* Result summary */}
      {result && (
        <div className="mt-4 space-y-3" data-testid={T.result}>
          <Separator />
          <div className="flex items-center justify-between flex-wrap gap-2">
            <span className="text-sm font-medium flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-[hsl(152_55%_36%)]" /> {result.message}
            </span>
            <Badge variant="secondary">{result.total_rows} rows read</Badge>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <StatPill
              icon={Building2} label="Companies added"
              value={result.companies_inserted || 0}
              tone="bg-[hsl(199_78%_94%)] text-[hsl(199_78%_30%)] dark:bg-[hsl(199_78%_18%)] dark:text-[hsl(199_78%_70%)]"
            />
            <StatPill
              icon={Building2} label="Companies updated"
              value={result.companies_updated || 0}
              tone="bg-muted text-muted-foreground"
            />
            <StatPill
              icon={Users} label="LLPs added"
              value={result.llps_inserted || 0}
              tone="bg-[hsl(270_60%_95%)] text-[hsl(270_50%_40%)] dark:bg-[hsl(270_40%_22%)] dark:text-[hsl(270_60%_80%)]"
            />
            <StatPill
              icon={AlertTriangle} label="Rejected"
              value={result.rejected_count || 0}
              tone={
                (result.rejected_count || 0) > 0
                  ? "bg-[hsl(38_90%_94%)] text-[hsl(38_90%_34%)] dark:bg-[hsl(38_90%_18%)] dark:text-[hsl(38_90%_70%)]"
                  : "bg-muted text-muted-foreground"
              }
            />
          </div>

          {(result.rejected_rows || []).length > 0 && (
            <div className="rounded-lg border" data-testid={T.rejectedList}>
              <div className="px-3 py-2 text-xs font-medium text-muted-foreground border-b">
                Rejected rows (fix and re-upload)
              </div>
              <div className="max-h-56 overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-16">Row</TableHead>
                      <TableHead>Identifier</TableHead>
                      <TableHead>Reason</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.rejected_rows.map((r, i) => (
                      <TableRow key={i}>
                        <TableCell className="tabular-nums">{r.row_number}</TableCell>
                        <TableCell className="font-mono text-xs break-all">{r.identifier || "—"}</TableCell>
                        <TableCell className="text-sm">{r.reason}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
