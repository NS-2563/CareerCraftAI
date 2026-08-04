import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { FileText, Plus } from "lucide-react";

import ResumeBuilder from "@/components/resume/ResumeBuilder";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { IconTile } from "@/components/ui/atoms";
import { useResumeContext } from "@/context/useResumeContext";
import resumeApi from "@/services/resumeApi";

export default function ResumeStudio() {
  const location = useLocation();
  const navigate = useNavigate();
  const { resumeId, setResumeId, startNewResume } = useResumeContext();

  const [initialSection, setInitialSection] = useState(null);
  const [prevSearch, setPrevSearch] = useState(location.search);

  if (location.search !== prevSearch) {
    setPrevSearch(location.search);
    setInitialSection(new URLSearchParams(location.search).get("section"));
  }

  const params = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const idFromUrl = params.get("id");
  const createFlag = Boolean(params.get("create"));

  // Only fetch the resume list when the studio is opened without an explicit
  // target (`?id=` for an existing resume, or the explicit-create `?create=1`
  // entrypoint). This is used purely to decide which existing resume to open —
  // it never creates one.
  const { data: resumes, isLoading: resumesLoading } = useQuery({
    queryKey: ["resumes", "workspace"],
    queryFn: () => resumeApi.listResumes(false),
    enabled: !idFromUrl && !createFlag,
    staleTime: 0,
    retry: 1,
  });

  // Keep the open resume in sync with `?id=` so SPA navigation between resumes
  // (e.g. from the Resume Library) loads the requested record instead of a
  // stale one previously held in context.
  const idFromUrlNumber = idFromUrl !== null && idFromUrl !== "" ? Number(idFromUrl) : null;
  useEffect(() => {
    if (!Number.isInteger(idFromUrlNumber) || idFromUrlNumber <= 0) return;
    if (resumeId === idFromUrlNumber) return;
    setResumeId(idFromUrlNumber);
  }, [idFromUrlNumber, resumeId, setResumeId]);

  // Explicit create entrypoint: header "New"/command palette/toolbar links that
  // navigate to /resume-studio?create=1. This is a user action — fires once per
  // visit (handled-ref guards React StrictMode double-invocation).
  const createHandledRef = useRef(false);
  useEffect(() => {
    if (!createFlag) {
      createHandledRef.current = false;
      return;
    }
    if (createHandledRef.current) return;
    createHandledRef.current = true;
    startNewResume();
  }, [createFlag, startNewResume]);

  // Workspace: with no target, open the most recently edited resume. This only
  // selects an existing record — it never creates one. When there are no
  // resumes, the empty state is rendered below.
  const latestResume = useMemo(() => {
    if (!Array.isArray(resumes) || resumes.length === 0) return null;
    return [...resumes].sort(
      (a, b) => new Date(b.updated_at ?? 0) - new Date(a.updated_at ?? 0)
    )[0];
  }, [resumes]);

  useEffect(() => {
    if (idFromUrl || createFlag || resumesLoading || !resumes) return;
    if (!latestResume || resumeId === latestResume.id) return;

    setResumeId(latestResume.id);
    window.history.replaceState({}, "", `/resume-studio?id=${latestResume.id}`);
  }, [idFromUrl, createFlag, resumesLoading, resumes, latestResume, resumeId, setResumeId]);

  if (idFromUrl || createFlag || resumeId) {
    return <ResumeBuilder initialSection={initialSection} />;
  }

  if (resumesLoading || !resumes) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary" />
      </div>
    );
  }

  return (
    <ResumeWorkspaceEmpty
      onCreate={startNewResume}
      onBrowseLibrary={() => navigate("/resumes")}
    />
  );
}

function ResumeWorkspaceEmpty({ onCreate, onBrowseLibrary }) {
  return (
    <div className="mx-auto max-w-2xl py-16">
      <Card sheen className="relative overflow-hidden p-8 text-center sm:p-12">
        <div className="mb-6 flex justify-center">
          <IconTile icon={FileText} accent="var(--brand)" size="lg" />
        </div>
        <h1 className="font-display text-2xl font-semibold tracking-tight">
          No resumes yet
        </h1>
        <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
          Build your first resume, or open the Resume Library to import or
          duplicate an existing one.
        </p>
        <div className="mt-6 flex flex-col justify-center gap-3 sm:flex-row">
          <Button size="lg" onClick={onCreate} className="gap-2">
            <Plus className="size-4" /> Create Resume
          </Button>
          <Button size="lg" variant="outline" onClick={onBrowseLibrary} className="gap-2">
            Browse Resume Library
          </Button>
        </div>
      </Card>
    </div>
  );
}