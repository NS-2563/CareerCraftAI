import { useQuery } from "@tanstack/react-query";
import resumeApi from "@/services/resumeApi";

export function useResumes(searchQuery = "", sortBy = "updated_at") {
  return useQuery({
    queryKey: ["resumes", searchQuery, sortBy],

    queryFn: async () => {
      let resumes = await resumeApi.listResumes();

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

