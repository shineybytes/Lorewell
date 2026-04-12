import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createEvent, listTimezones } from "../api/events";
import StatusMessage from "../components/StatusMessage";
import CreditsEditor, {
  parseVendorEntries,
  serializeVendorEntries,
} from "../components/CreditsEditor";
import type { VendorEntry } from "../types/api";

export default function NewEventPage() {
  const navigate = useNavigate();

  const [timezones, setTimezones] = useState<string[]>([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [vendors, setVendors] = useState<VendorEntry[]>([
    { role: "", instagram: "" },
  ]);

  useEffect(() => {
    async function loadTimezones() {
      try {
        const data = await listTimezones();
        setTimezones(data);
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
      setError(
        "If you provide an event date/time, you must also provide a timezone.",
      );
      return;
    }

    if (!eventDate && eventTimezone) {
      setError(
        "If you provide a timezone, you must also provide an event date/time.",
      );
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
        vendors: serializeVendorEntries(vendors),
        event_guidance:
          String(formData.get("event_guidance") || "").trim() || null,
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
        <p className="helper-text">* Required</p>

        <fieldset>
          <legend>Basic Information</legend>

          <div className="form-row">
            <label htmlFor="title">Title *</label>
            <input id="title" name="title" required />
            <p className="helper-text">
              Use a clear human-readable name for the event.
            </p>
          </div>

          <div className="form-row">
            <label htmlFor="event-type">Event Type</label>
            <input id="event-type" name="event_type" />
            <p className="helper-text">
              Example: wedding, DJ set, birthday, launch party.
            </p>
          </div>

          <div className="form-row">
            <label htmlFor="location">Location</label>
            <input id="location" name="location" />
            <p className="helper-text">
              Add the venue, city, or general setting.
            </p>
          </div>
        </fieldset>

        <fieldset>
          <legend>Timing</legend>

          <div className="form-row">
            <label htmlFor="event-date">Event Date &amp; Time</label>
            <input id="event-date" name="event_date" type="datetime-local" />
            <p className="helper-text">
              Optional. If you add a date/time, also choose a timezone.
            </p>
          </div>

          <div className="form-row">
            <label htmlFor="event-timezone">Event Timezone</label>
            <select id="event-timezone" name="event_timezone" defaultValue="">
              <option value="">Select a timezone</option>
              {timezones.map((tz) => (
                <option key={tz} value={tz}>
                  {tz}
                </option>
              ))}
            </select>
            <p className="helper-text">
              Optional unless you provide an event date/time.
            </p>
          </div>
        </fieldset>

        <fieldset>
          <legend>Context</legend>

          <div className="form-row">
            <label htmlFor="recap">Recap</label>
            <textarea id="recap" name="recap" rows={5} />
            <p className="helper-text">
              Optional. Summarize what happened so captions have better context.
            </p>
          </div>

          <div className="form-row">
            <label htmlFor="event-guidance">Event Guidance</label>
            <textarea id="event-guidance" name="event_guidance" rows={4} />
            <p className="helper-text">
              Optional. Add editorial direction like tone, emphasis, or themes.
            </p>
          </div>

          <div className="form-row">
            <label htmlFor="keywords">Keywords</label>
            <input id="keywords" name="keywords" />
            <p className="helper-text">
              Optional, comma-delimited. Example: house music, rooftop, sunset,
              crowd energy.
            </p>
          </div>

          <CreditsEditor entries={vendors} onEntriesChange={setVendors} />
        </fieldset>

        <div className="form-actions">
          <button type="submit">Create Event</button>
        </div>
      </form>
    </section>
  );
}
