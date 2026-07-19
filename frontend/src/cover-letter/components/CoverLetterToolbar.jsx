import { useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import {
  Download,
  FileText,
  Copy,
  Edit3,
  Trash2,
  MoreVertical,
  RotateCcw,
  FileDown,
  Printer,
  Save,
} from "lucide-react";

const TONES = ["professional", "friendly", "executive", "creative"];
const TEMPLATES = ["modern", "professional", "executive", "minimal"];

export default function CoverLetterToolbar({
  coverLetter,
  onSave,
  onDelete,
  onDuplicate,
  onRename,
  onTemplateChange,
  onToneChange,
  onExport,
  onGenerate,
  isGenerating,
  isSaving,
  isExporting,
}) {
  const [setShowActions] = useState(false);
  const [showRenameDialog, setShowRenameDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [setShowVersionHistory] = useState(false);

  const handleRename = () => {
    if (newTitle.trim()) {
      onRename(newTitle.trim());
      setNewTitle("");
      setShowRenameDialog(false);
    }
  };

  const handleDelete = () => {
    onDelete();
    setShowDeleteDialog(false);
  };

  // Export handlers
  const handleExportPDF = () => onExport("pdf");
  const handleExportDOCX = () => onExport("docx");
  const handlePrint = () => window.print();

  return (
    <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex items-center justify-between px-6 py-3">
        {/* Left: Title */}
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-semibold">
            {coverLetter?.title || "Untitled Cover Letter"}
          </h1>
          <span className="text-sm text-muted-foreground">
            v{coverLetter?.version || 1}
          </span>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          {/* Generate with AI */}
          <button
            className="inline-flex items-center gap-2 px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
            onClick={onGenerate}
            disabled={isGenerating}
          >
            <Edit3 className="w-4 h-4" />
            {isGenerating ? "Generating..." : "Generate AI"}
          </button>

          {/* Save */}
          <button
            className="inline-flex items-center gap-2 px-3 py-1.5 text-sm border rounded-md hover:bg-accent disabled:opacity-50"
            onClick={onSave}
            disabled={isSaving}
          >
            <Save className="w-4 h-4" />
            {isSaving ? "Saving..." : "Save"}
          </button>

          {/* Export Dropdown */}
          <Dialog.Root>
            <Dialog.Trigger asChild>
              <button
                className="inline-flex items-center gap-2 px-3 py-1.5 text-sm border rounded-md hover:bg-accent disabled:opacity-50"
                disabled={isExporting}
              >
                <Download className="w-4 h-4" />
                {isExporting ? "Exporting..." : "Export"}
              </button>
            </Dialog.Trigger>
            <Dialog.Portal>
              <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
              <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-background rounded-lg shadow-lg border p-4 z-50 w-80">
                <Dialog.Title className="text-lg font-semibold mb-4">
                  Export Cover Letter
                </Dialog.Title>
                <div className="grid gap-2">
                  <button
                    className="flex items-center gap-3 w-full p-3 text-left border rounded-md hover:bg-accent"
                    onClick={handleExportPDF}
                  >
                    <FileDown className="w-5 h-5" />
                    <div>
                      <div className="font-medium">PDF</div>
                      <div className="text-sm text-muted-foreground">
                        Best for applications
                      </div>
                    </div>
                  </button>
                  <button
                    className="flex items-center gap-3 w-full p-3 text-left border rounded-md hover:bg-accent"
                    onClick={handleExportDOCX}
                  >
                    <FileText className="w-5 h-5" />
                    <div>
                      <div className="font-medium">DOCX</div>
                      <div className="text-sm text-muted-foreground">
                        Editable Word document
                      </div>
                    </div>
                  </button>
                  <button
                    className="flex items-center gap-3 w-full p-3 text-left border rounded-md hover:bg-accent"
                    onClick={handlePrint}
                  >
                    <Printer className="w-5 h-5" />
                    <div>
                      <div className="font-medium">Print</div>
                      <div className="text-sm text-muted-foreground">
                        Print or save as PDF
                      </div>
                    </div>
                  </button>
                </div>
              </Dialog.Content>
            </Dialog.Portal>
          </Dialog.Root>

          {/* More Actions */}
          <Dialog.Root>
            <Dialog.Trigger asChild>
              <button className="p-2 border rounded-md hover:bg-accent">
                <MoreVertical className="w-4 h-4" />
              </button>
            </Dialog.Trigger>
            <Dialog.Portal>
              <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
              <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-background rounded-lg shadow-lg border p-4 z-50 w-80">
                <Dialog.Title className="text-lg font-semibold mb-4">
                  More Actions
                </Dialog.Title>
                <div className="grid gap-2">
                  <button
                    className="flex items-center gap-3 w-full p-3 text-left border rounded-md hover:bg-accent"
                    onClick={() => {
                      setShowRenameDialog(true);
                      setShowActions(false);
                    }}
                  >
                    <Edit3 className="w-5 h-5" />
                    <span>Rename</span>
                  </button>
                  <button
                    className="flex items-center gap-3 w-full p-3 text-left border rounded-md hover:bg-accent"
                    onClick={() => {
                      onDuplicate();
                      setShowActions(false);
                    }}
                  >
                    <Copy className="w-5 h-5" />
                    <span>Duplicate</span>
                  </button>
                  <button
                    className="flex items-center gap-3 w-full p-3 text-left border rounded-md hover:bg-accent"
                    onClick={() => setShowVersionHistory(true)}
                  >
                    <RotateCcw className="w-5 h-5" />
                    <span>Version History</span>
                  </button>
                  <button
                    className="flex items-center gap-3 w-full p-3 text-left border rounded-md hover:bg-red-50 text-red-600"
                    onClick={() => setShowDeleteDialog(true)}
                  >
                    <Trash2 className="w-5 h-5" />
                    <span>Delete</span>
                  </button>
                </div>
              </Dialog.Content>
            </Dialog.Portal>
          </Dialog.Root>
        </div>
      </div>

      {/* Template & Tone Selection */}
      <div className="flex items-center gap-6 px-6 py-2 border-t">
        {/* Template Selector */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Template:</span>
          <select
            value={coverLetter?.template || "modern"}
            onChange={(e) => onTemplateChange(e.target.value)}
            className="text-sm border rounded-md px-2 py-1"
          >
            {TEMPLATES.map((t) => (
              <option key={t} value={t}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Tone Selector */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Tone:</span>
          <select
            value={coverLetter?.tone || "professional"}
            onChange={(e) => onToneChange(e.target.value)}
            className="text-sm border rounded-md px-2 py-1"
          >
            {TONES.map((t) => (
              <option key={t} value={t}>
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Rename Dialog */}
      <Dialog.Root open={showRenameDialog} onOpenChange={setShowRenameDialog}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
          <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-background rounded-lg shadow-lg border p-6 z-50 w-96">
            <Dialog.Title className="text-lg font-semibold mb-4">
              Rename Cover Letter
            </Dialog.Title>
            <input
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="Enter new title..."
              className="w-full border rounded-md px-3 py-2 mb-4"
              autoFocus
            />
            <div className="flex justify-end gap-2">
              <button
                className="px-4 py-2 border rounded-md"
                onClick={() => setShowRenameDialog(false)}
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 bg-primary text-primary-foreground rounded-md"
                onClick={handleRename}
              >
                Rename
              </button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      {/* Delete Dialog */}
      <Dialog.Root open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
          <Dialog.Content className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-background rounded-lg shadow-lg border p-6 z-50 w-96">
            <Dialog.Title className="text-lg font-semibold mb-4">
              Delete Cover Letter
            </Dialog.Title>
            <p className="text-muted-foreground mb-4">
              Are you sure you want to delete "{coverLetter?.title}"? This action cannot be
              undone.
            </p>
            <div className="flex justify-end gap-2">
              <button
                className="px-4 py-2 border rounded-md"
                onClick={() => setShowDeleteDialog(false)}
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 bg-red-600 text-white rounded-md"
                onClick={handleDelete}
              >
                Delete
              </button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  );
}

