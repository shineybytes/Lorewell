import { createBrowserRouter } from "react-router-dom";
import Layout from "./components/Layout";
import EventsPage from "./pages/EventsPage";
import NewEventPage from "./pages/NewEventPage";
import EventDetailPage from "./pages/EventDetailPage";
import DraftEditorPage from "./pages/DraftsEditorPage";
import DraftsPage from "./pages/DraftsPage";
import ApprovalsPage from "./pages/ApprovalsPage";
import SchedulesPage from "./pages/SchedulesPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      {
        index: true,
        element: <EventsPage />,
      },
      {
        path: "events/new",
        element: <NewEventPage />,
      },
      {
        path: "events/:eventId",
        element: <EventDetailPage />,
      },
      {
        path: "drafts",
        element: <DraftsPage />,
      },
      {
        path: "drafts/editor",
        element: <DraftEditorPage />,
      },
      {
        path: "approvals",
        element: <ApprovalsPage />,
      },
      {
        path: "schedules",
        element: <SchedulesPage />,
      },
    ],
  },
]);
