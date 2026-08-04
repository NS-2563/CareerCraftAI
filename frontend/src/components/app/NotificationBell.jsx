/* eslint react-hooks/set-state-in-effect: "off" */
import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Bell, BellDot, X as XIcon, FileEdit, Loader2 } from "lucide-react";
import { useSuggestions, useDismissSuggestion, useGenerateFromSuggestion } from "@/communication/hooks/useSuggestions";
import { normalizeError } from "@/utils/apiErrorHandler";

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [generateError, setGenerateError] = useState(null);
  const ref = useRef(null);
  const { data: suggestions = [] } = useSuggestions();
  const dismissMutation = useDismissSuggestion();
  const generateMutation = useGenerateFromSuggestion();
  const navigate = useNavigate();

  useEffect(() => {
    function handleClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (!open) {
      setGenerateError(null);
    }
  }, [open]);

  const count = suggestions.length;
  const Icon = count > 0 ? BellDot : Bell;

  const handleDismiss = (id) => {
    dismissMutation.mutate(id);
  };

  const handleGenerate = (id, jobAppId) => {
    setGenerateError(null);
    generateMutation.mutate(id, {
      onSuccess: () => {
        setOpen(false);
        navigate(`/communication?jobId=${jobAppId}`);
      },
      onError: (err) => {
        const status = err?.response?.status;
        if (status === 429) {
          setGenerateError("AI service is temporarily rate-limited. Please wait a moment and try again.");
        } else {
          setGenerateError(normalizeError(err).message);
        }
      },
    });
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="relative p-2 rounded-md hover:bg-accent"
        title="Notifications"
      >
        <Icon className="w-5 h-5" />
        {count > 0 && (
          <span className="absolute -top-0.5 -right-0.5 inline-flex items-center justify-center w-4 h-4 text-[10px] font-bold text-white bg-red-500 rounded-full">
            {count > 9 ? "9+" : count}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 w-80 bg-background border rounded-md shadow-lg z-50 max-h-96 flex flex-col">
          <div className="flex items-center justify-between px-4 py-2 border-b">
            <span className="text-sm font-semibold">Follow-up Suggestions</span>
            <button onClick={() => setOpen(false)} className="p-1 rounded hover:bg-accent">
              <XIcon className="w-4 h-4" />
            </button>
          </div>
          {generateError && (
            <div className="px-4 py-2 bg-destructive/10 border-b">
              <p className="text-xs text-destructive font-medium">{generateError}</p>
            </div>
          )}

          {count === 0 ? (
            <div className="p-4 text-sm text-muted-foreground text-center">
              No outstanding suggestions
            </div>
          ) : (
            <div className="overflow-y-auto flex-1">
              {suggestions.map((s) => (
                <div key={s.id} className="flex items-start gap-3 px-4 py-3 border-b last:border-0 hover:bg-accent/50">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{s.job_title}</p>
                    <p className="text-xs text-muted-foreground truncate">{s.job_company}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {s.days_since_update}d since last update
                    </p>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <button
                      onClick={() => handleGenerate(s.id, s.job_application_id)}
                      disabled={generateMutation.isPending}
                      className="p-1.5 rounded hover:bg-primary/10 text-primary"
                      title="Generate follow-up"
                    >
                      {generateMutation.isPending ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <FileEdit className="w-4 h-4" />
                      )}
                    </button>
                    <button
                      onClick={() => handleDismiss(s.id)}
                      className="p-1.5 rounded hover:bg-accent text-muted-foreground hover:text-foreground"
                      title="Dismiss"
                    >
                      <XIcon className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
