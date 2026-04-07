import { useEffect, useState } from "react";
import { listApprovedPosts } from "../api/approvals";
import type { ApprovedPost } from "../api/approvals";
import StatusMessage from "../components/StatusMessage";
import { createSchedule } from "../api/schedules";
import { listTimezones } from "../api/events";

export default function ApprovalsPage() {
	const [posts, setPosts] = useState<ApprovedPost[]>([]);
	const [status, setStatus] = useState("");
	const [error, setError] = useState("");

	const [timezones, setTimezones] = useState<string[]>([]);
	const [defaultTz, setDefaultTz] = useState("America/Los_Angeles");

	// Per-post schedule state
	const [scheduleState, setScheduleState] = useState<
		Record<number, { date: string; tz: string }>
	>({});

	// Load approved posts
	useEffect(() => {
		async function load() {
			try {
				setStatus("Loading approved posts...");
				setError("");

				const data = await listApprovedPosts();
				setPosts(data);

				setStatus("");
			} catch (err) {
				console.error(err);
				setError(err instanceof Error ? err.message : "Failed to load approvals.");
				setStatus("");
			}
		}

		void load();
	}, []);

	// Load timezones
	useEffect(() => {
		async function loadTimezones() {
			try {
				const data = await listTimezones();
				setTimezones(data);

				const browserTz = Intl.DateTimeFormat().resolvedOptions().timeZone;

				if (data.includes(browserTz)) {
					setDefaultTz(browserTz);
				}
			} catch (err) {
				console.error(err);
			}
		}

		void loadTimezones();
	}, []);

	return (
		<section aria-labelledby="approvals-heading">
			<header className="page-header">
				<div>
					<h2 id="approvals-heading">Approvals</h2>
					<p>Posts ready for scheduling.</p>
				</div>
			</header>

			<StatusMessage status={status} error={error} />

			{!posts.length && !status && !error ? (
				<p>No approved posts yet.</p>
			) : (
				<ul className="card-list">
					{posts.map((post) => {
						const state = scheduleState[post.id] || {
							date: "",
							tz: defaultTz,
						};

						return (
							<li key={post.id}>
								<article className="card">
									<h3>Approved #{post.id}</h3>

									<p><strong>Caption:</strong></p>
									<p>{post.caption_final}</p>

									<p><strong>Hashtags:</strong></p>
									<p>{post.hashtags_final.join(" ")}</p>

									<p><strong>Accessibility:</strong></p>
									<p>{post.accessibility_text}</p>

									<p><strong>Status:</strong> {post.status}</p>

									{/* Date */}
									<div className="form-row">
										<label>Publish At</label>
										<input
											type="datetime-local"
											value={state.date}
											onChange={(e) =>
												setScheduleState((prev) => ({
													...prev,
													[post.id]: {
														date: e.target.value,
														tz: state.tz,
													},
												}))
											}
										/>
									</div>

									{/* Timezone */}
									<div className="form-row">
										<label>Timezone</label>
										<select
											value={state.tz}
											onChange={(e) =>
												setScheduleState((prev) => ({
													...prev,
													[post.id]: {
														date: state.date,
														tz: e.target.value,
													},
												}))
											}
										>
											<option value="">Select a timezone</option>
											{timezones.map((tz) => (
												<option key={tz} value={tz}>
													{tz}
												</option>
											))}
										</select>
									</div>

									{/* Schedule Button */}
									<button
										type="button"
										onClick={async () => {
											try {
												if (!state.date) {
													alert("Choose a publish date and time.");
													return;
												}

												if (!state.tz) {
													alert("Choose a timezone.");
													return;
												}

												await createSchedule(post.id, {
													publish_at: state.date,
													publish_timezone: state.tz,
												});

												alert("Scheduled!");
											} catch (err) {
												console.error(err);
												alert(
													err instanceof Error
														? err.message
														: "Failed to schedule"
												);
											}
										}}
									>
										Schedule
									</button>
								</article>
							</li>
						);
					})}
				</ul>
			)}
		</section>
	);
}
