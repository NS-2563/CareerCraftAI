/* eslint react-hooks/set-state-in-effect: "off" */
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import AnalyticsSkeleton from "@/components/career/AnalyticsSkeleton";
import analyticsApi from "@/services/analyticsApi";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

import {
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";

const COLORS = [
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#8b5cf6",
  "#ef4444",
  "#06b6d4",
];

export default function Analytics() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  async function loadAnalytics() {
    try {
      const res = await analyticsApi.getAnalytics();
      setAnalytics(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAnalytics();
  }, []);

  if (loading) {
    return <AnalyticsSkeleton />;
  }

  const careerGoalData = Object.entries(
    analytics.career_goals || {}
  ).map(([name, value]) => ({
    name,
    value,
  }));

  return (
    <div className="max-w-7xl mx-auto p-8 space-y-8">

      {/* Heading */}

      <div>
        <h1 className="text-4xl font-bold">
          Progress Analytics
        </h1>

        <p className="text-gray-500 mt-2">
          Track your career readiness growth over time.
        </p>
      </div>

      {/* Statistics */}

      <div className="grid md:grid-cols-4 gap-6">

        {[
          {
            title: "Reports",
            value: analytics.total_reports,
          },
          {
            title: "Average",
            value: `${analytics.average_score}%`,
          },
          {
            title: "Highest",
            value: `${analytics.highest_score}%`,
          },
          {
            title: "Latest",
            value: `${analytics.latest_score}%`,
          },
        ].map((card, index) => (
          <motion.div
            key={card.title}
            initial={{
              opacity: 0,
              y: 25,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            transition={{
              delay: index * 0.15,
            }}
          >
            <StatCard
              title={card.title}
              value={card.value}
            />
          </motion.div>
        ))}

      </div>

      {/* Readiness Graph */}

      <motion.div
        className="rounded-2xl border p-6 shadow-sm"
        initial={{
          opacity: 0,
        }}
        animate={{
          opacity: 1,
        }}
        transition={{
          duration: 0.5,
        }}
      >

        <h2 className="text-xl font-semibold mb-6">
          Readiness Progress
        </h2>

        <ResponsiveContainer
          width="100%"
          height={350}
        >
          <LineChart data={analytics.trend}>
            <CartesianGrid strokeDasharray="3 3" />

            <XAxis dataKey="date" />

            <YAxis />

            <Tooltip
              formatter={(value) => [
                `${value}%`,
                "Readiness Score",
              ]}
            />

            <Line
              type="monotone"
              dataKey="score"
              stroke="#3b82f6"
              strokeWidth={3}
            />
          </LineChart>
        </ResponsiveContainer>

      </motion.div>

      {/* Career Goal Distribution */}

      <motion.div
        className="rounded-2xl border p-6 shadow-sm"
        initial={{
          opacity: 0,
        }}
        animate={{
          opacity: 1,
        }}
        transition={{
          delay: 0.3,
        }}
      >

        <h2 className="text-xl font-semibold mb-6">
          Career Interests
        </h2>

        <ResponsiveContainer
          width="100%"
          height={350}
        >
          <PieChart>

            <Pie
              data={careerGoalData}
              dataKey="value"
              nameKey="name"
              outerRadius={120}
              label
            >
              {careerGoalData.map((entry, index) => (
                <Cell
                  key={index}
                  fill={
                    COLORS[index % COLORS.length]
                  }
                />
              ))}
            </Pie>

            <Tooltip />

            <Legend />

          </PieChart>
        </ResponsiveContainer>

      </motion.div>

      {/* Recent Progress */}

<motion.div
  className="rounded-2xl border p-6 shadow-sm"
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ delay: 0.45 }}
>
  <h2 className="text-xl font-semibold mb-6">
    Recent Progress
  </h2>

  {analytics.previous_score === null ? (

    <div className="text-gray-500">
      Complete another assessment to compare your progress.
    </div>

  ) : (

    <div className="grid md:grid-cols-3 gap-6">

      <div>
        <p className="text-sm text-gray-500">
          Previous Score
        </p>

        <p className="text-4xl font-bold mt-2">
          {analytics.previous_score}%
        </p>
      </div>

      <div>
        <p className="text-sm text-gray-500">
          Latest Score
        </p>

        <p className="text-4xl font-bold mt-2">
          {analytics.latest_score}%
        </p>
      </div>

      <div>
        <p className="text-sm text-gray-500">
          Improvement
        </p>

        {analytics.score_change > 0 && (
          <div className="flex items-center gap-2 mt-2 text-green-600">
            <TrendingUp size={26} />
            <span className="text-4xl font-bold">
              +{analytics.score_change}
            </span>
          </div>
        )}

        {analytics.score_change < 0 && (
          <div className="flex items-center gap-2 mt-2 text-red-600">
            <TrendingDown size={26} />
            <span className="text-4xl font-bold">
              {analytics.score_change}
            </span>
          </div>
        )}

        {analytics.score_change === 0 && (
          <div className="flex items-center gap-2 mt-2 text-gray-500">
            <Minus size={26} />
            <span className="text-4xl font-bold">
              0
            </span>
          </div>
        )}

      </div>

    </div>

  )}
</motion.div>

    </div>
  );
}

function StatCard({
  title,
  value,
}) {
  return (
    <div className="rounded-2xl border p-6 shadow-sm hover:shadow-lg transition-all duration-300 hover:-translate-y-1">

      <div className="text-sm text-gray-500">
        {title}
      </div>

      <div className="text-4xl font-bold mt-3">
        {value}
      </div>

    </div>
  );
}