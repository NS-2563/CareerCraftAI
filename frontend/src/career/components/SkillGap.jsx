export default function SkillGap({ skillGap }) {
  return (
    <section className="rounded-xl border p-6">

      <h2 className="text-2xl font-bold mb-6">
        Skill Gap Analysis
      </h2>

      <div className="grid lg:grid-cols-3 gap-6">

        <div className="rounded-lg border p-5">

          <h3 className="font-semibold mb-4">
            Existing Skills
          </h3>

          <ul className="space-y-2">

            {skillGap?.existing_skills?.map((skill, index) => (
              <li key={index}>✅ {skill}</li>
            ))}

          </ul>

        </div>

        <div className="rounded-lg border p-5">

          <h3 className="font-semibold mb-4">
            Missing Skills
          </h3>

          <ul className="space-y-2">

            {skillGap?.missing_skills?.map((skill, index) => (
              <li key={index}>❌ {skill}</li>
            ))}

          </ul>

        </div>

        <div className="rounded-lg border p-5">

          <h3 className="font-semibold mb-4">
            Priority
          </h3>

          <ul className="space-y-2">

            {skillGap?.priority?.map((skill, index) => (
              <li key={index}>⭐ {skill}</li>
            ))}

          </ul>

        </div>

      </div>

    </section>
  );
}

