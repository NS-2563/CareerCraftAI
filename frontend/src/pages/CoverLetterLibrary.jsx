import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import * as Dialog from "@radix-ui/react-dialog";
import {
  Archive,
  Copy,
  Eye,
  FileText,
  History,
  Link2,
  Plus,
  RefreshCw,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";

import { StatusBadge } from "@/components/ui/atoms";
import DeleteConfirmModal from "@/components/ui/DeleteConfirmModal";
import {
  searchCoverLetters,
  listArchivedCoverLetters,
  getVersionHistory,
  restoreVersion,
  duplicateCoverLetter,
  renameCoverLetter,
  archiveCoverLetter,
  restoreCoverLetter,
  deleteCoverLetter,
} from "@/services/coverLetterApi";

const formatDate = (d) =>
  d ? new Date(d).toLocaleDateString() : "N/A";

const formatDateTime = (d) => {
  if (!d) return "N/A";
  const date = new Date(d);
  if (Number.isNaN(date.getTime())) return "N/A";
  return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
};

export default function CoverLetterLibrary() {
  const [coverLetters, setCoverLetters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");
  const [sortBy, setSortBy] = useState("updated_at");

  const [busy, setBusy] = useState(false);

  // Rename modal
  const [renameTarget, setRenameTarget] = useState(null);
  const [renameValue, setRenameValue] = useState("");

  // Version modal
  const [versionsTarget, setVersionsTarget] = useState(null);
  const [versions, setVersions] = useState([]);
  const [versionsOpen, setVersionsOpen] = useState(false);

  // Delete modal
  const [deleteTarget, setDeleteTarget] = useState(null);

  const searchTimer = useRef(null);

  const loadLetters = async (query, filter, sort) => {
    setLoading(true);
    setError(null);
    try {
      if (filter === "archived") {
        const result = await listArchivedCoverLetters();
        setCoverLetters(result.success ? result.data || [] : []);
      } else {
        const result = await searchCoverLetters(query, filter === "all" ? false : true, sort);
        setCoverLetters(result.success ? result.data || [] : []);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => {
      loadLetters(searchQuery, activeFilter, sortBy);
    }, 300);
    return () => {
      if (searchTimer.current) clearTimeout(searchTimer.current);
    };
  }, [searchQuery, activeFilter, sortBy]);

  const handleDuplicate = async (cl) => {
    setBusy(true);
    try {
      const result = await duplicateCoverLetter(cl.id, `${cl.title} (Copy)`);
      if (result.success) {
        toast.success("Cover letter duplicated");
        loadLetters(searchQuery, activeFilter, sortBy);
      } else {
        toast.error(result.error);
      }
    } finally {
      setBusy(false);
    }
  };

  const openRename = (cl) => {
    setRenameTarget(cl);
    setRenameValue(cl.title || "");
  };

  const handleRename = async () => {
    if (!renameTarget || !renameValue.trim()) return;
    setBusy(true);
    try {
      const result = await renameCoverLetter(renameTarget.id, renameValue.trim());
      if (result.success) {
        toast.success("Cover letter renamed");
        setRenameTarget(null);
        loadLetters(searchQuery, activeFilter, sortBy);
      } else {
        toast.error(result.error);
      }
    } finally {
      setBusy(false);
    }
  };

  const openVersions = async (cl) => {
    setVersionsTarget(cl);
    setVersions([]);
    setVersionsOpen(true);
    try {
      const result = await getVersionHistory(cl.id);
      setVersions(Array.isArray(result.data) ? result.data : []);
    } catch {
      setVersions([]);
    }
  };

  const handleRestoreVersion = async (version) => {
    if (!versionsTarget) return;
    setBusy(true);
    try {
      const result = await restoreVersion(versionsTarget.id, version);
      if (result.success) {
        toast.success(`Restored version ${version}`);
        setVersionsOpen(false);
        loadLetters(searchQuery, activeFilter, sortBy);
      } else {
        toast.error(result.error);
      }
    } finally {
      setBusy(false);
    }
  };

  const handleArchive = async (cl) => {
    setBusy(true);
    try {
      const result = await archiveCoverLetter(cl.id);
      if (result.success) toast.success("Cover letter archived");
      else toast.error(result.error);
      loadLetters(searchQuery, activeFilter, sortBy);
    } finally {
      setBusy(false);
    }
  };

  const handleRestore = async (cl) => {
    setBusy(true);
    try {
      const result = await restoreCoverLetter(cl.id);
      if (result.success) toast.success("Cover letter restored");
      else toast.error(result.error);
      loadLetters(searchQuery, activeFilter, sortBy);
    } finally {
      setBusy(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    setBusy(true);
    try {
      const result = await deleteCoverLetter(deleteTarget.id);
      if (result.success) toast.success("Cover letter deleted");
      else toast.error(result.error);
      setDeleteTarget(null);
      loadLetters(searchQuery, activeFilter, sortBy);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Cover Letter Library</h1>
          <p className="text-sm text-muted-foreground">
            All your saved cover letters, with generation metadata, ATS keyword
            coverage and version history.
          </p>
        </div>
        <Link
          to="/cover-letter-studio?create=1"
          className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="size-4" />
          New cover letter
        </Link>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col gap-3 border-b pb-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search cover letters..."
            className="h-9 flex-1 rounded-md border border-input bg-transparent px-3 text-sm"
          />
          <Link
            to="/cover-letter-studio"
            className="inline-flex h-9 shrink-0 items-center gap-2 rounded-md border border-input px-3 text-sm hover:bg-accent"
          >
            <Eye className="size-4" />
            Open studio
          </Link>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="h-9 rounded-md border border-input bg-transparent px-2.5 py-1 text-sm"
          >
            <option value="updated_at">Sort: Updated</option>
            <option value="title">Sort: Title</option>
          </select>

          <select
            value={activeFilter}
            onChange={(e) => setActiveFilter(e.target.value)}
            className="h-9 rounded-md border border-input bg-transparent px-2.5 py-1 text-sm"
          >
            <option value="all">Filter: Active</option>
            <option value="archived">Filter: Archived</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-600">
          {error}
        </div>
      )}

      {/* Cards */}
      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-44 animate-pulse rounded-xl border p-5">
              <div className="h-5 w-40 rounded bg-muted" />
              <div className="mt-3 h-4 w-24 rounded bg-muted" />
              <div className="mt-2 h-4 w-32 rounded bg-muted" />
            </div>
          ))}
        </div>
      ) : coverLetters.length === 0 ? (
        <div className="rounded-xl border border-dashed p-10 text-center">
          <FileText className="mx-auto size-10 text-muted-foreground" />
          <h2 className="mt-3 font-semibold">No cover letters yet</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {searchQuery || activeFilter === "archived"
              ? "Try clearing your search or filters."
              : "Create your first cover letter in the studio."}
          </p>
          {!searchQuery && activeFilter !== "archived" && (
            <Link
              to="/cover-letter-studio?create=1"
              className="mt-4 inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              <Plus className="size-4" />
              Create cover letter
            </Link>
          )}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {coverLetters.map((cl) => (
            <div key={cl.id} className="flex flex-col rounded-xl border p-5 shadow-sm">
              <div className="flex items-start justify-between gap-2">
                <Link
                  to={`/cover-letter-studio?id=${cl.id}`}
                  className="min-w-0 font-semibold hover:text-primary"
                >
                  <span className="block truncate">{cl.title || "Untitled"}</span>
                </Link>
                <span className="shrink-0 text-xs text-muted-foreground tabular-nums">
                  v{cl.version || 1}
                </span>
              </div>

              <div className="mt-2 flex flex-wrap items-center gap-1.5 text-xs">
                <StatusBadge status={cl.tone || "professional"} />
                <span className="rounded-full border px-2 py-0.5 capitalize text-muted-foreground">
                  {cl.template || "modern"}
                </span>
              </div>

              {cl.job_title || cl.company_name ? (
                <div className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Link2 className="size-3.5" />
                  {[cl.job_title, cl.company_name].filter(Boolean).join(" @ ")}
                </div>
              ) : null}

              <div className="mt-3 text-xs text-muted-foreground">
                Updated {formatDate(cl.updated_at)}
                {cl.generated_at
                  ? <> · Generated {formatDate(cl.generated_at)}</>
                  : null}
              </div>

              {cl.ai_provider || cl.model_name ? (
                <div className="mt-1 truncate font-mono text-[11px] text-muted-foreground">
                  {[cl.ai_provider, cl.model_name].filter(Boolean).join(" · ")}
                </div>
              ) : null}

              <div className="mt-auto flex flex-wrap items-center gap-1.5 pt-4">
                <Link
                  to={`/cover-letter-studio?id=${cl.id}`}
                  className="inline-flex h-8 items-center gap-1.5 rounded-md border px-2 text-sm hover:bg-accent"
                >
                  <Eye className="size-3.5" />
                  Open
                </Link>
                <button
                  className="inline-flex h-8 items-center gap-1.5 rounded-md border px-2 text-sm hover:bg-accent disabled:opacity-50"
                  disabled={busy}
                  onClick={() => openRename(cl)}
                >
                  <FileText className="size-3.5" />
                  Rename
                </button>
                <button
                  className="inline-flex h-8 items-center gap-1.5 rounded-md border px-2 text-sm hover:bg-accent disabled:opacity-50"
                  disabled={busy}
                  onClick={() => handleDuplicate(cl)}
                >
                  <Copy className="size-3.5" />
                  Duplicate
                </button>
                <button
                  className="inline-flex h-8 items-center gap-1.5 rounded-md border px-2 text-sm hover:bg-accent disabled:opacity-50"
                  disabled={busy}
                  onClick={() => openVersions(cl)}
                >
                  <History className="size-3.5" />
                  Versions
                </button>
                {cl.is_archived ? (
                  <button
                    className="inline-flex h-8 items-center gap-1.5 rounded-md border px-2 text-sm hover:bg-accent disabled:opacity-50"
                    disabled={busy}
                    onClick={() => handleRestore(cl)}
                  >
                    <RefreshCw className="size-3.5" />
                    Restore
                  </button>
                ) : (
                  <button
                    className="inline-flex h-8 items-center gap-1.5 rounded-md border px-2 text-sm hover:bg-accent disabled:opacity-50"
                    disabled={busy}
                    onClick={() => handleArchive(cl)}
                  >
                    <Archive className="size-3.5" />
                    Archive
                  </button>
                )}
                <button
                  className="inline-flex h-8 items-center gap-1.5 rounded-md border px-2 text-sm text-red-600 hover:bg-red-50 disabled:opacity-50"
                  disabled={busy}
                  onClick={() => setDeleteTarget(cl)}
                >
                  <Trash2 className="size-3.5" />
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Rename modal */}
      <Dialog.Root open={Boolean(renameTarget)} onOpenChange={(o) => !o && setRenameTarget(null)}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50" />
          <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-96 -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-background p-6 shadow-lg">
            <Dialog.Title className="mb-4 text-lg font-semibold">
              Rename Cover Letter
            </Dialog.Title>
            <input
              type="text"
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              className="mb-4 w-full rounded-md border px-3 py-2 text-sm"
              autoFocus
            />
            <div className="flex justify-end gap-2">
              <button
                className="rounded-md border px-4 py-2 text-sm"
                onClick={() => setRenameTarget(null)}
              >
                Cancel
              </button>
              <button
                className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
                disabled={busy || !renameValue.trim()}
                onClick={handleRename}
              >
                Rename
              </button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      {/* Version history modal */}
      <Dialog.Root open={versionsOpen} onOpenChange={setVersionsOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-50 bg-black/50" />
          <Dialog.Content className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-background p-6 shadow-lg">
            <Dialog.Title className="mb-1 text-lg font-semibold">
              Version History
            </Dialog.Title>
            <p className="mb-4 text-sm text-muted-foreground">
              {versionsTarget?.title || "Cover letter"}
            </p>
            {versions.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">
                No version history yet.
              </p>
            ) : (
              <div className="max-h-80 space-y-2 overflow-auto">
                {versions.map((v) => (
                  <div
                    key={v.version}
                    className="flex items-center justify-between rounded-md border p-3 text-sm"
                  >
                    <div>
                      <div className="font-medium">Version {v.version}</div>
                      <div className="text-xs text-muted-foreground">
                        {formatDateTime(v.updated_at)}
                        {v.summary ? ` · ${v.summary}` : ""}
                      </div>
                    </div>
                    <button
                      className="rounded-md border px-2 py-1 text-xs hover:bg-accent disabled:opacity-50"
                      disabled={busy}
                      onClick={() => handleRestoreVersion(v.version)}
                    >
                      Restore
                    </button>
                  </div>
                ))}
              </div>
            )}
            <div className="mt-4 flex justify-end">
              <button
                className="rounded-md border px-4 py-2 text-sm"
                onClick={() => setVersionsOpen(false)}
              >
                Close
              </button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      {/* Delete modal */}
      <DeleteConfirmModal
        open={Boolean(deleteTarget)}
        title={deleteTarget ? `Delete "${deleteTarget.title}"` : "Delete Cover Letter"}
        description={`Are you sure you want to delete "${deleteTarget?.title}"? This action cannot be undone.`}
        onCancel={() => setDeleteTarget(null)}
        onConfirm={handleConfirmDelete}
        confirmDisabled={busy}
      />
    </div>
  );
}
