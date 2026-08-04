import { useQuery } from "@tanstack/react-query";
import resumeApi from "@/services/resumeApi";

export function useResumes(
  searchQuery = "",
  sortBy = "updated_at",
  activeFilter = "all"
) {
  return useQuery({
    queryKey: ["resumes", searchQuery, sortBy, activeFilter],

    queryFn: async () => {
      let archived = null;

if (activeFilter === "archived") {
  archived = true;
} else if (
  activeFilter === "all" ||
  activeFilter === "draft" ||
  activeFilter === "completed"
) {
  archived = false;
}

let resumes = await resumeApi.listResumes(archived);
      

      if (searchQuery) {
        resumes = resumes.filter((r) =>
          r.name.toLowerCase().includes(searchQuery.toLowerCase())
        );
      }

      if (sortBy === "name") {
        resumes = [...resumes].sort((a, b) =>
          a.name.localeCompare(b.name)
        );
      }

      return resumes;
    },
  });
}



