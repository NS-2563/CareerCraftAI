import { useState, forwardRef } from "react";
import {
  Download,
  Printer,
  ChevronDown,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { useReactToPrint } from "react-to-print";

const ExportMenu = forwardRef(function ExportMenu(
  { previewRef, disabled },
  ref
) {
  const [isOpen, setIsOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState(null);

  const wait = (ms) => new Promise((r) => setTimeout(r, ms));

  const handlePrintResume = useReactToPrint({
    contentRef: previewRef,

    documentTitle: "Resume",

    pageStyle: `
      @page { size: A4; margin: 0; }
      body {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }
    `,

    onBeforeGetContent: async () => {
      setIsExporting(true);
      setStatus("Preparing print...");
      setError(null);

      await wait(300);
    },

    onAfterPrint: () => {
      setIsExporting(false);
      setStatus("");
    },
  });

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || isExporting}
        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isExporting ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>{status || "Processing..."}</span>
          </>
        ) : (
          <>
            <Download className="w-4 h-4" />
            <span>Export</span>
            <ChevronDown className="w-4 h-4" />
          </>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-background rounded-lg border shadow-lg z-50 overflow-hidden">
          <button
            onClick={() => {
              setIsOpen(false);
              handlePrintResume();
            }}
            disabled={disabled || isExporting}
            className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Printer className="w-4 h-4" />
            <span>Print / Save as PDF</span>
          </button>
        </div>
      )}

      {error && (
        <div className="absolute top-full mt-2 right-0 flex items-center gap-2 text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
});

export default ExportMenu;