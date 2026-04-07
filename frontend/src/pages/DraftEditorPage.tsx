import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { getEvent } from "../api/events";
import { listEventAssets } from "../api/assets";
import { approvePost, createPost, generatePost, getPost, updatePost } from "../api/posts";
import type { AssetRecord, EventRecord, PostGenerationResponse, PostRecord } from "../types/api";
import StatusMessage from "../components/StatusMessage";
import AssetPreview from "../components/AssetPreview";

export default function DraftEditorPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const eventId = searchParams.get("event_id");
  const assetId = searchParams.get("asset_id");
  const postId = searchParams.get("post_id");

  const numericEventId = eventId ? Number(eventId) : null;
  const numericAssetId = assetId ? Number(assetId) : null;
  const numericPostId = postId ? Number(postId) : null;

  const [event, setEvent] = useState<EventRecord | null>(null);
  const [asset, setAsset] = useState<AssetRecord | null>(null);
  const [post, setPost] = useState<PostRecord | null>(null);

  const [brandVoice, setBrandVoice] = useState("");
  const [ctaGoal, setCtaGoal] = useState("");
  const [generationNotes, setGenerationNotes] = useState("");

  const [generated, setGenerated] = useState<PostGenerationResponse | null>(null);
  const [finalCaption, setFinalCaption] = useState("");
  const [finalHashtags, setFinalHashtags] = useState("");
  const [finalAccessibility, setFinalAccessibility] = useState("");

  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  const contextMissing = useMemo(() => {
    return !numericPostId && (!numericEventId || !numericAssetId);
  }, [numericPostId, numericEventId, numericAssetId]);

  useEffect(() => {
    async function load() {
      if (contextMissing) {
        setError("Missing draft context.");
        return;
      }

      try {
        setStatus("Loading draft context...");
        setError("");

        let resolvedEventId = numericEventId;
        let resolvedAssetId = numericAssetId;
        let loadedPost: PostRecord | null = null;

        if (numericPostId) {
          loadedPost = await getPost(numericPostId);
          setPost(loadedPost);

          resolvedEventId = loadedPost.event_id;
          resolvedAssetId = loadedPost.asset_id;

          setBrandVoice(loadedPost.brand_voice || "");
          setCtaGoal(loadedPost.cta_goal || "");
          setGenerationNotes(loadedPost.generation_notes || "");
        }

        if (!resolvedEventId || !resolvedAssetId) {
          setError("Draft is missing event or asset context.");
          setStatus("");
          return;
        }

        const [eventData, assetData] = await Promise.all([
          getEvent(resolvedEventId),
          listEventAssets(resolvedEventId),
        ]);

        const selectedAsset =
          assetData.find((candidate) => candidate.id === resolvedAssetId) || null;

        setEvent(eventData);
        setAsset(selectedAsset);

        if (!selectedAsset) {
          setError("Asset not found for this event.");
        }

        if (
          loadedPost &&
          loadedPost.status === "generated" &&
          loadedPost.generated_caption_options
        ) {
          setFinalCaption(loadedPost.generated_caption_options || "");
          setFinalHashtags(loadedPost.generated_hashtag_options || "");
          setFinalAccessibility(loadedPost.generated_accessibility_options || "");
        }

        setStatus("");
      } catch (err) {
        console.error(err);
        setError(err instanceof Error ? err.message : "Failed to load draft context.");
        setStatus("");
      }
    }

    void load();
  }, [contextMissing, numericPostId, numericEventId, numericAssetId]);

  function useCaption(text: string) {
    setFinalCaption(text);
  }

  async function handleGenerate(eventSubmit: FormEvent<HTMLFormElement>) {
    eventSubmit.preventDefault();

    try {
      setStatus("Generating draft...");
      setError("");

      const payload = {
        brand_voice: brandVoice,
        cta_goal: ctaGoal,
        generation_notes: generationNotes,
      };

      let resolvedPostId = numericPostId;

      if (!resolvedPostId) {
        if (!numericEventId || !numericAssetId) {
          setError("Missing event or asset context.");
          setStatus("");
          return;
        }

        const created = await createPost({
          event_id: numericEventId,
          asset_id: numericAssetId,
          ...payload,
        });

        resolvedPostId = created.post_id;
        setSearchParams({
          post_id: String(created.post_id),
        });
      } else {
        await updatePost(resolvedPostId, payload);
      }

      const generatedResult = await generatePost(resolvedPostId);
      setGenerated(generatedResult);

      setFinalCaption(
        generatedResult.caption_medium ||
          generatedResult.caption_long ||
          generatedResult.caption_short ||
          ""
      );
      setFinalHashtags((generatedResult.hashtags || []).join(" "));
      setFinalAccessibility(generatedResult.accessibility_text || "");

      setStatus("Draft generated.");
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Failed to generate draft.");
      setStatus("");
    }
  }

  async function handleSendToApprovals() {
    const resolvedPostId = numericPostId || generated?.post_id;

    if (!resolvedPostId) {
      setError("Missing post id.");
      return;
    }

    try {
      setStatus("Sending to Approvals...");
      setError("");

      const approved = await approvePost(resolvedPostId, {
        caption_final: finalCaption,
        hashtags_final: finalHashtags.split(/\s+/).filter(Boolean),
        accessibility_text: finalAccessibility,
      });

      setStatus("Moved to Approvals.");
      navigate("/drafts");
      alert(`Moved to Approvals. Approved post id: ${approved.approved_post_id}`);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Failed to send to approvals.");
      setStatus("");
    }
  }

  return (
    <section aria-labelledby="draft-editor-heading">
      <p>
        <Link to="/drafts">Back to Drafts</Link>
      </p>

      <header className="page-header">
        <div>
          <h2 id="draft-editor-heading">Draft Editor</h2>
          <p>Generate, refine, and move this draft forward.</p>
        </div>
      </header>

      <StatusMessage status={status} error={error} />

      <section aria-labelledby="context-heading">
        <h3 id="context-heading">Context</h3>

        {event ? (
          <div className="card">
            <h4>{event.title}</h4>
            <p>
              <strong>Type:</strong> {event.event_type || "None"}
            </p>
            <p>
              <strong>Location:</strong> {event.location || "None"}
            </p>
            <p>
              <strong>Recap:</strong> {event.recap || "No recap provided."}
            </p>
            <p>
              <strong>Guidance:</strong>{" "}
              {event.event_guidance || "No guidance provided."}
            </p>
            {asset && <AssetPreview asset={asset} />}
          </div>
        ) : (
          <p>No context loaded yet.</p>
        )}
      </section>

      <section aria-labelledby="settings-heading">
        <h3 id="settings-heading">Draft Settings</h3>

        <form onSubmit={handleGenerate}>
          <div className="form-row">
            <label htmlFor="brand-voice">Brand Voice</label>
            <input
              id="brand-voice"
              value={brandVoice}
              onChange={(e) => setBrandVoice(e.target.value)}
              required
            />
          </div>

          <div className="form-row">
            <label htmlFor="cta-goal">CTA Goal</label>
            <input
              id="cta-goal"
              value={ctaGoal}
              onChange={(e) => setCtaGoal(e.target.value)}
              required
            />
          </div>

          <div className="form-row">
            <label htmlFor="generation-notes">Generation Notes</label>
            <textarea
              id="generation-notes"
              value={generationNotes}
              onChange={(e) => setGenerationNotes(e.target.value)}
            />
          </div>

          <button type="submit">Generate Draft</button>
        </form>
      </section>

      <section aria-labelledby="generated-heading">
        <h3 id="generated-heading">Generated Draft</h3>

        {!generated ? (
          <p>No generated draft yet.</p>
        ) : (
          <>
            <section>
              <h4>Generated Caption Options</h4>

              {[
                { label: "Short Caption", value: generated.caption_short },
                { label: "Medium Caption", value: generated.caption_medium },
                { label: "Long Caption", value: generated.caption_long },
              ]
                .filter((option) => option.value)
                .map((option) => (
                  <div className="generated-option" key={option.label}>
                    <h5>{option.label}</h5>
                    <textarea readOnly value={option.value} />
                    <button type="button" onClick={() => useCaption(option.value)}>
                      Use This Caption
                    </button>
                  </div>
                ))}
            </section>

            <section>
              <h4>Finalize Draft</h4>
              <p className="helper-text">
                You can keep editing this in Drafts. When ready, send it to Approvals.
              </p>

              <div className="form-row">
                <label htmlFor="final-caption">Final Caption</label>
                <textarea
                  id="final-caption"
                  value={finalCaption}
                  onChange={(e) => setFinalCaption(e.target.value)}
                />
              </div>

              <div className="form-row">
                <label htmlFor="final-hashtags">Final Hashtags</label>
                <textarea
                  id="final-hashtags"
                  value={finalHashtags}
                  onChange={(e) => setFinalHashtags(e.target.value)}
                />
              </div>

              <div className="form-row">
                <label htmlFor="final-accessibility">Final Accessibility Text</label>
                <textarea
                  id="final-accessibility"
                  value={finalAccessibility}
                  onChange={(e) => setFinalAccessibility(e.target.value)}
                />
              </div>

              <button type="button" onClick={handleSendToApprovals}>
                Send to Approvals
              </button>
            </section>
          </>
        )}
      </section>
    </section>
  );
}
