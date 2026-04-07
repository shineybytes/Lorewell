import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createEvent, listTimezones } from "../api/events";
import StatusMessage from "../components/StatusMessage";

export default function NewEventPage() {
  const navigate = useNavigate();

  const [timezones, setTimezones] = useState<string[]>([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadTimezones() {
      try {
        const data = await listTimezones();
        setTimezones(data);

        const browserTz = Intl.DateTimeFormat().resolvedOptions().timeZone;
        if (data.includes(browserTz)) {
          const select = document.getElementById("event-timezone") as HTMLSelectElement | null;
          if (select) {
            select.value = browserTz;
          }
        }
      } catch (err) {
        console.error(err);
      }
    }

    void loadTimezones();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setStatus("");
    setError("");

    const formData = new FormData(event.currentTarget);

    const eventDate = String(formData.get("event_date") || "").trim();
    const eventTimezone = String(formData.get("event_timezone") || "").trim();

    if (eventDate && !eventTimezone) {
      setError("If you provide an event date/time, you must also provide a timezone.");
      return;
    }

    if (!eventDate && eventTimezone) {
      setError("If you provide a timezone, you must also provide an event date/time.");
      return;
    }

    try {
      setStatus("Creating event...");

      const created = await createEvent({
        title: String(formData.get("title") || "").trim(),
        event_type: String(formData.get("event_type") || "").trim() || null,
        location: String(formData.get("location") || "").trim() || null,
        event_date: eventDate || null,
        event_timezone: eventTimezone || null,
        recap: String(formData.get("recap") || "").trim() || null,
        keywords: String(formData.get("keywords") || "").trim() || null,
        vendors: String(formData.get("vendors") || "").trim() || null,
        event_guidance: String(formData.get("event_guidance") || "").trim() || null,
      });

      navigate(`/events/${created.id}`);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Failed to create event.");
      setStatus("");
    }
  }

  return (
    <section aria-labelledby="new-event-heading">
      <h2 id="new-event-heading">Create Event</h2>
      <p>Start with what happened. Lorewell can help with the rest.</p>

      <StatusMessage status={status} error={error} />

      <form onSubmit={handleSubmit}>
        <fieldset>
          <legend>Basic Information</legend>

          <div className="form-row">
            <label htmlFor="title">Title</label>
            <input id="title" name="title" required />
          </div>

          <div className="form-row">
            <label htmlFor="event-type">Event Type</label>
            <input id="event-type" name="event_type" />
          </div>

          <div className="form-row">
            <label htmlFor="location">Location</label>
            <input id="location" name="location" />
          </div>
        </fieldset>

        <fieldset>
          <legend>Timing</legend>

          <div className="form-row">
            <label htmlFor="event-date">Event Date & Time (optional)</label>
            <input id="event-date" name="event_date" type="datetime-local" />
          </div>

          <div className="form-row">
            <label htmlFor="event-timezone">Event Timezone (optional)</label>
            <select id="event-timezone" name="event_timezone" defaultValue="">
              <option value="">Select a timezone</option>
              {timezones.map((tz) => (
                <option key={tz} value={tz}>
                  {tz}
                </option>
              ))}
            </select>
          </div>
        </fieldset>

        <fieldset>
          <legend>Context</legend>

          <div className="form-row">
            <label htmlFor="recap">Recap</label>
            <textarea id="recap" name="recap" rows={5} />
          </div>

          <div className="form-row">
            <label htmlFor="event-guidance">Event Guidance</label>
            <textarea id="event-guidance" name="event_guidance" rows={4} />
          </div>

          <div className="form-row">
            <label htmlFor="keywords">Keywords</label>
            <input id="keywords" name="keywords" />
          </div>

          <div className="form-row">
            <label htmlFor="vendors">Vendors</label>
            <input id="vendors" name="vendors" />
          </div>
        </fieldset>

        <div className="form-actions">
          <button type="submit">Create Event</button>
        </div>
      </form>
    </section>
  );
}
