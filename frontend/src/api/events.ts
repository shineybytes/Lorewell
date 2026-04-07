import { fetchJson } from "./client";
import type { EventCreatePayload, EventRecord } from "../types/api";

export function listEvents() {
  return fetchJson<EventRecord[]>("/events");
}

export function getEvent(eventId: number) {
  return fetchJson<EventRecord>(`/events/${eventId}`);
}

export function createEvent(payload: EventCreatePayload) {
  return fetchJson<EventRecord>("/events", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export function listTimezones() {
  return fetchJson<string[]>("/timezones");
}
