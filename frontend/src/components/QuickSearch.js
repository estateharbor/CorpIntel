import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Building2, Loader2 } from "lucide-react";
import {
  CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList,
} from "@/components/ui/command";
import { Button } from "@/components/ui/button";
import { quickSearch } from "@/lib/api";

export function QuickSearch({ variant = "button" }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const down = (e) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  useEffect(() => {
    if (!q) {
      setItems([]);
      return;
    }
    setLoading(true);
    const t = setTimeout(async () => {
      try {
        const d = await quickSearch(q, 8);
        setItems(d.suggestions || []);
      } catch (e) {
        setItems([]);
      } finally {
        setLoading(false);
      }
    }, 250);
    return () => clearTimeout(t);
  }, [q]);

  const select = (cin) => {
    setOpen(false);
    setQ("");
    navigate(`/company/${cin}`);
  };

  return (
    <>
      <Button
        variant="outline"
        onClick={() => setOpen(true)}
        data-testid="topbar-quick-search"
        className="h-10 min-w-0 justify-start gap-2 text-muted-foreground w-full max-w-md bg-background px-2 mb:px-3"
      >
        <Search className="h-4 w-4" />
        <span className="hidden xs:inline truncate text-sm">Search companies, CIN, sector…</span>
        <span className="xs:hidden truncate text-sm">Search</span>
        <kbd className="ml-auto hidden sm:inline-flex items-center rounded border bg-muted px-1.5 text-[10px] font-mono">
          ⌘K
        </kbd>
      </Button>
      <CommandDialog open={open} onOpenChange={setOpen} shouldFilter={false}>
        <CommandInput
          placeholder="Search by company name, CIN, sector…"
          value={q}
          onValueChange={setQ}
          data-testid="quick-search-input"
        />
        <CommandList>
          {loading && (
            <div className="flex items-center gap-2 p-4 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" /> Searching…
            </div>
          )}
          {!loading && q && items.length === 0 && <CommandEmpty>No companies found.</CommandEmpty>}
          {items.length > 0 && (
            <CommandGroup heading="Companies">
              {items.map((it) => (
                <CommandItem
                  key={it.cin}
                  value={`${it.name} ${it.cin}`}
                  onSelect={() => select(it.cin)}
                  data-testid="quick-search-result"
                  className="flex items-center gap-3"
                >
                  <Building2 className="h-4 w-4 text-accent shrink-0" />
                  <div className="min-w-0">
                    <div className="truncate font-medium">{it.name}</div>
                    <div className="truncate text-xs text-muted-foreground">
                      {it.cin} · {it.city || "—"} · {it.sector || "Unclassified"}
                    </div>
                  </div>
                </CommandItem>
              ))}
            </CommandGroup>
          )}
        </CommandList>
      </CommandDialog>
    </>
  );
}
