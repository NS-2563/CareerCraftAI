export default function LearningResources({ resources }) {
  return (
    <section className="rounded-xl border p-6">

      <h2 className="text-2xl font-bold mb-6">
        Learning Resources
      </h2>

      <div className="grid lg:grid-cols-2 gap-5">

        {resources?.map((resource, index) => (

          <div
            key={index}
            className="rounded-lg border p-5"
          >

            <h3 className="font-bold">
              {resource.title}
            </h3>

            <span className="inline-block mt-2 rounded-full bg-primary/10 px-3 py-1 text-xs">
              {resource.type}
            </span>

            <p className="mt-3 text-muted-foreground">
              {resource.description}
            </p>

          </div>

        ))}

      </div>

    </section>
  );
}

