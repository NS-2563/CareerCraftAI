import { Input } from "@/components/ui/input";
import { useResumeContext } from "@/context/ResumeContext";

export default function PersonalInfo() {
  const { resumeData, updateField } = useResumeContext();
  const personal = resumeData.personal || {};
  return (
    <div className="rounded-xl border p-5 space-y-6">
      <h3 className="text-lg font-semibold">Personal Information</h3>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <label className="text-sm font-medium">First Name</label>
          <Input
            value={personal.firstName || ""}
            onChange={(e) =>
              updateField("personal", "firstName", e.target.value)
            }
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Last Name</label>
          <Input
            value={personal.lastName || ""}
            onChange={(e) =>
              updateField("personal", "lastName", e.target.value)
            }
          />
        </div>

        <div className="space-y-2 md:col-span-2">
          <label className="text-sm font-medium">Professional Title</label>
          <Input
            value={personal.title || ""}
            onChange={(e) =>
              updateField("personal", "title", e.target.value)
            }
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Email</label>
          <Input
            value={personal.email || ""}
            onChange={(e) =>
              updateField("personal", "email", e.target.value)
            }
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Phone</label>
          <Input
            value={personal.phone || ""}
            onChange={(e) =>
              updateField("personal", "phone", e.target.value)
            }
          />
        </div>

        <div className="space-y-2 md:col-span-2">
          <label className="text-sm font-medium">Location</label>
          <Input
            value={personal.location || ""}
            onChange={(e) =>
              updateField("personal", "location", e.target.value)
            }
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">LinkedIn</label>
          <Input
            value={personal.linkedin || ""}
            onChange={(e) =>
              updateField("personal", "linkedin", e.target.value)
            }
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">GitHub</label>
          <Input
            value={personal.github || ""}
            onChange={(e) =>
              updateField("personal", "github", e.target.value)
            }
          />
        </div>

        <div className="space-y-2 md:col-span-2">
          <label className="text-sm font-medium">Portfolio</label>
          <Input
            value={personal.portfolio || ""}
            onChange={(e) =>
              updateField("personal", "portfolio", e.target.value)
            }
          />
        </div>
      </div>
    </div>
  );
}