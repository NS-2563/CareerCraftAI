import { Button } from "@/components/ui/button";

export default function VersionHistoryModal({
  showVersionModal,
  versions,
  handleClose,
  handleRestoreVersion,
}) {
  if (!showVersionModal) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[80vh] overflow-y-auto">
        <div className="p-4 border-b flex justify-between items-center">
          <h3 className="text-lg font-semibold">Version History</h3>
          <Button variant="ghost" size="icon" onClick={handleClose}>
            ✕
          </Button>
        </div>
        <div className="p-4">
          {versions.length === 0 ? (
            <p className="text-gray-500">No version history available</p>
          ) : (
            <div className="space-y-2">
              {versions.map((v, idx) => (
                <div
                  key={idx}
                  className="flex justify-between items-center p-2 bg-gray-50 rounded"
                >
                  <div>
                    <span className="font-medium">Version {v.version}</span>
                    <span className="text-sm text-gray-500 ml-2">
                      {new Date(v.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleRestoreVersion(v.version)}
                  >
                    Restore
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}



