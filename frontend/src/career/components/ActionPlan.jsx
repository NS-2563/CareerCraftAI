export default function ActionPlan({ actionPlan }) {
  const renderItem = (item, index) => {
    // Simple string
    if (typeof item === "string") {
      return <li key={index}>• {item}</li>;
    }

    // Object returned by AI
    if (item && typeof item === "object") {
      return (
        <li key={index} className="mb-3">
          {item.skill && (
            <div className="font-medium">
              • {item.skill}
            </div>
          )}

          {item.task && (
            <div>
              • {item.task}
            </div>
          )}

          {item.description && (
            <div className="text-sm text-muted-foreground">
              {item.description}
            </div>
          )}

          {Array.isArray(item.resources) && item.resources.length > 0 && (
            <ul className="ml-5 mt-2 list-disc text-sm text-muted-foreground">
              {item.resources.map((resource, i) => (
                <li key={i}>{resource}</li>
              ))}
            </ul>
          )}
        </li>
      );
    }

    return null;
  };

  return (
    <section className="rounded-xl border p-6">
      <h2 className="text-2xl font-bold mb-6">
        Action Plan
      </h2>

      <div className="grid lg:grid-cols-3 gap-6">

        <div className="rounded-lg border p-5">
          <h3 className="font-bold mb-3">
            Next Week
          </h3>

          <ul className="space-y-2">
            {actionPlan?.next_week?.map(renderItem)}
          </ul>
        </div>

        <div className="rounded-lg border p-5">
          <h3 className="font-bold mb-3">
            Next Month
          </h3>

          <ul className="space-y-2">
            {actionPlan?.next_month?.map(renderItem)}
          </ul>
        </div>

        <div className="rounded-lg border p-5">
          <h3 className="font-bold mb-3">
            Next 6 Months
          </h3>

          <ul className="space-y-2">
            {actionPlan?.next_6_months?.map(renderItem)}
          </ul>
        </div>

      </div>
    </section>
  );
}

