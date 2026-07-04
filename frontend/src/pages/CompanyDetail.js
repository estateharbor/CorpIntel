import React from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft, Building2, MapPin, Calendar, IndianRupee, Hash, Briefcase, Lock,
  Mail, Phone, Globe, Linkedin, FileText, Landmark, Users, Loader2,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/StatusBadge";
import { EntityBadge } from "@/components/EntityBadge";
import { CityTag, SectorChip } from "@/components/CityTag";
import { CompanyCard } from "@/components/CompanyCard";
import {
  getCompany, getDirectors, getPartners, getCharges, getFilings, getContact, getSimilar,
} from "@/lib/api";
import { formatINR, formatDate } from "@/lib/format";
import { useAuth } from "@/context/AuthContext";

function Stat({ icon: Icon, label, value }) {
  return (
    <div className="flex items-start gap-2.5">
      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary dark:bg-white/5 dark:text-foreground shrink-0">
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0">
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className="text-sm font-medium break-words">{value || "—"}</div>
      </div>
    </div>
  );
}

export default function CompanyDetail() {
  const { cin } = useParams();  // route param may be a CIN or an LLPIN
  const navigate = useNavigate();
  const { user } = useAuth();

  const { data: company, isLoading } = useQuery({ queryKey: ["company", cin], queryFn: () => getCompany(cin) });
  const isLLP = company?.entity_type === "LLP";

  const { data: directors } = useQuery({ queryKey: ["directors", cin], queryFn: () => getDirectors(cin), enabled: !!company && !isLLP });
  const { data: partners } = useQuery({ queryKey: ["partners", cin], queryFn: () => getPartners(cin), enabled: !!company && isLLP });
  const { data: charges } = useQuery({ queryKey: ["charges", cin], queryFn: () => getCharges(cin), enabled: !!company });
  const { data: filings } = useQuery({ queryKey: ["filings", cin], queryFn: () => getFilings(cin), enabled: !!company });
  const { data: contact } = useQuery({ queryKey: ["contact", cin, user?.plan], queryFn: () => getContact(cin), enabled: !!company });
  const { data: similar } = useQuery({ queryKey: ["similar", cin], queryFn: () => getSimilar(cin, 6), enabled: !!company });

  // Entity-aware "people" view: Designated Partners for LLPs, Directors otherwise.
  const people = isLLP ? (partners?.partners || []) : (directors?.directors || []);
  const peopleLoaded = isLLP ? !!partners : !!directors;
  const peopleCount = isLLP ? partners?.count : directors?.count;
  const peopleLabel = isLLP ? "Designated Partners" : "Directors";
  const peopleIdLabel = isLLP ? "DPIN" : "DIN";

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }
  if (!company) {
    return <Card className="p-10 text-center">Entity not found. <Link to="/search" className="text-accent underline">Back to search</Link></Card>;
  }

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="-ml-2"><ArrowLeft className="mr-1 h-4 w-4" /> Back</Button>

      {/* Header */}
      <Card className="p-4 xs:p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex min-w-0 items-start gap-3 xs:gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground">
              {isLLP ? <Users className="h-6 w-6" /> : <Building2 className="h-6 w-6" />}
            </div>
            <div className="min-w-0">
              <h1 className="font-heading text-2xl font-bold leading-tight" data-testid="company-header-name">{company.name}</h1>
              <div className="mt-1 font-mono text-xs text-muted-foreground break-all" data-testid="company-header-identifier">{company.identifier || company.cin}</div>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <EntityBadge type={company.entity_type} />
                <StatusBadge status={company.status} />
                <CityTag city={company.city} area={company.area} />
                <SectorChip sector={company.sector} />
                {company.interesting_flag && <Badge className="bg-accent/15 text-accent-foreground border border-accent/30">✨ Interesting</Badge>}
              </div>
            </div>
          </div>
          <div className="w-full mb:w-auto mb:text-right">
            <div className="text-xs text-muted-foreground">{isLLP ? "Total contribution" : "Paid-up capital"}</div>
            <div className="font-heading text-xl xs:text-2xl font-bold tabular-nums" data-testid="company-header-capital">
              {formatINR(isLLP && company.total_contribution != null ? company.total_contribution : company.paid_up_capital)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">Data quality {company.data_quality_score}/100</div>
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="overview" data-testid="company-tabs">
        <TabsList className="flex flex-wrap h-auto">
          <TabsTrigger value="overview" data-testid="tab-overview">Overview</TabsTrigger>
          <TabsTrigger value="directors" data-testid="tab-directors">{peopleLabel} {peopleLoaded ? `(${peopleCount})` : ""}</TabsTrigger>
          <TabsTrigger value="charges" data-testid="tab-charges">Charges {charges ? `(${charges.charges.length})` : ""}</TabsTrigger>
          <TabsTrigger value="filings" data-testid="tab-filings">Filings {filings ? `(${filings.filings.length})` : ""}</TabsTrigger>
          <TabsTrigger value="contact" data-testid="tab-contact">Contact</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-4">
          <Card className="p-4 xs:p-6">
            <div className="grid mb:grid-cols-2 lg:grid-cols-3 gap-5">
              <Stat icon={Hash} label={isLLP ? "LLPIN" : "CIN"} value={company.identifier || company.cin} />
              <Stat icon={Landmark} label="ROC" value={company.roc} />
              <Stat icon={Briefcase} label={isLLP ? "Entity type" : "Company class"} value={isLLP ? "LLP" : company.company_class} />
              {!isLLP && <Stat icon={Building2} label="Category" value={company.category} />}
              <Stat icon={Calendar} label={isLLP ? "Date of registration" : "Date of incorporation"} value={formatDate(company.date_of_incorporation)} />
              {isLLP ? (
                <Stat icon={IndianRupee} label="Total contribution" value={formatINR(company.total_contribution)} />
              ) : (
                <>
                  <Stat icon={IndianRupee} label="Authorized capital" value={formatINR(company.authorized_capital)} />
                  <Stat icon={IndianRupee} label="Paid-up capital" value={formatINR(company.paid_up_capital)} />
                </>
              )}
              <Stat icon={MapPin} label="Registered address" value={company.address} />
              <Stat icon={Briefcase} label="Principal activity" value={company.principal_activity} />
            </div>
            {company.interesting_reason && (
              <div className="mt-5 rounded-lg bg-accent/10 border border-accent/20 p-4 text-sm">
                <span className="font-medium">AI insight:</span> {company.interesting_reason}
              </div>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="directors" className="mt-4">
          <Card className="p-2 sm:p-4" data-testid="people-table">
            {!peopleLoaded ? <Skeleton className="h-40 w-full" /> : people.length === 0 ? (
              <EmptyRow icon={Users} text={isLLP ? "No designated partner records available." : "No director records available."} />
            ) : (
              <Table>
                <TableHeader><TableRow><TableHead>{peopleIdLabel}</TableHead><TableHead>Name</TableHead><TableHead>Designation</TableHead><TableHead>Appointed</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
                <TableBody>
                  {people.map((d) => (
                    <TableRow key={d.din || d.dpin}>
                      <TableCell className="font-mono text-xs">{d.din || d.dpin}</TableCell>
                      <TableCell className="font-medium">{d.name}</TableCell>
                      <TableCell>{d.designation}</TableCell>
                      <TableCell>{formatDate(d.date_of_appointment)}</TableCell>
                      <TableCell>{d.is_active ? <Badge className="bg-success/15 text-success">Active</Badge> : <Badge variant="secondary">Inactive</Badge>}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="charges" className="mt-4">
          <Card className="p-2 sm:p-4">
            {!charges ? <Skeleton className="h-40 w-full" /> : charges.charges.length === 0 ? (
              <EmptyRow icon={Landmark} text="No registered charges (loans/mortgages)." />
            ) : (
              <Table>
                <TableHeader><TableRow><TableHead>Charge ID</TableHead><TableHead>Amount</TableHead><TableHead>Holder</TableHead><TableHead>Created</TableHead><TableHead>Satisfied</TableHead></TableRow></TableHeader>
                <TableBody>
                  {charges.charges.map((c, i) => (
                    <TableRow key={i}>
                      <TableCell className="font-mono text-xs">{c.charge_id}</TableCell>
                      <TableCell className="tabular-nums">{formatINR(c.amount)}</TableCell>
                      <TableCell>{c.holder}</TableCell>
                      <TableCell>{c.created}</TableCell>
                      <TableCell>{c.satisfied ? <Badge className="bg-success/15 text-success">Yes</Badge> : <Badge variant="secondary">No</Badge>}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="filings" className="mt-4">
          <Card className="p-2 sm:p-4">
            {!filings ? <Skeleton className="h-40 w-full" /> : filings.filings.length === 0 ? (
              <EmptyRow icon={FileText} text="No filing history available." />
            ) : (
              <Table>
                <TableHeader><TableRow><TableHead>Form type</TableHead><TableHead>Financial year</TableHead><TableHead>Filing date</TableHead><TableHead>Status</TableHead></TableRow></TableHeader>
                <TableBody>
                  {filings.filings.map((f, i) => (
                    <TableRow key={i}>
                      <TableCell className="font-medium">{f.form_type}</TableCell>
                      <TableCell>{f.financial_year || "—"}</TableCell>
                      <TableCell>{f.filing_date}</TableCell>
                      <TableCell><Badge className="bg-success/15 text-success">{f.status}</Badge></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="contact" className="mt-4">
          <Card className="p-4 xs:p-6">
            {!contact ? <Skeleton className="h-32 w-full" /> : contact.locked ? (
              <div className="text-center py-8">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-muted"><Lock className="h-5 w-5 text-muted-foreground" /></div>
                <p className="mt-3 font-medium">Contact data is a Pro feature</p>
                <p className="text-sm text-muted-foreground mt-1">{contact.message}</p>
                <Button asChild className="mt-4 bg-accent text-accent-foreground hover:brightness-95"><Link to="/pricing">Upgrade to Pro</Link></Button>
              </div>
            ) : (
              <div className="grid mb:grid-cols-2 gap-5">
                <Stat icon={Hash} label="GSTIN" value={contact.gstin} />
                <Stat icon={Phone} label="Phone" value={contact.phone} />
                <Stat icon={Mail} label="Email" value={contact.email} />
                <Stat icon={Globe} label="Website" value={contact.website} />
                <Stat icon={Linkedin} label="LinkedIn" value={contact.linkedin_url} />
              </div>
            )}
          </Card>
        </TabsContent>
      </Tabs>

      {/* Similar */}
      <div data-testid="company-similar-companies">
        <h2 className="font-heading text-lg font-semibold mb-3">Similar companies</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {(similar?.results || []).map((c) => <CompanyCard key={c.identifier || c.cin} company={c} />)}
        </div>
      </div>
    </div>
  );
}

function EmptyRow({ icon: Icon, text }) {
  return (
    <div className="flex flex-col items-center justify-center py-10 text-center">
      <Icon className="h-8 w-8 text-muted-foreground" />
      <p className="mt-2 text-sm text-muted-foreground">{text}</p>
    </div>
  );
}
