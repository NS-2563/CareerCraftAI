import { useState } from "react";

import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  ChevronLeft,
  ChevronRight,
  FileText,
  CheckCircle2,
  TrendingUp,
  RefreshCw,
} from "lucide-react";
import useResume from "@/hooks/useResume";
import useAI from "@/hooks/useAI";
import { analyzeResume } from "@/services/aiService";
import AISuggestionCard from "./AISuggestionCard";
import AILoading from "./AILoading";
import AIEmptyState from "./AIEmptyState";

export default function AIAssistantPanel() {
  const [isExpanded, setIsExpanded] = useState(true);
  const { resumeData } = useResume();
  const { loading, error, execute} = useAI();
  const [analysis, setAnalysis] = useState(null);

  // IMPORTANT: Do NOT auto-analyze on resume edits.
  // AI analysis must only run when the user explicitly clicks the button.
  // (Intentionally removed the previous useEffect-based auto trigger.)


  function handleSuggestionClick(suggestion) {
    console.log("Suggestion clicked:", suggestion.title);
  }

  return (
    <motion.aside
      initial={{ width: isExpanded ? 380 : 48 }}
      animate={{ width: isExpanded ? 380 : 48 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      className="lg:sticky lg:top-6 self-start rounded-xl border bg-background overflow-hidden"
    >
      <div className="flex h-full">
        {/* Main Panel Content */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 p-4 space-y-4"
            >
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-primary" />
                  <h2 className="font-semibold">AI Assistant</h2>
                </div>
                <button
                  onClick={() => setIsExpanded(false)}
                  className="p-1 hover:bg-muted rounded"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>

              {/* Loading State */}
              {loading && <AILoading message="Analyzing resume..." />}

              {/* Error State */}
              {error && (
                <div className="p-3 text-sm text-red-600 bg-red-50 rounded-lg">
                  {error}
                </div>
              )}

              {/* Analysis Results */}
              {analysis && !loading && (
                <div className="space-y-4">
                  {/* Analysis Failure State */}
                  {analysis.analysisFailed && (
                    <div className="p-3 text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg">
                      We couldn't complete this analysis — please try again.
                    </div>
                  )}

                  {/* Score Cards */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-lg bg-muted/30">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                        <FileText className="w-3 h-3" />
                        Resume Score
                      </div>
                      <div className="text-2xl font-bold">
                        {analysis.resumeScore ?? "—"}
                        <span className="text-sm font-normal text-muted-foreground">
                          {" "}
                          / 100
                        </span>
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-muted/30">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                        <CheckCircle2 className="w-3 h-3" />
                        ATS Score
                      </div>
                      <div className="text-2xl font-bold">
                        {analysis.atsScore ?? "—"}
                        <span className="text-sm font-normal text-muted-foreground">
                          {" "}
                          / 100
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Re-analyze Button */}
                  <button
                    onClick={async () => {
                      const result = await execute(analyzeResume, resumeData);
                      if (result) {
                        setAnalysis(result);
                      }
                    }}
                    disabled={loading}
                    className="w-full flex items-center justify-center gap-2 p-2 text-sm rounded-lg border hover:bg-muted transition-colors"
                  >
                    <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                    Re-analyze
                  </button>

                  {/* Suggestions */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium">
                      <TrendingUp className="w-4 h-4" />
                      Suggestions
                    </div>

                    {analysis.suggestions?.length > 0 ? (
                      <div className="space-y-2">
                        {analysis.suggestions.map((suggestion, idx) => (
                          <AISuggestionCard
                            key={suggestion.id}
                            suggestion={suggestion}
                            onClick={() => handleSuggestionClick(suggestion)}
                            delay={idx * 0.1}
                          />
                        ))}
                      </div>
                    ) : (
                      <AIEmptyState />
                    )}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Collapse Button */}
        {!isExpanded && (
          <button
            onClick={() => setIsExpanded(true)}
            className="w-12 flex items-center justify-center h-full hover:bg-muted transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        )}
      </div>
    </motion.aside>
  );
}

