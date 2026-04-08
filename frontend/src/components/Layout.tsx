import { NavLink, Outlet } from "react-router-dom";

export default function Layout() {
  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>

      <header className="site-header">
        <div className="site-shell">
          <h1 className="site-title">Lorewell</h1>
          <nav aria-label="Primary">
            <ul className="nav-list">
              <li>
                <NavLink to="/">Events</NavLink>
              </li>
              <li>
                <NavLink to="/events/new">New Event</NavLink>
              </li>
              <li>
                <NavLink to="/drafts">Drafts</NavLink>
              </li>
              <li>
                <NavLink to="/approvals">Approvals</NavLink>
              </li>
              <li>
                <NavLink to="/schedules">Schedules</NavLink>
              </li>
            </ul>
          </nav>
        </div>
      </header>

      <main id="main-content" className="site-shell">
        <Outlet />
      </main>
    </>
  );
}
