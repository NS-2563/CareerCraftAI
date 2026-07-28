import { useState, useRef, useCallback } from "react";
import { Upload, FileText, X, Loader2, AlertCircle, CheckCircle2 } from "lucide-react";
import { apiClient } from "@/lib/api";
import { Button } from "@/components/ui/button";
import ImportReviewStep from "@/components/dashboard/import-review/ImportReviewStep";

const STEP_UPLOAD = "upload";
const STEP_PARSING = "parsing";
const STEP_REVIEW = "review";

export default function ImportResumeModal({ open, onClose, onSuccess }) {
  const [step, setStep] = useState(STEP_UPLOAD);
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [parsedData, setParsedData] = useState(null);
  const [sourceMeta, setSourceMeta] = useState(null);
  const [resumeName, setResumeName] = useState("");
  const inputRef = useRef(null);

  const resetState = useCallback(() => {
    setStep(STEP_UPLOAD);
    setFile(null);
    setUploading(false);
    setError(null);
    setDragOver(false);
    setParsedData(null);
    setSourceMeta(null);
    setResumeName("");
  }, []);

  if (!open) return null;

  const MAX_SIZE = 10 * 1024 * 1024;

  const isValidFile = (f) => {
    if (!f) return false;
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are accepted.");
      return false;
    }
    if (f.size > MAX_SIZE) {
      setError("File exceeds the maximum size of 10MB.");
      return false;
    }
    return true;
  };

  const handleFileSelect = (e) => {
    setError(null);
    const f = e.target.files?.[0];
    if (f && isValidFile(f)) {
      setFile(f);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    setError(null);
    const f = e.dataTransfer?.files?.[0];
    if (f && isValidFile(f)) {
      setFile(f);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  const handleParse = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const { data } = await apiClient.post("/api/resume/import/parse", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setParsedData(data.parsed_data || {});
      setSourceMeta(data.source_meta || {});
      setResumeName(data.resume_name || "Imported Resume");
      setStep(STEP_REVIEW);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (detail) {
        if (typeof detail === "object" && detail.message) {
          setError(detail.message);
        } else if (typeof detail === "string") {
          setError(detail);
        } else {
          setError("Import failed. Please try again.");
        }
      } else {
        setError(err?.message || "Import failed. Please try again.");
      }
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    if (uploading) return;
    resetState();
    onClose();
  };

  const handleReviewCancel = () => {
    resetState();
    onClose();
  };

  const handleReviewSuccess = () => {
    resetState();
    onClose();
    onSuccess?.();
  };

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-6 pb-0">
          <h2 className="text-xl font-bold">
            {step === STEP_UPLOAD && "Import Resume"}
            {step === STEP_PARSING && "Import Resume"}
            {step === STEP_REVIEW && "Import Review"}
          </h2>
          <button
            onClick={handleClose}
            disabled={uploading}
            className="p-1 rounded-md hover:bg-gray-100 disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto flex-1">
          {/* Step indicators */}
          <div className="flex items-center gap-2 mb-6">
            <div
              className={`flex items-center gap-1.5 text-sm ${
                step === STEP_UPLOAD ? "text-primary font-semibold" : "text-green-600"
              }`}
            >
              {step !== STEP_UPLOAD ? (
                <CheckCircle2 className="w-4 h-4" />
              ) : (
                <span className="w-2 h-2 rounded-full bg-primary" />
              )}
              Upload
            </div>
            <div className="flex-1 h-px bg-gray-200" />
            <div
              className={`flex items-center gap-1.5 text-sm ${
                step === STEP_PARSING
                  ? "text-primary font-semibold"
                  : step === STEP_REVIEW
                  ? "text-green-600"
                  : "text-gray-400"
              }`}
            >
              {(step === STEP_REVIEW || step === STEP_PARSING) &&
              step !== STEP_PARSING ? (
                <CheckCircle2 className="w-4 h-4" />
              ) : step === STEP_PARSING ? (
                <span className="w-2 h-2 rounded-full bg-primary" />
              ) : (
                <span className="w-2 h-2 rounded-full bg-gray-300" />
              )}
              Parse
            </div>
            <div className="flex-1 h-px bg-gray-200" />
            <div
              className={`flex items-center gap-1.5 text-sm ${
                step === STEP_REVIEW ? "text-primary font-semibold" : "text-gray-400"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  step === STEP_REVIEW ? "bg-primary" : "bg-gray-300"
                }`}
              />
              Review
            </div>
          </div>

          {step === STEP_UPLOAD && (
            <div>
              <p className="text-sm text-gray-500 mb-6">
                Upload a PDF resume to import it into your library. The text will be extracted and you can review before saving.
              </p>

              {!file ? (
                <div
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
                    dragOver
                      ? "border-primary bg-primary/5"
                      : "border-gray-300 hover:border-primary/50 hover:bg-gray-50"
                  }`}
                  onClick={() => inputRef.current?.click()}
                >
                  <Upload className="w-10 h-10 mx-auto mb-3 text-gray-400" />
                  <p className="font-medium text-gray-700">Drop your PDF here or click to browse</p>
                  <p className="text-sm text-gray-400 mt-1">PDF only, up to 10MB</p>
                  <input
                    ref={inputRef}
                    type="file"
                    accept=".pdf"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                </div>
              ) : (
                <div className="border rounded-xl p-4 bg-gray-50">
                  <div className="flex items-center gap-3">
                    <FileText className="w-8 h-8 text-primary shrink-0" />
                    <div className="min-w-0">
                      <p className="font-medium truncate">{file.name}</p>
                      <p className="text-sm text-gray-500">
                        {(file.size / 1024 / 1024).toFixed(1)} MB
                      </p>
                    </div>
                    <button
                      onClick={() => { setFile(null); setError(null); }}
                      className="ml-auto p-1 rounded-md hover:bg-gray-200"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}

              {error && (
                <div className="mt-4 flex items-start gap-2 text-sm text-red-600 bg-red-50 border border-red-200 px-3 py-2 rounded-lg">
                  <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div className="flex justify-end gap-3 mt-6">
                <Button variant="outline" onClick={handleClose}>
                  Cancel
                </Button>
                <Button onClick={handleParse} disabled={!file}>
                  <Upload className="w-4 h-4 mr-2" />
                  Parse Resume
                </Button>
              </div>
            </div>
          )}

          {step === STEP_PARSING && (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="w-12 h-12 animate-spin text-primary mb-4" />
              <p className="text-lg font-medium text-gray-900">Analyzing your resume...</p>
              <p className="text-sm text-gray-500 mt-1">
                Extracting and structuring your resume information
              </p>
            </div>
          )}

          {step === STEP_REVIEW && parsedData && (
            <ImportReviewStep
              parsedData={parsedData}
              sourceMeta={sourceMeta}
              resumeName={resumeName}
              onCancel={handleReviewCancel}
              onSuccess={handleReviewSuccess}
            />
          )}
        </div>
      </div>
    </div>
  );
}
