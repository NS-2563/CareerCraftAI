export default function CorporateTemplate({ resumeData }) {
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
  const hasInterests = (resumeData.interests ?? []).some((i) => i?.name?.trim());

  return (
    <div className="rounded-xl shadow-sm">
      <div className="bg-white p-8 min-h-[900px]">
        <div className="mx-auto max-w-[210mm]">

          {/* Header - Blue accent, larger name */}
          <header className="pb-6 border-b-2 border-blue-800">
            <h1 className="text-3xl font-bold text-blue-900">
              {personal.firstName} {personal.lastName}
            </h1>
            {personal.title && (
              <p className="text-lg text-blue-700 mt-1">{personal.title}</p>
            )}
            <div className="text-sm text-gray-600 mt-3 flex flex-wrap gap-x-4 gap-y-1">
              {personal.email && <span>{personal.email}</span>}
              {personal.phone && <span>{personal.phone}</span>}
              {personal.location && <span>{personal.location}</span>}
            </div>
          </header>

          {/* Links */}
          {(personal.linkedin || personal.github || personal.portfolio) && (
            <div className="py-3 border-b border-gray-200 text-sm text-gray-700">
              {personal.linkedin && <span className="mr-4">LinkedIn: {personal.linkedin}</span>}
              {personal.github && <span className="mr-4">GitHub: {personal.github}</span>}
              {personal.portfolio && <span>Portfolio: {personal.portfolio}</span>}
            </div>
          )}

          {/* Summary */}
          {resumeData.summary && (
            <section className="mt-6">
              <h2 className="text-lg font-bold text-blue-900 flex items-center gap-2">
                <span className="w-2 h-2 bg-blue-800 rounded-full" />
                Professional Summary
              </h2>
              <p className="text-sm text-gray-700 mt-3 leading-relaxed">
                {resumeData.summary}
              </p>
            </section>
          )}

          {/* Experience */}
          {hasExperience && (
            <section className="mt-6">
              <h2 className="text-lg font-bold text-blue-900 flex items-center gap-2">
                <span className="w-2 h-2 bg-blue-800 rounded-full" />
                Professional Experience
              </h2>
              <div className="mt-4 space-y-5">
                {(resumeData.experience ?? [])
                  .filter((x) => x?.company?.trim() || x?.position?.trim())
                  .map((x, idx) => (
                    <div key={idx} className="relative pl-4 border-l-2 border-blue-200">
                      <div className="absolute -left-1.5 top-0 w-3 h-3 bg-blue-800 rounded-full" />
                      <div className="font-semibold text-gray-900">
                        {x.company}
                      </div>
                      <div className="text-sm text-blue-700">
                        {x.position}
                        {x.location && ` | ${x.location}`}
                      </div>
                      <div className="text-sm text-gray-600">
                        {x.startDate}
                        {x.startDate && x.endDate && " - "}
                        {x.endDate}
                        {x.current && " - Present"}
                      </div>
                      {x.description?.trim() && (
                        <p className="text-sm text-gray-700 mt-2">{x.description}</p>
                      )}
                    </div>
                  ))}
              </div>
            </section>
          )}

          {/* Education */}
          {hasEducation && (
            <section className="mt-6">
              <h2 className="text-lg font-bold text-blue-900 flex items-center gap-2">
                <span className="w-2 h-2 bg-blue-800 rounded-full" />
                Education
              </h2>
              <div className="mt-4 space-y-5">
                {(resumeData.education ?? [])
                  .filter((x) => x?.institution?.trim() || x?.degree?.trim())
                  .map((edu, idx) => (
                    <div
                      key={idx}
                      className="relative pl-4 border-l-2 border-blue-200"
                    >
                      <div className="absolute -left-1.5 top-0 w-3 h-3 bg-blue-800 rounded-full" />
                      <div className="font-semibold text-gray-900">
                        {edu.degree}
                      </div>
                      <div className="text-sm text-gray-700">
                        {edu.institution}
                        {edu.fieldOfStudy && ` - ${edu.fieldOfStudy}`}
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

          {/* Skills */}
          {hasSkills && (
            <section className="mt-6">
              <h2 className="text-lg font-bold text-blue-900 flex items-center gap-2">
                <span className="w-2 h-2 bg-blue-800 rounded-full" />
                Core Competencies
              </h2>
              <div className="mt-3 flex flex-wrap gap-2">
                {(resumeData.skills ?? [])
                  .filter((x) => x?.name?.trim())
                  .map((skill, idx) => (
                    <span
                      key={idx}
                      className="bg-blue-100 text-blue-800 px-3 py-1 text-sm rounded-full font-medium"
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
              <h2 className="text-lg font-bold text-blue-900 flex items-center gap-2">
                <span className="w-2 h-2 bg-blue-800 rounded-full" />
                Notable Projects
              </h2>
              <div className="mt-4 space-y-4">
                {(resumeData.projects ?? [])
                  .filter((p) => p?.title?.trim())
                  .map((p, idx) => (
                    <div key={idx}>
                      <div className="font-semibold text-gray-900">{p.title}</div>
                      {p.techStack && (
                        <div className="text-sm text-gray-600">{p.techStack}</div>
                      )}
                      {p.description?.trim() && (
                        <p className="text-sm text-gray-700 mt-1">{p.description}</p>
                      )}
                    </div>
                  ))}
              </div>
            </section>
          )}

          {/* Certifications */}
          {hasCertifications && (
            <section className="mt-6">
              <h2 className="text-lg font-bold text-blue-900 flex items-center gap-2">
                <span className="w-2 h-2 bg-blue-800 rounded-full" />
                Certifications
              </h2>
              <div className="mt-3 space-y-2">
                {(resumeData.certifications ?? [])
                  .filter((c) => c?.name?.trim())
                  .map((c, idx) => (
                    <div key={idx} className="text-sm text-gray-700">
                      <span className="font-medium">{c.name}</span>
                      {c.issuer && ` - ${c.issuer}`}
                      {c.issueDate && ` (${c.issueDate})`}
                    </div>
                  ))}
              </div>
            </section>
          )}

          {/* Languages */}
          {hasLanguages && (
            <section className="mt-6">
              <h2 className="text-lg font-bold text-blue-900 flex items-center gap-2">
                <span className="w-2 h-2 bg-blue-800 rounded-full" />
                Languages
              </h2>
              <div className="mt-3 space-y-1 text-sm text-gray-700">
                {(resumeData.languages ?? [])
                  .filter((l) => l?.language?.trim())
                  .map((l, idx) => (
                    <div key={idx}>
                      {l.language.trim()}
                      {l.proficiency && ` - ${l.proficiency}`}
                    </div>
                  ))}
              </div>
            </section>
          )}

          {/* Interests */}
          {hasInterests && (
            <section className="mt-6">
              <h2 className="text-lg font-bold text-blue-900 flex items-center gap-2">
                <span className="w-2 h-2 bg-blue-800 rounded-full" />
                Interests
              </h2>
              <p className="text-sm text-gray-700 mt-2">
                {(resumeData.interests ?? [])
                  .filter((i) => i?.name?.trim())
                  .map((i) => i.name.trim())
                  .join(", ")}
              </p>
            </section>
          )}

        </div>
      </div>
    </div>
  );
}