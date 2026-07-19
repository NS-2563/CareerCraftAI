export default function ProfessionalTemplate({ resumeData }) {
  const personal = resumeData.personal;

  const hasSkills = (resumeData.skills ?? []).some((x) => x?.name?.trim());
  const hasLanguages = (resumeData.languages ?? []).some((l) => l?.language?.trim());
  const hasCertifications = (resumeData.certifications ?? []).some((c) => c?.name?.trim());
  const hasExperience = (resumeData.experience ?? []).some(
    (x) => x?.company?.trim() || x?.position?.trim()
  );
  const hasProjects = (resumeData.projects ?? []).some((p) => p?.title?.trim());
  const hasEducation = (resumeData.education ?? []).some(
    (x) => x?.institution?.trim() || x?.degree?.trim()
  );

  return (
    <div className="rounded-xl shadow-sm">
      <div className="bg-white p-8 min-h-[900px]">
        <div className="mx-auto max-w-[210mm]">
          <div className="grid grid-cols-12 gap-6">

            {/* Left Column - Sidebar */}
            <aside className="col-span-4 bg-gray-50 p-4 -ml-4 min-h-[unset]">
              {/* Name */}
              <header className="pb-4 border-b border-gray-300">
                <h1 className="text-xl font-bold text-gray-900 leading-tight">
                  {personal.firstName} {personal.lastName}
                </h1>
                {personal.title && (
                  <p className="text-sm text-gray-600 mt-2">{personal.title}</p>
                )}
              </header>

              {/* Contact */}
              <section className="pt-4 border-b border-gray-300">
                <h2 className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                  Contact
                </h2>
                <div className="mt-2 space-y-1 text-xs text-gray-700">
                  {personal.email && <div>{personal.email}</div>}
                  {personal.phone && <div>{personal.phone}</div>}
                  {personal.location && <div>{personal.location}</div>}
                </div>
              </section>

              {/* Skills */}
              {hasSkills && (
                <section className="pt-4 border-b border-gray-300">
                  <h2 className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                    Skills
                  </h2>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {(resumeData.skills ?? [])
                      .filter((x) => x?.name?.trim())
                      .map((skill, idx) => (
                        <span
                          key={idx}
                          className="text-xs bg-gray-200 text-gray-800 px-2 py-0.5 rounded"
                        >
                          {skill.name.trim()}
                        </span>
                      ))}
                  </div>
                </section>
              )}

              {/* Languages */}
              {hasLanguages && (
                <section className="pt-4 border-b border-gray-300">
                  <h2 className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                    Languages
                  </h2>
                  <div className="mt-2 space-y-1 text-xs text-gray-700">
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

              {/* Certifications */}
              {hasCertifications && (
                <section className="pt-4">
                  <h2 className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                    Certifications
                  </h2>
                  <div className="mt-2 space-y-2 text-xs text-gray-700">
                    {(resumeData.certifications ?? [])
                      .filter((c) => c?.name?.trim())
                      .map((c, idx) => (
                        <div key={idx}>
                          <div className="font-medium">{c.name}</div>
                          {c.issuer && (
                            <div className="text-gray-600">{c.issuer}</div>
                          )}
                        </div>
                      ))}
                  </div>
                </section>
              )}
            </aside>

            {/* Right Column - Main Content */}
            <div className="col-span-8">
              {/* Summary */}
              {resumeData.summary && (
                <section className="pb-4 border-b border-gray-200">
                  <h2 className="text-lg font-semibold text-gray-900">
                    Professional Summary
                  </h2>
                  <p className="text-sm text-gray-700 mt-2 leading-relaxed">
                    {resumeData.summary}
                  </p>
                </section>
              )}

              {/* Experience */}
              {hasExperience && (
                <section className="pt-4">
                  <h2 className="text-lg font-semibold text-gray-900">
                    Professional Experience
                  </h2>
                  <div className="mt-4 space-y-4">
                    {(resumeData.experience ?? [])
                      .filter((x) => x?.company?.trim() || x?.position?.trim())
                      .map((x, idx) => (
                        <div key={idx}>
                          <div className="flex justify-between items-start">
                            <div>
                              <div className="font-semibold text-gray-900">
                                {x.company}
                              </div>
                              <div className="text-sm text-gray-600">
                                {x.position}
                                {x.location && ` | ${x.location}`}
                              </div>
                            </div>
                            <div className="text-sm text-gray-600">
                              {x.startDate}
                              {x.startDate && x.endDate && " - "}
                              {x.endDate}
                              {x.current && " - Present"}
                            </div>
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

              {/* Projects */}
              {hasProjects && (
                <section className="pt-4">
                  <h2 className="text-lg font-semibold text-gray-900">
                    Key Projects
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

              {/* Education */}
              {hasEducation && (
                <section className="pt-4">
                  <h2 className="text-lg font-semibold text-gray-900">
                    Education
                  </h2>
                  <div className="mt-4 space-y-4">
                    {(resumeData.education ?? [])
                      .filter((x) => x?.institution?.trim() || x?.degree?.trim())
                      .map((edu, idx) => (
                        <div key={idx}>
                          <div className="font-semibold text-gray-900">{edu.degree}</div>
                          <div className="text-sm text-gray-600">
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
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}

