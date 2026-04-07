import { useEffect, useState } from "react";
import { listSchedules } from "../api/schedules";
import type { Schedules } from "../api/schedules";
import StatusMessage from "../components/StatusMessage";

export default function SchedulesPage() {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        setStatus("Loading schedules...");
        const data = await listSchedules();
        setSchedules(data);
        setStatus("");
      } catch (err) {
        console.error(err);
        setError("Failed to load schedules.");
        setStatus("");
      }
    }

    void load();
  }, []);

  return (
    <section aria-labelledby="schedules-heading">
      <h2 id="schedules-heading">Schedules</h2>

      <StatusMessage status={status} error={error} />

      {!schedules.length ? (
        <p>No scheduled posts yet.</p>
      ) : (
        <ul className="card-list">
          {schedules.map((s) => (
            <li key={s.id}>
              <article className="card">
                <h3>Schedule #{s.id}</h3>
                <p>
                  <strong>Approved Post:</strong> {s.approved_post_id}
                </p>
                <p>
                  <strong>Publish At (UTC):</strong> {s.publish_at}
                </p>
                <p>
                  <strong>Timezone:</strong> {s.publish_timezone}
                </p>
                <p>
                  <strong>Status:</strong> {s.status}
                </p>
              </article>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
