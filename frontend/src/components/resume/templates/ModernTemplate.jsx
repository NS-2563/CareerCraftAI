export default function ModernTemplate({ resumeData }) {
  const personal = resumeData.personal;

  return (
    <div className="rounded-xl shadow-sm">
      <div className="bg-white p-8 min-h-[900px]">
        {/* A4-ish container */}
        <div className="mx-auto max-w-[210mm]">

          {/* PERSONAL */}
          <header className="text-center pb-6 border-b border-gray-200">
            <h1 className="text-3xl font-bold leading-tight">
              {personal.firstName} {personal.lastName}
            </h1>

            <p className="mt-2 text-sm text-gray-600">
              {personal.title}
            </p>

            {(personal.email || personal.phone || personal.location) && (
              <div className="mt-4 text-sm text-gray-700 space-y-1">
                {personal.email && <div>{personal.email}</div>}
                {personal.phone && <div>{personal.phone}</div>}
                {personal.location && <div>{personal.location}</div>}
              </div>
            )}
          </header>


          {/* SUMMARY */}
          {resumeData.summary && (
            <section className="pt-6 space-y-4">
              <div className="flex items-center gap-3">
                <h2 className="text-lg font-semibold text-gray-900">
                  Summary
                </h2>
                <div className="h-px flex-1 bg-gray-200" />
              </div>

              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                {resumeData.summary}
              </p>
            </section>
          )}



          {/* LINKS */}
          {(personal.linkedin ||
            personal.github ||
            personal.portfolio) && (
            <section className="pt-6">
              <div className="grid gap-1 text-sm text-gray-800">
                {personal.linkedin && (
                  <div>
                    LinkedIn: {personal.linkedin}
                  </div>
                )}

                {personal.github && (
                  <div>
                    GitHub: {personal.github}
                  </div>
                )}

                {personal.portfolio && (
                  <div>
                    Portfolio: {personal.portfolio}
                  </div>
                )}
              </div>
            </section>
          )}



          {/* EXPERIENCE */}
          <section className="pt-6 space-y-4">
            {(() => {
              const experiences = resumeData.experience ?? [];

              const visibleExperiences = experiences.filter((x) => {
                return (
                  x?.company?.trim() ||
                  x?.position?.trim() ||
                  x?.description?.trim()
                );
              });


              if (!visibleExperiences.length) return null;


              return (
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-lg font-semibold text-gray-900">
                      Experience
                    </h2>

                    <div className="h-px flex-1 bg-gray-200" />
                  </div>

                  <div className="mt-4 space-y-5">

                    {visibleExperiences.map((x, idx) => {

                      const dateRange = x.current
                        ? `${x.startDate || ""} - Present`
                        : `${x.startDate || ""}${
                            x.startDate ? " - " : ""
                          }${x.endDate || ""}`;


                      return (
                        <div
                          key={idx}
                          className="space-y-2"
                        >

                          <div className="font-semibold text-gray-900">
                            {x.company}
                          </div>


                          <div className="text-sm text-gray-800">

                            {x.position && (
                              <span>
                                {x.position}
                              </span>
                            )}

                            {x.location && (
                              <span>
                                {x.position && " • "}
                                {x.location}
                              </span>
                            )}

                          </div>


                          {dateRange.trim() && (
                            <div className="text-sm text-gray-700">
                              {dateRange}
                            </div>
                          )}


                          {x.description?.trim() && (
                            <div className="text-sm text-gray-700 whitespace-pre-wrap">
                              {x.description}
                            </div>
                          )}


                          <div className="border-b border-gray-200" />

                        </div>
                      );
                    })}

                  </div>
                </div>
              );
            })()}
          </section>




          {/* EDUCATION */}
          <section className="pt-6 space-y-4">
            {(() => {

              const educations = resumeData.education ?? [];


              const visibleEducations = educations.filter((x) => {
                return (
                  x?.institution?.trim() ||
                  x?.degree?.trim() ||
                  x?.description?.trim()
                );
              });


              if (!visibleEducations.length) return null;



              return (
                <div>

                  <div className="flex items-center gap-3">
                    <h2 className="text-lg font-semibold text-gray-900">
                      Education
                    </h2>

                    <div className="h-px flex-1 bg-gray-200" />
                  </div>


                  <div className="mt-4 space-y-5">

                    {visibleEducations.map((edu, idx) => {


                      const dateRange = edu.current
                        ? `${edu.startDate || ""} - Present`
                        : `${edu.startDate || ""}${
                            edu.startDate ? " - " : ""
                          }${edu.endDate || ""}`;



                      return (
                        <div
                          key={idx}
                          className="space-y-2"
                        >

                          {/* Degree */}
                          <div className="font-semibold text-gray-900">
                            {edu.degree}
                          </div>


                          {/* Institution */}
                          <div className="text-sm text-gray-800">

                            {edu.institution}


                            {edu.fieldOfStudy && (
                              <span>
                                {" • "}
                                {edu.fieldOfStudy}
                              </span>
                            )}


                            {edu.location && (
                              <span>
                                {" • "}
                                {edu.location}
                              </span>
                            )}

                          </div>



                          {dateRange.trim() && (
                            <div className="text-sm text-gray-700">
                              {dateRange}
                            </div>
                          )}



                          {edu.gpa && (
                            <div className="text-sm text-gray-700">
                              GPA: {edu.gpa}
                            </div>
                          )}



                          {edu.description?.trim() && (
                            <div className="text-sm text-gray-700 whitespace-pre-wrap">
                              {edu.description}
                            </div>
                          )}



                          <div className="border-b border-gray-200" />

                        </div>
                      );
                    })}

                  </div>

                </div>
              );

            })()}
          </section>


          {/* SKILLS */}
          <section className="pt-6 space-y-4">
            {(() => {
              const skills = resumeData.skills ?? [];

              const visibleSkills = skills.filter((x) => {
                return Boolean(x?.name?.trim() || x?.category?.trim());
              });

              if (!visibleSkills.length) return null;

              return (
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-lg font-semibold text-gray-900">Skills</h2>
                    <div className="h-px flex-1 bg-gray-200" />
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {visibleSkills.map((skill, idx) => {
                      const name = skill?.name?.trim();
                      const category = skill?.category?.trim();
                      if (!name) return null;

                      return (
                        <div
                          key={idx}
                          className="inline-flex items-center rounded-full bg-gray-100 px-3 py-1 text-sm text-gray-800"
                        >
                          {category ? (
                            <span>
                              {name} <span className="text-gray-500">•</span> {category}
                            </span>
                          ) : (
                            <span>{name}</span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })()}
          </section>

          {/* PROJECTS */}
          <section className="pt-6 space-y-4">
            {(() => {
              const projects = resumeData.projects ?? [];

              const visibleProjects = projects.filter((p) => {
                const title = p?.title?.trim();
                const techStack = p?.techStack?.trim();
                const description = p?.description?.trim();
                const github = p?.github?.trim();
                const liveDemo = p?.liveDemo?.trim();
                return Boolean(title || techStack || description || github || liveDemo);
              });

              if (!visibleProjects.length) return null;

              return (
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-lg font-semibold text-gray-900">Projects</h2>
                    <div className="h-px flex-1 bg-gray-200" />
                  </div>

                  <div className="mt-4 space-y-5">
                    {visibleProjects.map((p, idx) => {
                      const title = p?.title?.trim();
                      const techStack = p?.techStack?.trim();
                      const github = p?.github?.trim();
                      const liveDemo = p?.liveDemo?.trim();
                      const description = p?.description?.trim();

                      return (
                        <div key={idx} className="space-y-2">
                          {title && <div className="font-semibold text-gray-900">{title}</div>}

                          {techStack && (
                            <div className="text-sm text-gray-800">{techStack}</div>
                          )}

                          {description && (
                            <div className="text-sm text-gray-700 whitespace-pre-wrap">{description}</div>
                          )}

                          {(github || liveDemo) && (
                            <div className="text-sm text-gray-700">
                              {github && <div>GitHub: {github}</div>}
                              {liveDemo && <div>Live Demo: {liveDemo}</div>}
                            </div>
                          )}

                          <div className="border-b border-gray-200" />
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })()}
          </section>

          {/* CERTIFICATIONS */}
          <section className="pt-6 space-y-4">
            {(() => {
              const certifications = resumeData.certifications ?? [];

              const visibleCertifications = certifications.filter((c) => {
                const name = c?.name?.trim();
                const issuer = c?.issuer?.trim();
                const issueDate = c?.issueDate?.trim();
                const credentialUrl = c?.credentialUrl?.trim();
                return Boolean(name || issuer || issueDate || credentialUrl);
              });

              if (!visibleCertifications.length) return null;

              return (
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-lg font-semibold text-gray-900">Certifications</h2>
                    <div className="h-px flex-1 bg-gray-200" />
                  </div>

                  <div className="mt-4 space-y-5">
                    {visibleCertifications.map((c, idx) => {
                      const name = c?.name?.trim();
                      const issuer = c?.issuer?.trim();
                      const issueDate = c?.issueDate?.trim();
                      const credentialUrl = c?.credentialUrl?.trim();

                      return (
                        <div key={idx} className="space-y-2">
                          {name && <div className="font-semibold text-gray-900">{name}</div>}
                          {issuer && <div className="text-sm text-gray-800">{issuer}</div>}
                          {issueDate && <div className="text-sm text-gray-700">{issueDate}</div>}

                          {credentialUrl && (
                            <div className="text-sm text-gray-700">
                              <a
                                href={credentialUrl}
                                target="_blank"
                                rel="noreferrer"
                                className="underline"
                              >
                                Credential: {credentialUrl}
                              </a>
                            </div>
                          )}

                          <div className="border-b border-gray-200" />
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })()}
          </section>

          {/* LANGUAGES */}
          <section className="pt-6 space-y-4">
            {(() => {
              const languages = resumeData.languages ?? [];

              const visibleLanguages = languages.filter((l) => {
                const language = l?.language?.trim();
                const proficiency = l?.proficiency?.trim();
                return Boolean(language || proficiency);
              });

              if (!visibleLanguages.length) return null;

              return (
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-lg font-semibold text-gray-900">Languages</h2>
                    <div className="h-px flex-1 bg-gray-200" />
                  </div>

                  <div className="mt-4 space-y-2">
                    {visibleLanguages.map((l, idx) => {
                      const language = l?.language?.trim();
                      const proficiency = l?.proficiency?.trim();
                      if (!language) return null;

                      return (
                        <div key={idx} className="text-sm text-gray-800">
                          {language}
                          {proficiency && <span className="text-gray-500"> — {proficiency}</span>}
                          <div className="border-b border-gray-200 mt-2" />
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })()}
          </section>

          {/* INTERESTS */}
          {(() => {
            const interests = resumeData.interests ?? [];
            const visibleInterests = interests.filter((i) => Boolean(i?.name?.trim()));
            if (!visibleInterests.length) return null;

            return (
              <section className="pt-6 space-y-4">
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-lg font-semibold text-gray-900">Interests</h2>
                    <div className="h-px flex-1 bg-gray-200" />
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {visibleInterests.map((i, idx) => (
                      <div
                        key={idx}
                        className="inline-flex items-center rounded-full bg-gray-100 px-3 py-1 text-sm text-gray-800"
                      >
                        {i.name.trim()}
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            );
          })()}

          {/* REFERENCES */}
          <section className="pt-6 space-y-4">
            {(() => {
              const references = resumeData.references ?? [];
              const visibleReferences = references.filter((r) => {
                const name = r?.name?.trim();
                const designation = r?.designation?.trim();
                const organization = r?.organization?.trim();
                const email = r?.email?.trim();
                const phone = r?.phone?.trim();
                return Boolean(name || designation || organization || email || phone);
              });

              if (!visibleReferences.length) return null;

              return (
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-lg font-semibold text-gray-900">References</h2>
                    <div className="h-px flex-1 bg-gray-200" />
                  </div>

                  <div className="mt-4 space-y-5">
                    {visibleReferences.map((r, idx) => {
                      const name = r?.name?.trim();
                      const designation = r?.designation?.trim();
                      const organization = r?.organization?.trim();
                      const email = r?.email?.trim();
                      const phone = r?.phone?.trim();

                      return (
                        <div key={idx} className="space-y-2">
                          {name && (
                            <div className="font-semibold text-gray-900">{name}</div>
                          )}

                          {(designation || organization) && (
                            <div className="text-sm text-gray-800">
                              {designation}
                              {designation && organization ? " — " : ""}
                              {organization}
                            </div>
                          )}

                          {email && <div className="text-sm text-gray-700">{email}</div>}
                          {phone && <div className="text-sm text-gray-700">{phone}</div>}

                          <div className="border-b border-gray-200" />
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })()}
          </section>


        </div>
      </div>
    </div>
  );
}