/* eslint react-hooks/set-state-in-effect: "off" */
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import historyApi from "@/services/historyApi";
import CareerHistoryEmpty from "@/components/career/CareerHistoryEmpty";
import DeleteConfirmModal from "@/components/ui/DeleteConfirmModal";
import LoadingState from "@/components/career/LoadingState";
import { toast } from "sonner";
export default function CareerHistory() {
  const [reports, setReports] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [deleteId, setDeleteId] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const navigate = useNavigate();

  async function loadHistory() {
    try {
      const response = await historyApi.getHistory();
      setReports(response.data);
      console.log("History API:", response.data);
    } catch (error) {
      console.error(error);
      toast.error("Failed to load career history.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  async function confirmDelete() {
  try {
    await historyApi.deleteReport(deleteId);

    setReports((prev) =>
      prev.filter((report) => report.id !== deleteId)
    );

    setShowDeleteModal(false);
    setDeleteId(null);
  } catch (error) {
    console.error(error);
    toast.error("Failed to delete report.");
  }
}

    

  const filteredReports = reports.filter((report) =>
    report.career_goal?.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
  return (
    <div className="max-w-6xl mx-auto p-6">
      <LoadingState />
    </div>
  );
}
  console.log("Reports:", reports);
console.log("Filtered:", filteredReports);

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">

      <h1 className="text-3xl font-bold">
        Career History
      </h1>

      <div className="flex items-center justify-between">

        <input
          type="text"
          placeholder="Search reports..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border rounded-lg px-4 py-2 w-full sm:w-80"
        />

        <div className="font-medium">
          Total Reports: {filteredReports.length}
        </div>

      </div>

      {filteredReports.length === 0 ? (
  <CareerHistoryEmpty />
) : (
  <div className="space-y-5">
    {filteredReports.map((report) => (
      <div
        key={report.id}
        className="rounded-xl border p-6 shadow-sm"
      >
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold">
            🎯 {report.career_goal}
          </h2>

          <span
            className={`px-3 py-1 rounded-full text-sm ${
              report.source === "ai"
                ? "bg-green-100 text-green-700"
                : "bg-yellow-100 text-yellow-700"
            }`}
          >
            {(report.source || "unknown").toUpperCase()}
          </span>
        </div>

        <div className="mt-5 grid md:grid-cols-3 gap-4">
          <div>
            <div className="text-gray-500 text-sm">Readiness Score</div>
            <div className="text-2xl font-bold">
              {report.readiness_score}%
            </div>
          </div>

          <div>
            <div className="text-gray-500 text-sm">Best Match</div>
            <div>{report.best_match}</div>
          </div>

          <div>
            <div className="text-gray-500 text-sm">Generated</div>
            <div>
              {report.created_at
                ? new Date(report.created_at).toLocaleDateString()
                : "N/A"}
            </div>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={() =>
              navigate("/career", {
                state: {
                  report: report.report_json,
                },
              })
            }
            className="border rounded-lg px-4 py-2 hover:bg-gray-100"
          >
            View Report
          </button>

          <button
  onClick={() => {
    setDeleteId(report.id);
    setShowDeleteModal(true);
  }}
  className="border rounded-lg px-4 py-2 text-red-600 hover:bg-red-50"
>
  Delete
</button>
        </div>
      </div>
    ))}
  </div>
)}

<DeleteConfirmModal
  open={showDeleteModal}
  title="Delete Career Report"
  description="This career report will be permanently deleted. This action cannot be undone."
  onCancel={() => {
    setShowDeleteModal(false);
    setDeleteId(null);
    toast.success("Career report deleted successfully.");
  }}
  onConfirm={confirmDelete}
/>

    </div>
  );
}

