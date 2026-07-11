import DashboardToolbarPresentational from "@/components/dashboard/DashboardToolbarPresentational";

// Pure UI wrapper to keep existing import paths stable.
export default function DashboardToolbar(props) {
  return <DashboardToolbarPresentational {...props} />;
}

