import { useRef } from "react";
import ResumeToolbar from "./ResumeToolbar";
import ResumePreview from "./ResumePreview";
import ResumeWizard from "./wizard/ResumeWizard";
import AIAssistantPanel from "@/components/ai/AIAssistantPanel";
import { useResumeContext } from "@/context/useResumeContext";

export default function ResumeBuilder({ initialSection }) {
  const { selectedTemplate, setSelectedTemplate } = useResumeContext();
  const previewRef = useRef(null);

  return (
    <div className="min-h-screen bg-background">

      <ResumeToolbar previewRef={previewRef} />

      <div className="grid lg:grid-cols-12 gap-4 sm:gap-8 p-4 sm:p-6">

        {/* Templates */}
        <aside className="lg:col-span-2 rounded-xl border p-4 sm:p-6">

          <h2 className="text-lg font-semibold mb-4">
            Templates
          </h2>

          <div className="flex lg:flex-col gap-3 overflow-x-auto pb-2">
            {/* Modern */}
            <button
              className={`shrink-0 w-48 lg:w-full rounded-lg border-2 p-3 text-left transition-all hover:shadow-md ${
                selectedTemplate === "modern"
                  ? "border-primary bg-primary/5 shadow-md"
                  : "border-border hover:border-primary/50"
              }`}
              onClick={() => setSelectedTemplate("modern")}
            >
              <div className="font-medium">Modern</div>
              <div className="text-xs text-muted-foreground mt-1">Clean layout with bold headers</div>
            </button>

            {/* Minimal */}
            <button
              className={`shrink-0 w-48 lg:w-full rounded-lg border-2 p-3 text-left transition-all hover:shadow-md ${
                selectedTemplate === "minimal"
                  ? "border-primary bg-primary/5 shadow-md"
                  : "border-border hover:border-primary/50"
              }`}
              onClick={() => setSelectedTemplate("minimal")}
            >
              <div className="font-medium">Minimal</div>
              <div className="text-xs text-muted-foreground mt-1">ATS-friendly, black & white</div>
            </button>

            {/* Professional */}
            <button
              className={`shrink-0 w-48 lg:w-full rounded-lg border-2 p-3 text-left transition-all hover:shadow-md ${
                selectedTemplate === "professional"
                  ? "border-primary bg-primary/5 shadow-md"
                  : "border-border hover:border-primary/50"
              }`}
              onClick={() => setSelectedTemplate("professional")}
            >
              <div className="font-medium">Professional</div>
              <div className="text-xs text-muted-foreground mt-1">Two-column with sidebar</div>
            </button>

            {/* Corporate */}
            <button
              className={`shrink-0 w-48 lg:w-full rounded-lg border-2 p-3 text-left transition-all hover:shadow-md ${
                selectedTemplate === "corporate"
                  ? "border-primary bg-primary/5 shadow-md"
                  : "border-border hover:border-primary/50"
              }`}
              onClick={() => setSelectedTemplate("corporate")}
            >
              <div className="font-medium">Corporate</div>
              <div className="text-xs text-muted-foreground mt-1">Executive blue style</div>
            </button>

            {/* Creative */}
            <button
              className={`shrink-0 w-48 lg:w-full rounded-lg border-2 p-3 text-left transition-all hover:shadow-md ${
                selectedTemplate === "creative"
                  ? "border-primary bg-primary/5 shadow-md"
                  : "border-border hover:border-primary/50"
              }`}
              onClick={() => setSelectedTemplate("creative")}
            >
              <div className="font-medium">Creative</div>
              <div className="text-xs text-muted-foreground mt-1">Modern gradient accents</div>
            </button>
          </div>

        </aside>

        {/* Wizard (left) */}
        <main className="lg:col-span-5 rounded-xl border p-6">

          <h2 className="text-xl font-semibold mb-6">
            Resume Editor
          </h2>

          <ResumeWizard initialSection={initialSection} />

        </main>

        {/* Preview (right, sticky) */}
        <aside className="lg:col-span-5 lg:sticky lg:top-6 self-start">

          <ResumePreview ref={previewRef} />

        </aside>

        {/* AI Assistant Panel */}
        <aside className="hidden lg:block">

          <AIAssistantPanel />

        </aside>

      </div>


    </div>
  );
}

