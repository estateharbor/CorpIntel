"use client";

import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search as SearchIcon, SlidersHorizontal, ChevronLeft, ChevronRight, Bookmark, Inbox } from "lucide-react";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Sheet, SheetContent, SheetTrigger, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { FilterSidebar } from "@/components/FilterSidebar";
import { CompanyCard } from "@/components/CompanyCard";
import { GridSkeleton } from "@/components/Skeletons";
import { getCompanies, saveSearch } from "@/lib/api";
import { SORT_OPTIONS, formatNumber } from "@/lib/format";
import { useAuth } from "@/context/AuthContext";

const DEFAULT_FILTERS = { city: "All", status: "All", sector: "All", company_class: "All", entity_type: "All", date_from: "", date_to: "", min_capital: 0, max_capital: 100000000 };
const LIMIT = 24;

export default function SearchPage() {
  const { user } = useAuth();
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [searchText, setSearchText] = useState("");
  const [debounced, setDebounced] = useState("");
  const [sortBy, setSortBy] = useState("date_of_incorporation");
  const [order, setOrder] = useState("desc");
  const [page, setPage] = useState(1);

  React.useEffect(() => {
    const t = setTimeout(() => { setDebounced(searchText); setPage(1); }, 350);
    return () => clearTimeout(t);
  }, [searchText]);

  const params = useMemo(() => {
    const p = { sort_by: sortBy, order, page, limit: LIMIT };
    if (debounced) p.search = debounced;
    if (filters.city !== "All") p.city = filters.city;
    if (filters.status !== "All") p.status = filters.status;
    if (filters.sector !== "All") p.sector = filters.sector;
    if (filters.company_class !== "All") p.company_class = filters.company_class;
    if (filters.entity_type !== "All") p.entity_type = filters.entity_type;
    if (filters.date_from) p.date_from = filters.date_from;
    if (filters.date_to) p.date_to = filters.date_to;
    if (filters.min_capital > 0) p.min_capital = filters.min_capital;
    if (filters.max_capital < 100000000) p.max_capital = filters.max_capital;
    return p;
  }, [filters, debounced, sortBy, order, page]);

  const { data, isLoading, isError } = useQuery({ queryKey: ["companies", params], queryFn: () => getCompanies(params), keepPreviousData: true });

  const patch = (p) => { setFilters((f) => ({ ...f, ...p })); setPage(1); };
  const reset = () => { setFilters(DEFAULT_FILTERS); setSearchText(""); setPage(1); };

  const onSave = async () => {
    if (!user) { toast.error("Sign in to save searches"); return; }
    try {
      await saveSearch({ name: debounced || `${filters.city} · ${filters.sector}`, criteria: params });
      toast.success("Search saved");
    } catch (e) { toast.error("Could not save search"); }
  };

  const total = data?.total || 0;
  const pages = data?.pages || 1;

  return (
    <div className="flex gap-6">
      {/* Desktop filters */}
      <aside className="hidden lg:block w-64 shrink-0">
        <Card className="p-4 sticky top-20">
          <FilterSidebar value={filters} onChange={patch} onReset={reset} />
        </Card>
      </aside>

      <div className="flex-1 min-w-0 space-y-4">
        <div>
          <h1 className="font-heading text-2xl font-bold">Company Search</h1>
          <p className="text-sm text-muted-foreground">Search and filter companies across the Mumbai Metropolitan Region</p>
        </div>

        <div className="relative">
          <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Search by company name, CIN or sector…"
            className="pl-9 h-11"
            data-testid="search-input"
          />
        </div>

        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            {/* Mobile filter trigger */}
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="outline" className="lg:hidden" data-testid="search-filters-open-button">
                  <SlidersHorizontal className="mr-2 h-4 w-4" /> Filters
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-[min(100vw_-_2rem,320px)] overflow-y-auto">
                <SheetHeader><SheetTitle>Filters</SheetTitle></SheetHeader>
                <div className="mt-4"><FilterSidebar value={filters} onChange={patch} onReset={reset} /></div>
              </SheetContent>
            </Sheet>
            <span className="text-sm text-muted-foreground" data-testid="search-results-count">
              {isLoading ? "Loading…" : `${formatNumber(total)} companies`}
            </span>
          </div>
          <div className="grid w-full grid-cols-1 gap-2 xs:grid-cols-2 xl:w-auto xl:flex xl:items-center">
            <Select value={filters.entity_type} onValueChange={(v) => patch({ entity_type: v })}>
              <SelectTrigger className="h-9 w-full xl:w-[130px]" data-testid="search-entity-type-select"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="All">All types</SelectItem>
                <SelectItem value="Company">Companies</SelectItem>
                <SelectItem value="LLP">LLPs</SelectItem>
              </SelectContent>
            </Select>
            <Select value={sortBy} onValueChange={(v) => { setSortBy(v); setPage(1); }}>
              <SelectTrigger className="h-9 w-full xl:w-[180px]" data-testid="search-sort-select"><SelectValue /></SelectTrigger>
              <SelectContent>{SORT_OPTIONS.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
            </Select>
            <Select value={order} onValueChange={(v) => { setOrder(v); setPage(1); }}>
              <SelectTrigger className="h-9 w-full xl:w-[120px]"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="desc">Descending</SelectItem>
                <SelectItem value="asc">Ascending</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" className="h-9 w-full xl:w-auto" onClick={onSave} data-testid="search-save-search-button">
              <Bookmark className="mr-2 h-4 w-4" /> Save
            </Button>
          </div>
        </div>

        {isLoading ? (
          <GridSkeleton count={6} />
        ) : isError ? (
          <Card className="p-10 text-center text-muted-foreground">Failed to load companies.</Card>
        ) : total === 0 ? (
          <Card className="p-12 text-center">
            <Inbox className="mx-auto h-10 w-10 text-muted-foreground" />
            <p className="mt-3 font-medium">No companies match your filters</p>
            <Button variant="outline" className="mt-4" onClick={reset}>Reset filters</Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {data.results.map((c) => <CompanyCard key={c.identifier || c.cin} company={c} />)}
          </div>
        )}

        {pages > 1 && (
          <div className="flex items-center justify-center gap-3 pt-2" data-testid="search-pagination">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)} data-testid="pagination-prev">
              <ChevronLeft className="h-4 w-4" /> Prev
            </Button>
            <span className="text-sm text-muted-foreground tabular-nums">Page {page} of {pages}</span>
            <Button variant="outline" size="sm" disabled={page >= pages} onClick={() => setPage((p) => p + 1)} data-testid="pagination-next">
              Next <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
