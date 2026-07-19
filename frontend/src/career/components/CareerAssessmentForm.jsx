import { useState } from "react";
import { MapPlus } from "lucide-react";

export default function CareerAssessmentForm({ onSubmit, loading = false }) {
  const [formData, setFormData] = useState({
    education: "",
    experience: "",
    skills: "",
    interests: "",
    goal: "",
    industry: "",
    location: "",
  });

  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));

    if (errors[e.target.name]) {
      setErrors((prev) => ({
        ...prev,
        [e.target.name]: "",
      }));
    }
  };

  const validate = () => {
    const newErrors = {};

    if (!formData.education.trim())
      newErrors.education = "Education is required";

    if (!formData.experience)
      newErrors.experience = "Experience is required";

    if (!formData.skills.trim())
      newErrors.skills = "Skills are required";

    if (!formData.interests.trim())
      newErrors.interests = "Interests are required";

    if (!formData.goal.trim())
      newErrors.goal = "Career goal is required";

    setErrors(newErrors);

    return Object.keys(newErrors).length === 0;
  };

  const submit = (e) => {
    e.preventDefault();

    if (!validate()) return;

    onSubmit(formData);
  };

  return (
    <div className="max-w-7xl mx-auto rounded-2xl border bg-card shadow-sm overflow-hidden">

      <div className="grid lg:grid-cols-[380px_1fr]">

        {/* LEFT PANEL */}

        <div className="border-r p-10 flex flex-col">

          <div className="flex items-start justify-between">

            <div>
              <h2 className="text-content-primary font-serif text-[40px] leading-[100%] font-extralight tracking-[-1.2px]">
                AI Career Assessment
              </h2>

              <p className="text-muted-foreground mt-4 leading-7">
                Tell us about yourself so our AI can analyze your profile,
                identify career opportunities, and generate a personalized
                roadmap for your future.
              </p>
            </div>

            

          </div>

          <div className="mt-12 space-y-5">

            <div className="flex gap-3">
              <span>✨</span>
              <div>
                <h4 className="font-semibold">
                  AI Powered
                </h4>
                <p className="text-sm text-muted-foreground">
                  Personalized career analysis.
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <span><MapPlus className="h-5 w-5" /></span>
              <div>
                <h4 className="font-semibold">
                  Career Roadmap
                </h4>
                <p className="text-sm text-muted-foreground">
                  Step-by-step learning plan.
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <span>💾</span>
              <div>
                <h4 className="font-semibold">
                  Saved Automatically
                </h4>
                <p className="text-sm text-muted-foreground">
                  Every assessment is stored in Career History.
                </p>
              </div>
            </div>

          </div>

        </div>

        {/* RIGHT PANEL */}

        <div className="p-10">

          <form onSubmit={submit} className="space-y-6">

            <div>
              <label className="font-medium">
                Current Education *
              </label>

              <input
                name="education"
                value={formData.education}
                onChange={handleChange}
                placeholder="MCA, B.Tech, BCA..."
                className="w-full mt-2 rounded-md border px-3 py-2"
              />

              {errors.education && (
                <p className="text-red-500 text-sm mt-1">
                  {errors.education}
                </p>
              )}
            </div>

            <div>
              <label className="font-medium">
                Experience Level *
              </label>

              <select
                name="experience"
                value={formData.experience}
                onChange={handleChange}
                className="w-full mt-2 rounded-md border px-3 py-2"
              >
                <option value="">Select</option>
                <option>Student</option>
                <option>Fresher</option>
                <option>0-2 Years</option>
                <option>2-5 Years</option>
                <option>5+ Years</option>
              </select>

              {errors.experience && (
                <p className="text-red-500 text-sm mt-1">
                  {errors.experience}
                </p>
              )}
            </div>

            <div>
              <label className="font-medium">
                Current Skills *
              </label>

              <textarea
                rows={4}
                name="skills"
                value={formData.skills}
                onChange={handleChange}
                placeholder="React, Python, SQL..."
                className="w-full mt-2 rounded-md border px-3 py-2"
              />

              {errors.skills && (
                <p className="text-red-500 text-sm mt-1">
                  {errors.skills}
                </p>
              )}
            </div>

            <div>
              <label className="font-medium">
                Interests *
              </label>

              <textarea
                rows={3}
                name="interests"
                value={formData.interests}
                onChange={handleChange}
                placeholder="AI, Web Development, Cloud..."
                className="w-full mt-2 rounded-md border px-3 py-2"
              />

              {errors.interests && (
                <p className="text-red-500 text-sm mt-1">
                  {errors.interests}
                </p>
              )}
            </div>

            <div>
              <label className="font-medium">
                Career Goal *
              </label>

              <input
                name="goal"
                value={formData.goal}
                onChange={handleChange}
                placeholder="Full Stack Developer"
                className="w-full mt-2 rounded-md border px-3 py-2"
              />

              {errors.goal && (
                <p className="text-red-500 text-sm mt-1">
                  {errors.goal}
                </p>
              )}
            </div>

            <div className="grid md:grid-cols-2 gap-6">

              <div>
                <label className="font-medium">
                  Preferred Industry
                </label>

                <input
                  name="industry"
                  value={formData.industry}
                  onChange={handleChange}
                  placeholder="Software, FinTech..."
                  className="w-full mt-2 rounded-md border px-3 py-2"
                />
              </div>

              <div>
                <label className="font-medium">
                  Preferred Location
                </label>

                <input
                  name="location"
                  value={formData.location}
                  onChange={handleChange}
                  placeholder="Bangalore"
                  className="w-full mt-2 rounded-md border px-3 py-2"
                />
              </div>

            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-md bg-primary px-4 py-3 text-primary-foreground font-medium disabled:opacity-50"
            >
              {loading
                ? "Generating Career Plan..."
                : "Generate Career Plan"}
            </button>

          </form>

        </div>

      </div>

    </div>
  );
}

