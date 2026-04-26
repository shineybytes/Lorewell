import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { deleteEvent, listEvents } from "../api/events";
import type { EventRecord } from "../types/api";
import StatusMessage from "../components/StatusMessage";
import { useAsyncState } from "../hooks/useAsyncState";
import ListToolbar from "../components/ListToolbar";
import ListSummary from "../components/ListSummary";

type EventSortMode = "newest" | "oldest" | "title_asc" | "title_desc";

function formatDate(value: string | null | undefined) {
  if (!value) return "Unknown";

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;

  return parsed.toLocaleString();
}

export default function EventsPage() {
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [eventSearch, setEventSearch] = useState("");
  const [sortMode, setSortMode] = useState<EventSortMode>("newest");
  const [expandedEventId, setExpandedEventId] = useState<number | null>(null);

  const loadState = useAsyncState();

  async function loadData(showLoadingMessage = true) {
    try {
      if (showLoadingMessage) {
        loadState.start("Loading events...");
      }

      const data = await listEvents();
      setEvents(data);

      if (showLoadingMessage) {
        loadState.succeed("");
      }
    } catch (err) {
      console.error(err);
      loadState.fail(
        err instanceof Error ? err.message : "Failed to load events.",
      );
    }
  }

  useEffect(() => {
    void loadData(true);
  }, []);

  const filteredEvents = useMemo(() => {
    let result = [...events];

    const query = eventSearch.trim().toLowerCase();

    if (query) {
      result = result.filter((event) => {
        const title = (event.title || "").toLowerCase();
        const eventType = (event.event_type || "").toLowerCase();
        const location = (event.location || "").toLowerCase();
        const recap = (event.recap || "").toLowerCase();
        const keywords = (event.keywords || "").toLowerCase();
        const vendors = (event.vendors || "").toLowerCase();
        const guidance = (event.event_guidance || "").toLowerCase();

        return (
          title.includes(query) ||
          eventType.includes(query) ||
          location.includes(query) ||
          recap.includes(query) ||
          keywords.includes(query) ||
          vendors.includes(query) ||
          guidance.includes(query)
        );
      });
    }

    result.sort((a, b) => {
      switch (sortMode) {
        case "oldest":
          return (
            new Date(a.event_date || a.created_at || "").getTime() -
            new Date(b.event_date || b.created_at || "").getTime()
          );
        case "title_asc":
          return (a.title || "").localeCompare(b.title || "");
        case "title_desc":
          return (b.title || "").localeCompare(a.title || "");
        case "newest":
        default:
          return (
            new Date(b.event_date || b.created_at || "").getTime() -
            new Date(a.event_date || a.created_at || "").getTime()
          );
      }
    });

    return result;
  }, [events, eventSearch, sortMode]);

  function toggleExpandedEvent(id: number) {
    setExpandedEventId((current) => (current === id ? null : id));
  }

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

      <ListToolbar
        searchId="event-search"
        searchValue={eventSearch}
        onSearchChange={setEventSearch}
        searchPlaceholder="Search title, type, location, keywords, vendors, or recap"
        sortId="event-sort"
        sortValue={sortMode}
        onSortChange={(v) =>
          setSortMode(v as "newest" | "oldest" | "title_asc" | "title_desc")
        }
        sortOptions={[
          { value: "newest", label: "Newest first" },
          { value: "oldest", label: "Oldest first" },
          { value: "title_asc", label: "Title A–Z" },
          { value: "title_desc", label: "Title Z–A" },
        ]}
      />
      <ListSummary
        visibleCount={filteredEvents.length}
        totalCount={events.length}
        noun="events"
        query={eventSearch}
      />
      <StatusMessage
        loading={loadState.loading}
        status={loadState.status}
        error={loadState.error}
      />

      {!filteredEvents.length && !loadState.loading && !loadState.error ? (
        <p>No events yet.</p>
      ) : (
        <>
          <div className="event-index-header" aria-hidden="true">
            <span>Title</span>
            <span>Type</span>
            <span>Location</span>
            <span>Date</span>
          </div>

          <ul className="event-index-list">
            {filteredEvents.map((event) => {
              const isExpanded = expandedEventId === event.id;

              return (
                <li key={event.id} className="event-index-row">
                  <div
                    className="event-index-main"
                    onClick={() => toggleExpandedEvent(event.id)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        toggleExpandedEvent(event.id);
                      }
                    }}
                  >
                    <span className="event-index-title">{event.title}</span>
                    <span>{event.event_type || "None"}</span>
                    <span>{event.location || "None"}</span>
                    <span>{formatDate(event.event_date)}</span>
                  </div>

                  {isExpanded && (
                    <div className="event-index-details">
                      <article className="card">
                        <h3>{event.title}</h3>

                        <p>
                          <strong>Type:</strong> {event.event_type || "None"}
                        </p>
                        <p>
                          <strong>Location:</strong> {event.location || "None"}
                        </p>
                        <p>
                          <strong>Date:</strong> {formatDate(event.event_date)}
                        </p>
                        <p>
                          <strong>Timezone:</strong>{" "}
                          {event.event_timezone || "None"}
                        </p>
                        <p>
                          <strong>Keywords:</strong> {event.keywords || "None"}
                        </p>
                        <p>
                          <strong>Vendors:</strong> {event.vendors || "None"}
                        </p>
                        <p>
                          <strong>Recap:</strong> {event.recap || "None"}
                        </p>
                        <p>
                          <strong>Guidance:</strong>{" "}
                          {event.event_guidance || "None"}
                        </p>

                        <div className="approval-action-row">
                          <Link
                            className="button-link"
                            to={`/events/${event.id}`}
                          >
                            Open Event
                          </Link>

                          <button
                            type="button"
                            className="button-danger"
                            onClick={async (e) => {
                              e.stopPropagation();

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
                                  prev.filter(
                                    (candidate) => candidate.id !== event.id,
                                  ),
                                );
                                setExpandedEventId((current) =>
                                  current === event.id ? null : current,
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
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        </>
      )}
    </section>
  );
}
