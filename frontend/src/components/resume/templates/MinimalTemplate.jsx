export default function MinimalTemplate({ resumeData }) {
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

          {/* Header - Very compact */}
          <header className="pb-4">
            <h1 className="text-2xl font-bold text-black">
              {personal.firstName} {personal.lastName}
            </h1>
            {personal.title && (
              <p className="text-base text-gray-700 mt-1">{personal.title}</p>
            )}
            <div className="text-sm text-gray-600 mt-2 flex flex-wrap gap-x-4 gap-y-1">
              {personal.email && <span>{personal.email}</span>}
              {personal.phone && <span>{personal.phone}</span>}
              {personal.location && <span>{personal.location}</span>}
            </div>
          </header>

          {/* Summary */}
          {resumeData.summary && (
            <section className="mt-4">
              <h2 className="text-sm font-bold text-black uppercase tracking-wider border-b border-black pb-1">
                Summary
              </h2>
              <p className="text-sm text-gray-800 mt-2 leading-relaxed">
                {resumeData.summary}
              </p>
            </section>
          )}

          {/* Experience */}
          {hasExperience && (
            <section className="mt-4">
              <h2 className="text-sm font-bold text-black uppercase tracking-wider border-b border-black pb-1">
                Experience
              </h2>
              <div className="mt-3 space-y-3">
                {(resumeData.experience ?? []).filter(
                  (x) => x?.company?.trim() || x?.position?.trim()
                ).map((x, idx) => (
                  <div key={idx}>
                    <div className="text-sm font-bold text-black">
                      {x.company}
                      {x.position && ` - ${x.position}`}
                    </div>
                    <div className="text-sm text-gray-600">
                      {x.startDate}
                      {x.startDate && x.endDate && " - "}
                      {x.endDate}
                      {x.current && " - Present"}
                    </div>
                    {x.description?.trim() && (
                      <p className="text-sm text-gray-800 mt-1">{x.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Education */}
          {hasEducation && (
            <section className="mt-4">
              <h2 className="text-sm font-bold text-black uppercase tracking-wider border-b border-black pb-1">
                Education
              </h2>
              <div className="mt-3 space-y-3">
                {(resumeData.education ?? []).filter(
                  (x) => x?.institution?.trim() || x?.degree?.trim()
                ).map((edu, idx) => (
                  <div key={idx}>
                    <div className="text-sm font-bold text-black">{edu.degree}</div>
                    <div className="text-sm text-gray-600">
                      {edu.institution}
                      {edu.fieldOfStudy && `, ${edu.fieldOfStudy}`}
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
            <section className="mt-4">
              <h2 className="text-sm font-bold text-black uppercase tracking-wider border-b border-black pb-1">
                Skills
              </h2>
              <p className="text-sm text-gray-800 mt-2">
                {(resumeData.skills ?? [])
                  .filter((x) => x?.name?.trim())
                  .map((s) => s.name.trim())
                  .join(", ")}
              </p>
            </section>
          )}

          {/* Projects */}
          {hasProjects && (
            <section className="mt-4">
              <h2 className="text-sm font-bold text-black uppercase tracking-wider border-b border-black pb-1">
                Projects
              </h2>
              <div className="mt-3 space-y-3">
                {(resumeData.projects ?? [])
                  .filter((p) => p?.title?.trim())
                  .map((p, idx) => (
                    <div key={idx}>
                      <div className="text-sm font-bold text-black">{p.title}</div>
                      {p.techStack && (
                        <div className="text-sm text-gray-600">{p.techStack}</div>
                      )}
                      {p.description?.trim() && (
                        <p className="text-sm text-gray-800">{p.description}</p>
                      )}
                    </div>
                  ))}
              </div>
            </section>
          )}

          {/* Certifications */}
          {hasCertifications && (
            <section className="mt-4">
              <h2 className="text-sm font-bold text-black uppercase tracking-wider border-b border-black pb-1">
                Certifications
              </h2>
              <div className="mt-2 text-sm text-gray-800">
                {(resumeData.certifications ?? [])
                  .filter((c) => c?.name?.trim())
                  .map((c) => (
                    <div key={c.name}>
                      {c.name}
                      {c.issuer && ` - ${c.issuer}`}
                      {c.issueDate && ` (${c.issueDate})`}
                    </div>
                  ))}
              </div>
            </section>
          )}

          {/* Languages */}
          {hasLanguages && (
            <section className="mt-4">
              <h2 className="text-sm font-bold text-black uppercase tracking-wider border-b border-black pb-1">
                Languages
              </h2>
              <p className="text-sm text-gray-800 mt-2">
                {(resumeData.languages ?? [])
                  .filter((l) => l?.language?.trim())
                  .map((l) => l.language.trim())
                  .join(", ")}
              </p>
            </section>
          )}

        </div>
      </div>
    </div>
  );
}