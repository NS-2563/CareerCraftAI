/**
 * Best-effort first-name extraction from the authenticated user.
 * Falls back through full_name → username → email local-part.
 * @param {{ full_name?: string, username?: string, email?: string }|null} user
 * @returns {string|null}
 */
export function getFirstName(user) {
  const raw = user?.full_name || user?.username || user?.email;
  if (!raw) return null;
  const first = raw
    .trim()
    .split(/\s+/)[0]
    ?.split(/[@._-]/)[0];
  if (!first) return null;
  return first.charAt(0).toUpperCase() + first.slice(1);
}

/**
 * Time-aware dashboard greeting. Deterministic given an hour.
 *
 * Morning: 5 AM – 11:59 AM
 * Afternoon: 12 PM – 5:59 PM
 * Evening: 6 PM – 4:59 AM
 *
 * @param {{ user?: object, hour?: number }} [params]
 * @returns {{ greeting: string, message: string, firstName: string|null }}
 */
export function getGreeting({ user, hour = new Date().getHours() } = {}) {
  let greeting;
  let message;

  if (hour >= 5 && hour < 12) {
    greeting = "Good morning";
    message = "You're closer to your dream role than yesterday.";
  } else if (hour >= 12 && hour < 18) {
    greeting = "Good afternoon";
    message = "Let's keep building your career momentum.";
  } else {
    greeting = "Good evening";
    message = "Every small improvement compounds over time.";
  }

  return { greeting, message, firstName: getFirstName(user) };
}
