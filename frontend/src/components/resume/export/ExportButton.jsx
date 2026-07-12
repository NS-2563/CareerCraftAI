import { useState } from "react";
import { FileDown, Loader2, AlertCircle } from "lucide-react";
import { exportToPDF } from "@/utils/pdfExport";

export default function ExportButton({ previewRef, resumeData, disabled }) {
  const [isExporting, setIsExporting] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState(null);

  async function handleExport() {
    if (!previewRef?.current) {
      setError("Preview not available");
      return;
    }

    setIsExporting(true);
    setError(null);

    const result = await exportToPDF(previewRef.current, resumeData, {
      onProgress: setStatus,
    });

    setIsExporting(false);
    setStatus("");

    if (!result.success) {
      setError(result.error || "Export failed");
      setTimeout(() => setError(null), 3000);
    }
  }

  return (
    <div className="relative">
      <button
        onClick={handleExport}
        disabled={disabled || isExporting}
        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isExporting ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>{status || "Generating PDF..."}</span>
          </>
        ) : (
          <>
            <FileDown className="w-4 h-4" />
            <span>Download PDF</span>
          </>
        )}
      </button>

      {error && (
        <div className="absolute top-full mt-2 left-0 flex items-center gap-2 text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}

