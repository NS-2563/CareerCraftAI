import StatCard from "./StatCard";

export default function StatsGrid({ stats }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <StatCard
          key={stat.key}
          title={stat.title}
          value={stat.value}
          icon={stat.icon}
          variant={stat.variant}
        />
      ))}
    </div>
  );
}

