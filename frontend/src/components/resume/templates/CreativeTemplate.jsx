import { MapPin, Mail, Phone, Link2, Globe, Code } from "lucide-react";

export default function CreativeTemplate({ resumeData }) {
  const personal = resumeData.personal;

  const hasExperience = (resumeData.experience ?? []).some(
    (x) => x?.company?.trim() || x?.position?.trim()
  );
  const hasEducation = (resumeData.education ?? []).some(
    (x) => x?.institution?.trim() || x?.degree?.trim()
  );
  const hasSkills = (resumeData.skills ?? []).some((x) => x?.name?.trim());
  const hasProjects = (resumeData.projects ?? []).some((p) => p?.title?.trim());
  const hasCertifications = (resumeData.certifications ?? []).some((c) => c?.name?.trim());
  const hasLanguages = (resumeData.languages ?? []).some((l) => l?.language?.trim());

  return (
    <div className="rounded-xl shadow-sm">
      <div className="bg-white p-8 min-h-[900px]">
        <div className="mx-auto max-w-[210mm]">

          {/* Header - Modern gradient accent */}
          <header className="pb-6 border-b-2 border-l-4 border-purple-600 bg-gradient-to-r from-purple-50 to-transparent pl-4">
            <h1 className="text-3xl font-bold text-gray-900">
              {personal.firstName}{" "}
              <span className="text-purple-700">{personal.lastName}</span>
            </h1>
            {personal.title && (
              <p className="text-lg text-purple-600 mt-1 font-medium">
                {personal.title}
              </p>
            )}

            {/* Contact Icons */}
            <div className="flex flex-wrap gap-4 mt-4">
              {personal.email && (
                <div className="flex items-center gap-1 text-sm text-gray-600">
                  <Mail className="w-4 h-4 text-purple-600" />
                  {personal.email}
                </div>
              )}
              {personal.phone && (
                <div className="flex items-center gap-1 text-sm text-gray-600">
                  <Phone className="w-4 h-4 text-purple-600" />
                  {personal.phone}
                </div>
              )}
              {personal.location && (
                <div className="flex items-center gap-1 text-sm text-gray-600">
                  <MapPin className="w-4 h-4 text-purple-600" />
                  {personal.location}
                </div>
              )}
            </div>

            {/* Social Links */}
            <div className="flex flex-wrap gap-4 mt-2">
              {personal.linkedin && (
                <div className="flex items-center gap-1 text-sm text-purple-600">
                  <Link2 className="w-4 h-4" />
                  {personal.linkedin}
                </div>
              )}
              {personal.github && (
                <div className="flex items-center gap-1 text-sm text-purple-600">
                  <Code className="w-4 h-4" />
                  {personal.github}
                </div>
              )}
              {personal.portfolio && (
                <div className="flex items-center gap-1 text-sm text-purple-600">
                  <Globe className="w-4 h-4" />
                  {personal.portfolio}
                </div>
              )}
            </div>
          </header>

          {/* Summary */}
          {resumeData.summary && (
            <section className="mt-6">
              <h2 className="text-lg font-bold text-gray-900">
                About Me
              </h2>
              <p className="text-sm text-gray-700 mt-2 leading-relaxed">
                {resumeData.summary}
              </p>
            </section>
          )}

          {/* Experience - Timeline style */}
          {hasExperience && (
            <section className="mt-6">
              <h2 className="text-lg font-bold text-purple-700">
                Experience
              </h2>
              <div className="mt-4 space-y-6">
                {(resumeData.experience ?? [])
                  .filter((x) => x?.company?.trim() || x?.position?.trim())
                  .map((x, idx) => (
                    <div key={idx} className="relative pl-6">
                      {/* Timeline dot */}
                      <div className="absolute left-0 top-1 w-3 h-3 bg-purple-600 rounded-full ring-4 ring-purple-100" />
                      {/* Timeline line */}
                      {idx !== ((resumeData.experience ?? []).filter(
                        (e) => e?.company?.trim() || e?.position?.trim()
                      ).length - 1) && (
                        <div className="absolute left-1 top-4 w-0.5 h-full bg-purple-200" />
                      )}

                      <div className="text-sm text-gray-500 mb-1">
                        {x.startDate}
                        {x.startDate && x.endDate && " - "}
                        {x.endDate}
                        {x.current && " - Present"}
                      </div>
                      <div className="font-semibold text-gray-900 text-base">
                        {x.position}
                      </div>
                      <div className="text-purple-600 font-medium">
                        {x.company}
                        {x.location && ` | ${x.location}`}
                      </div>
                      {x.description?.trim() && (
                        <p className="text-sm text-gray-700 mt-2">
                          {x.description}
                        </p>
                      )}
                    </div>
                  ))}
              </div>
            </section>
          )}

          {/* Education */}
          {hasEducation && (
            <section className="mt-6">
              <h2 className="text-lg font-bold text-purple-700">
                Education
              </h2>
              <div className="mt-4 space-y-4">
                {(resumeData.education ?? [])
                  .filter((x) => x?.institution?.trim() || x?.degree?.trim())
                  .map((edu, idx) => (
                    <div key={idx} className="relative pl-6">
                      <div className="absolute left-0 top-1 w-3 h-3 bg-purple-600 rounded-full ring-4 ring-purple-100" />
                      <div className="font-semibold text-gray-900">
                        {edu.degree}
                      </div>
                      <div className="text-purple-600">
                        {edu.institution}
                        {edu.fieldOfStudy && ` in ${edu.fieldOfStudy}`}
                      </div>
                      <div className="text-sm text-gray-600">
  {edu.current ? (
    <>
      {edu.startDate}
      {edu.startDate && " - "}
      Present
    </>
  ) : (
    <>
      {edu.startDate}
      {edu.startDate && edu.endDate && " - "}
      {edu.endDate}
    </>
  )}

  {edu.gpa && ` | GPA: ${edu.gpa}`}
</div>
                    </div>
                  ))}
              </div>
            </section>
          )}

          {/* Skills - Modern tags */}
          {hasSkills && (
            <section className="mt-6">
              <h2 className="text-lg font-bold text-purple-700">
                Skills
              </h2>
              <div className="mt-3 flex flex-wrap gap-2">
                {(resumeData.skills ?? [])
                  .filter((x) => x?.name?.trim())
                  .map((skill, idx) => (
                    <span
                      key={idx}
                      className="bg-gradient-to-r from-purple-100 to-pink-100 text-purple-800 px-3 py-1.5 text-sm rounded-lg font-medium"
                    >
                      {skill.name.trim()}
                    </span>
                  ))}
              </div>
            </section>
          )}

          {/* Projects */}
          {hasProjects && (
            <section className="mt-6">
              <h2 className="text-lg font-bold text-purple-700">
                Projects
              </h2>
              <div className="mt-4 grid gap-4">
                {(resumeData.projects ?? [])
                  .filter((p) => p?.title?.trim())
                  .map((p, idx) => (
                    <div
                      key={idx}
                      className="bg-gradient-to-r from-purple-50 to-transparent p-3 rounded-lg border-l-4 border-purple-400"
                    >
                      <div className="font-semibold text-gray-900">
                        {p.title}
                      </div>
                      {p.techStack && (
                        <div className="text-sm text-purple-600 mt-1">
                          {p.techStack}
                        </div>
                      )}
                      {p.description?.trim() && (
                        <p className="text-sm text-gray-700 mt-2">
                          {p.description}
                        </p>
                      )}
                      {(p.github || p.liveDemo) && (
                        <div className="flex gap-3 mt-2 text-sm text-purple-600">
                          {p.github && <span>GitHub: {p.github}</span>}
                          {p.liveDemo && <span>Demo: {p.liveDemo}</span>}
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            </section>
          )}

          {/* Certifications */}
          {hasCertifications && (
            <section className="mt-6">
              <h2 className="text-lg font-bold text-purple-700">
                Certifications
              </h2>
              <div className="mt-3 grid gap-2">
                {(resumeData.certifications ?? [])
                  .filter((c) => c?.name?.trim())
                  .map((c, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 text-sm"
                    >
                      <span className="w-2 h-2 bg-purple-500 rounded-full" />
                      <span className="font-medium text-gray-900">{c.name}</span>
                      {c.issuer && (
                        <span className="text-gray-500">- {c.issuer}</span>
                      )}
                      {c.issueDate && (
                        <span className="text-gray-400">({c.issueDate})</span>
                      )}
                    </div>
                  ))}
              </div>
            </section>
          )}

          {/* Languages */}
          {hasLanguages && (
            <section className="mt-6">
              <h2 className="text-lg font-bold text-purple-700">
                Languages
              </h2>
              <div className="mt-3 flex flex-wrap gap-4">
                {(resumeData.languages ?? [])
                  .filter((l) => l?.language?.trim())
                  .map((l, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 text-sm"
                    >
                      <span className="w-2 h-2 bg-purple-500 rounded-full" />
                      <span className="font-medium text-gray-900">
                        {l.language.trim()}
                      </span>
                      {l.proficiency && (
                        <span className="text-gray-500">
                          ({l.proficiency})
                        </span>
                      )}
                    </div>
                  ))}
              </div>
            </section>
          )}

        </div>
      </div>
    </div>
  );
}

