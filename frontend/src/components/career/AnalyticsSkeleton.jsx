export default function AnalyticsSkeleton() {
  return (
    <div className="max-w-7xl mx-auto p-8 animate-pulse">

      <div className="h-10 w-72 bg-muted rounded mb-3"></div>

      <div className="h-5 w-96 bg-muted rounded mb-10"></div>

      <div className="grid md:grid-cols-4 gap-6 mb-8">

        {[1,2,3,4].map((i)=>(
          <div
            key={i}
            className="rounded-2xl border p-6"
          >
            <div className="h-4 w-20 bg-muted rounded mb-6"></div>

            <div className="h-10 w-16 bg-muted rounded"></div>
          </div>
        ))}

      </div>

      <div className="rounded-2xl border p-6">

        <div className="h-6 w-56 bg-muted rounded mb-8"></div>

        <div className="h-[350px] bg-muted rounded-xl"></div>

      </div>

    </div>
  );
}