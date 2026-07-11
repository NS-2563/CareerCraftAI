export default function LearningRoadmap({ roadmap }) {
  return (
    <section className="rounded-xl border p-6">

      <h2 className="text-2xl font-bold mb-6">
        Learning Roadmap
      </h2>

      <div className="space-y-5">

        {roadmap?.map((stage, index) => (

          <div
            key={index}
            className="rounded-lg border p-5"
          >

            <h3 className="font-bold text-lg">
              {stage.stage}
            </h3>

            <div className="mt-4">

              <p className="font-semibold">
                Topics
              </p>

              <ul className="list-disc pl-5 mt-2">

                {stage.topics?.map((topic, i) => (
                  <li key={i}>{topic}</li>
                ))}

              </ul>

            </div>

            <div className="mt-4">

              <p className="font-semibold">
                Projects
              </p>

              <ul className="list-disc pl-5 mt-2">

                {stage.projects?.map((project, i) => (
                  <li key={i}>{project}</li>
                ))}

              </ul>

            </div>

          </div>

        ))}

      </div>

    </section>
  );
}