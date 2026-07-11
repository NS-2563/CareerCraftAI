export default function CareerPaths({ paths }) {
  return (
    <section className="rounded-xl border p-6">

      <h2 className="text-2xl font-bold mb-6">
        Career Paths
      </h2>

      <div className="grid lg:grid-cols-2 gap-5">

        {paths?.map((path, index) => (

          <div
            key={index}
            className="rounded-lg border p-5"
          >

            <h3 className="font-bold text-lg">
              {path.title}
            </h3>

            <p className="mt-3 text-muted-foreground">
              {path.reason}
            </p>

            <div className="mt-5 flex gap-3 flex-wrap">

              <span className="rounded-full bg-primary/10 px-3 py-1 text-sm">
                {path.difficulty}
              </span>

              <span className="rounded-full bg-primary/10 px-3 py-1 text-sm">
                {path.future_demand}
              </span>

            </div>

          </div>

        ))}

      </div>

    </section>
  );
}