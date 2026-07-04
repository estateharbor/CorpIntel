"use client";

export default function ErrorPage({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background px-4 text-center">
      <h1 className="font-heading text-3xl font-bold">Something went wrong</h1>
      <p className="max-w-md text-sm text-muted-foreground">
        The page failed to load. Try again in a moment.
      </p>
      <button
        type="button"
        onClick={reset}
        className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-foreground"
      >
        Retry
      </button>
    </main>
  );
}
