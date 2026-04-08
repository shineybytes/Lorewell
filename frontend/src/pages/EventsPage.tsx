import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { deleteEvent, listEvents } from "../api/events";
import type { EventRecord } from "../types/api";
import StatusMessage from "../components/StatusMessage";

export default function EventsPage() {
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        setStatus("Loading events...");
        setError("");
        const data = await listEvents();
        setEvents(data);
        setStatus("");
      } catch (err) {
        console.error(err);
        setError(err instanceof Error ? err.message : "Failed to load events.");
        setStatus("");
      }
    }

    void load();
  }, []);

  return (
    <section aria-labelledby="events-heading">
      <div className="page-header">
        <div>
          <h2 id="events-heading">Events</h2>
          <p>Your event containers live here.</p>
        </div>

        <Link className="button-link" to="/events/new">
          Create Event
        </Link>
      </div>

      <StatusMessage status={status} error={error} />

      {!events.length && !status && !error ? (
        <p>No events yet.</p>
      ) : (
        <ul className="card-list">
          {events.map((event) => (
            <li key={event.id}>
              <article className="card">
                <h3>{event.title}</h3>
                <p>
                  <strong>Type:</strong> {event.event_type || "None"}
                </p>
                <p>
                  <strong>Location:</strong> {event.location || "None"}
                </p>
                <p>
                  <strong>Date:</strong> {event.event_date || "Unknown"}
                </p>

                <div className="approval-action-row">
                  <Link className="button-link" to={`/events/${event.id}`}>
                    Open Event
                  </Link>

                  <button
                    type="button"
                    className="button-danger"
                    onClick={async () => {
                      if (
                        !confirm(
                          "Delete this event? This may affect related assets and drafts.",
                        )
                      ) {
                        return;
                      }

                      try {
                        await deleteEvent(event.id);
                        setEvents((prev) =>
                          prev.filter((e) => e.id !== event.id),
                        );
                      } catch (err) {
                        console.error(err);
                        alert(
                          err instanceof Error
                            ? err.message
                            : "Failed to delete event.",
                        );
                      }
                    }}
                  >
                    Delete Event
                  </button>
                </div>
              </article>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
