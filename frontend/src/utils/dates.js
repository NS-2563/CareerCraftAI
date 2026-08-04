const MS_PER_MINUTE = 60_000;
const MS_PER_DAY = 86_400_000;

/**
 * Normalize a date to the start of its local day.
 * @param {Date|string|number} [date]
 */
export function startOfDay(date = new Date()) {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  return d;
}

/**
 * Human "X ago" label for a timestamp (best effort, locale-aware for old dates).
 * @param {string|number|Date|null} dateStr
 * @returns {string}
 */
export function formatTimeAgo(dateStr) {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  if (Number.isNaN(date.getTime())) return "";
  const diffMs = Date.now() - date.getTime();
  const diffMins = Math.floor(diffMs / MS_PER_MINUTE);
  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

/**
 * Whole days from today until a date (negative = in the past, null = invalid).
 * @param {string|number|Date|null} dateStr
 * @returns {number|null}
 */
export function daysUntil(dateStr) {
  if (!dateStr) return null;
  const target = startOfDay(new Date(dateStr));
  if (Number.isNaN(target.getTime())) return null;
  return Math.round((target.getTime() - startOfDay().getTime()) / MS_PER_DAY);
}

/**
 * Relative day label for upcoming dates: "Today", "Tomorrow", "In 3 days", or a weekday.
 * @param {string|number|Date|null} dateStr
 * @returns {string}
 */
export function formatRelativeDay(dateStr) {
  const diff = daysUntil(dateStr);
  if (diff == null) return "";
  if (diff === 0) return "Today";
  if (diff === 1) return "Tomorrow";
  if (diff > 1 && diff < 7) return `In ${diff} days`;
  return new Date(dateStr).toLocaleDateString("en-US", { weekday: "long" });
}

/**
 * Grouping label for the activity feed ("Today", "Yesterday", "3 days ago", date).
 * @param {string|number|Date|null} dateStr
 * @returns {string}
 */
export function formatGroupDay(dateStr) {
  const diff = daysUntil(dateStr);
  if (diff == null) return "";
  if (diff === 0) return "Today";
  if (diff === -1) return "Yesterday";
  if (diff < -1 && diff > -7) return `${Math.abs(diff)} days ago`;
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}
