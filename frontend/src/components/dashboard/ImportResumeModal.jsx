import { useState, useRef } from "react";
import { Upload, FileText, X, Loader2, AlertCircle } from "lucide-react";
import { apiClient } from "@/lib/api";
import { Button } from "@/components/ui/button";

export default function ImportResumeModal({ open, onClose, onSuccess }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef(null);

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

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const { data } = await apiClient.post("/api/resume/import", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      onSuccess?.(data);
      setFile(null);
      onClose();
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
    setFile(null);
    setError(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">Import Resume</h2>
          <button
            onClick={handleClose}
            disabled={uploading}
            className="p-1 rounded-md hover:bg-gray-100 disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-sm text-gray-500 mb-6">
          Upload a PDF resume to import it into your library. The text will be extracted and you can refine it in Resume Studio.
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
                disabled={uploading}
                className="ml-auto p-1 rounded-md hover:bg-gray-200 disabled:opacity-50"
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
          <Button variant="outline" onClick={handleClose} disabled={uploading}>
            Cancel
          </Button>
          <Button onClick={handleUpload} disabled={!file || uploading}>
            {uploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                Importing...
              </>
            ) : (
              "Import Resume"
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
