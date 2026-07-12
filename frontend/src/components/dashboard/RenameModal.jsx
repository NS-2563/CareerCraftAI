import { Button } from "@/components/ui/button";

export default function RenameModal({
  showRenameModal,
  renameValue,
  setRenameValue,
  handleRename,
  selectedResume,
  handleClose,
}) {
  if (!showRenameModal) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        <div className="border-b px-6 py-4">
          <h3 className="text-lg font-semibold">Rename Resume</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Choose a new name for your resume.
          </p>
        </div>
        <div className="px-6 py-5">
          <input
            type="text"
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            autoFocus
          />
        </div>
        <div className="flex justify-end gap-2 border-t p-4">
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>

          <Button onClick={() => handleRename(selectedResume.id)}>
            Save Changes
          </Button>
        </div>
      </div>
    </div>
  );
}



