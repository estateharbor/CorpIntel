import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background px-4 text-center">
      <h1 className="font-heading text-3xl font-bold">Page not found</h1>
      <p className="max-w-md text-sm text-muted-foreground">
        The page you are looking for is not available.
      </p>
      <Link href="/" className="text-sm font-medium text-accent underline">
        Back to CorpIntel
      </Link>
    </main>
  );
}
