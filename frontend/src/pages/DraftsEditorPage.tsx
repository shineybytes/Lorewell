import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { getEvent } from "../api/events";
import { getAsset } from "../api/assets";
import {
  approvePost,
  createPost,
  generatePost,
  getPost,
  saveDraftContent,
  updatePost,
} from "../api/posts";
import type {
  AssetRecord,
  EventRecord,
  PostGenerationResponse,
  PostRecord,
  VendorEntry,
} from "../types/api";
import StatusMessage from "../components/StatusMessage";
import AssetPreview from "../components/AssetPreview";
import { useAsyncState } from "../hooks/useAsyncState";
import InstagramPreview from "../components/InstagramPreview";
import CreditsEditor, {
  buildCreditsText,
  parseVendorEntries,
  presetToTemplate,
  type CreditStylePreset,
} from "../components/CreditsEditor";

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
  const [workingTitle, setWorkingTitle] = useState("");

  const [generated, setGenerated] = useState<PostGenerationResponse | null>(
    null,
  );
  const [finalCaption, setFinalCaption] = useState("");
  const [finalHashtags, setFinalHashtags] = useState("");
  const [finalAccessibility, setFinalAccessibility] = useState("");

  const [creditEntries, setCreditEntries] = useState<VendorEntry[]>([
    { role: "", instagram: "" },
  ]);
  const [creditPreset, setCreditPreset] = useState<CreditStylePreset>("by");
  const [creditTemplate, setCreditTemplate] = useState("{role} by {handle}");

  const loadState = useAsyncState();
  const generateState = useAsyncState();
  const approvalState = useAsyncState();
  const saveState = useAsyncState();

  const contextMissing = useMemo(() => {
    return !numericPostId && !numericAssetId;
  }, [numericPostId, numericAssetId]);

  useEffect(() => {
    async function load() {
      if (contextMissing) {
        loadState.fail("Missing draft context.");
        return;
      }

      try {
        loadState.start("Loading draft context...");

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

        if (!resolvedAssetId) {
          loadState.fail("Draft is missing asset context.");
          return;
        }

        const assetData = await getAsset(resolvedAssetId);
        setAsset(assetData);

        let eventData: EventRecord | null = null;
        const finalEventId = resolvedEventId ?? assetData.event_id ?? null;

        if (finalEventId) {
          try {
            eventData = await getEvent(finalEventId);
            setEvent(eventData);

            if (eventData.vendors) {
              setCreditEntries(parseVendorEntries(eventData.vendors));
            }
          } catch {
            setEvent(null);
          }
        } else {
          setEvent(null);
        }

        if (loadedPost) {
          setFinalCaption(
            loadedPost.approved_caption_final ||
              loadedPost.draft_caption_current ||
              loadedPost.generated_caption_options ||
              "",
          );
          setFinalHashtags(
            loadedPost.approved_hashtags_final ||
              loadedPost.draft_hashtags_current ||
              loadedPost.generated_hashtag_options ||
              "",
          );
          setFinalAccessibility(
            loadedPost.approved_accessibility_text ||
              loadedPost.draft_accessibility_current ||
              loadedPost.generated_accessibility_options ||
              "",
          );
          setWorkingTitle(loadedPost.working_title || "");
        }

        loadState.succeed("");
      } catch (err) {
        console.error(err);
        loadState.fail(
          err instanceof Error ? err.message : "Failed to load draft context.",
        );
      }
    }

    void load();
  }, [contextMissing, numericPostId, numericEventId, numericAssetId]);

  function useCaption(text: string) {
    setFinalCaption(text);
  }

  function parseHashtags(value: string): string[] {
    return value
      .split(/\s+/)
      .map((tag) => tag.trim())
      .filter(Boolean);
  }

  function normalizeHashtag(tag: string): string {
    const cleaned = tag
      .trim()
      .replace(/^#+/, "")
      .toLowerCase()
      .replace(/[^\p{L}\p{N}_]+/gu, "");

    return cleaned ? `#${cleaned}` : "";
  }

  function keywordToHashtag(keyword: string): string {
    return normalizeHashtag(keyword.replace(/\s+/g, ""));
  }

  function addHashtag(tag: string) {
    const normalized = normalizeHashtag(tag);
    if (!normalized) return;

    const existing = parseHashtags(finalHashtags).map(normalizeHashtag);
    if (existing.includes(normalized)) return;

    const next = [...parseHashtags(finalHashtags), normalized].join(" ").trim();
    setFinalHashtags(next);
  }

  function replaceGeneratedHashtags() {
    if (!generated?.hashtags?.length) return;
    const next = generated.hashtags
      .map(normalizeHashtag)
      .filter(Boolean)
      .join(" ");
    setFinalHashtags(next);
  }

  function mergeGeneratedHashtags() {
    if (!generated?.hashtags?.length) return;

    const current = parseHashtags(finalHashtags)
      .map(normalizeHashtag)
      .filter(Boolean);
    const incoming = generated.hashtags.map(normalizeHashtag).filter(Boolean);
    const merged = Array.from(new Set([...current, ...incoming]));

    setFinalHashtags(merged.join(" "));
  }

  function useGeneratedAccessibility() {
    if (!generated?.accessibility_text) return;
    setFinalAccessibility(generated.accessibility_text);
  }

  const selectedHashtagSet = useMemo(() => {
    return new Set(parseHashtags(finalHashtags).map(normalizeHashtag));
  }, [finalHashtags]);

  const suggestedHashtags = useMemo(() => {
    if (!generated?.seo_keywords?.length) return [];

    return generated.seo_keywords
      .map(keywordToHashtag)
      .filter(Boolean)
      .filter((tag, index, arr) => arr.indexOf(tag) === index)
      .filter((tag) => !selectedHashtagSet.has(tag));
  }, [generated, selectedHashtagSet]);

  const effectiveCreditTemplate = useMemo(() => {
    return creditPreset === "custom"
      ? creditTemplate
      : presetToTemplate(creditPreset);
  }, [creditPreset, creditTemplate]);

  const creditsText = useMemo(() => {
    return buildCreditsText(creditEntries, effectiveCreditTemplate);
  }, [creditEntries, effectiveCreditTemplate]);

  const previewCaption = useMemo(() => {
    return [finalCaption, creditsText]
      .map((s) => s.trim())
      .filter(Boolean)
      .join("\n\n");
  }, [finalCaption, creditsText]);

  async function runGenerate(seedCaption?: string) {
    try {
      generateState.start(
        seedCaption
          ? "Generating caption variants..."
          : "Generating suggestions...",
      );

      const payload = {
        brand_voice: brandVoice,
        cta_goal: ctaGoal,
        generation_notes: generationNotes,
      };

      let resolvedPostId = numericPostId;

      if (!resolvedPostId) {
        if (!numericAssetId) {
          generateState.fail("Missing asset context.");
          return;
        }

        const created = await createPost({
          event_id: numericEventId ?? null,
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

      const generatedResult = await generatePost(resolvedPostId, seedCaption);
      setGenerated(generatedResult);

      generateState.succeed(
        seedCaption ? "Caption variants generated." : "Suggestions generated.",
      );
    } catch (err) {
      console.error(err);
      generateState.fail(
        err instanceof Error ? err.message : "Failed to generate suggestions.",
      );
    }
  }

  async function handleGenerate(eventSubmit: FormEvent<HTMLFormElement>) {
    eventSubmit.preventDefault();
    await runGenerate();
  }

  async function handleGenerateVariants() {
    if (!finalCaption.trim()) {
      generateState.fail("Add or select a final caption first.");
      return;
    }

    await runGenerate(finalCaption.trim());
  }

  async function handleSaveDraft() {
    const resolvedPostId = numericPostId || generated?.post_id;

    if (!resolvedPostId) {
      saveState.fail("Generate or create a draft before saving.");
      return;
    }

    try {
      saveState.start("Saving draft...");

      await updatePost(resolvedPostId, {
        brand_voice: brandVoice,
        cta_goal: ctaGoal,
        generation_notes: generationNotes,
        working_title: workingTitle || null,
      });

      await saveDraftContent(resolvedPostId, {
        draft_caption_current: finalCaption,
        draft_hashtags_current: finalHashtags,
        draft_accessibility_current: finalAccessibility,
      });

      saveState.succeed("Draft saved.");
    } catch (err) {
      console.error(err);
      saveState.fail(
        err instanceof Error ? err.message : "Failed to save draft.",
      );
    }
  }

  async function handleSendToApprovals() {
    const resolvedPostId = numericPostId || generated?.post_id;

    if (!resolvedPostId) {
      approvalState.fail("Missing post id.");
      return;
    }

    try {
      approvalState.start("Sending to Approvals...");

      const fullCaption = [finalCaption, creditsText]
        .map((s) => s.trim())
        .filter(Boolean)
        .join("\n\n");

      const approved = await approvePost(resolvedPostId, {
        caption_final: fullCaption,
        hashtags_final: finalHashtags.split(/\s+/).filter(Boolean),
        accessibility_text: finalAccessibility,
      });

      approvalState.succeed("Moved to Approvals.");
      alert(
        `Moved to Approvals. Approved post id: ${approved.approved_post_id}`,
      );
      navigate("/drafts");
    } catch (err) {
      console.error(err);
      approvalState.fail(
        err instanceof Error ? err.message : "Failed to send to approvals.",
      );
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

      <p className="helper-text">* Required</p>

      <div className="form-row">
        <label htmlFor="working-title">Draft Label</label>
        <input
          id="working-title"
          value={workingTitle}
          onChange={(e) => setWorkingTitle(e.target.value)}
          placeholder="e.g. A/B Test – High Energy Version"
        />
        <p className="helper-text">
          Optional. Helps distinguish multiple versions of the same post.
        </p>
      </div>

      <StatusMessage
        loading={loadState.loading}
        status={loadState.status}
        error={loadState.error}
      />

      <section aria-labelledby="preview-heading" className="draft-preview-hero">
        <h3 id="preview-heading">Preview</h3>

        <div className="draft-preview-sticky">
          <InstagramPreview
            asset={asset}
            caption={previewCaption}
            hashtags={finalHashtags}
            profileLabel="Draft Preview"
          />
        </div>
      </section>

      <section aria-labelledby="generated-heading" className="draft-generated">
        <h3 id="generated-heading">Suggestions & Draft</h3>

        {generated ? (
          <section>
            <h4>Generated Caption Options</h4>

            <div className="generated-grid">
              {[
                {
                  label: "Caption Option 1",
                  value: generated.caption_option_1,
                },
                {
                  label: "Caption Option 2",
                  value: generated.caption_option_2,
                },
                {
                  label: "Caption Option 3",
                  value: generated.caption_option_3,
                },
              ]
                .filter((option) => option.value)
                .map((option) => (
                  <div className="generated-option" key={option.label}>
                    <h5>{option.label}</h5>
                    <textarea readOnly value={option.value} />
                    <button
                      type="button"
                      onClick={() => useCaption(option.value)}
                    >
                      Use This Caption
                    </button>
                  </div>
                ))}
            </div>

            <section>
              <h4>Generated Hashtags</h4>
              <p className="helper-text">
                These are suggestions. They do not replace your draft unless you
                choose to apply them.
              </p>

              <div className="token-row">
                {(generated.hashtags || []).map((tag) => {
                  const normalized = normalizeHashtag(tag);
                  if (!normalized) return null;

                  return (
                    <span key={normalized} className="token-chip">
                      {normalized}
                    </span>
                  );
                })}
              </div>

              <div className="approval-action-row">
                <button type="button" onClick={mergeGeneratedHashtags}>
                  Merge Hashtags
                </button>
                <button type="button" onClick={replaceGeneratedHashtags}>
                  Replace Hashtags
                </button>
              </div>
            </section>

            <section>
              <h4>Generated Accessibility</h4>
              <textarea readOnly value={generated.accessibility_text || ""} />
              <div className="approval-action-row">
                <button type="button" onClick={useGeneratedAccessibility}>
                  Use Accessibility
                </button>
              </div>
            </section>
          </section>
        ) : (
          <p>
            Generate suggestions to see caption options, hashtags, and
            accessibility based on the selected media
            {event ? " and event context." : "."}
          </p>
        )}

        <section>
          <h4>Finalize Draft</h4>
          <p className="helper-text">
            Your draft content lives here. You can start writing immediately or
            generate suggestions first.
          </p>

          <div className="form-row">
            <label htmlFor="final-caption">Final Caption *</label>
            <textarea
              id="final-caption"
              value={finalCaption}
              onChange={(e) => setFinalCaption(e.target.value)}
              placeholder="Write your caption here, or generate suggestions to get started."
            />
            <p className="helper-text">
              This is the caption that will be sent forward for approval.
            </p>
          </div>

          <CreditsEditor
            entries={creditEntries}
            onEntriesChange={setCreditEntries}
            preset={creditPreset}
            onPresetChange={setCreditPreset}
            template={creditTemplate}
            onTemplateChange={setCreditTemplate}
            showStyleControls
          />

          <div className="form-row">
            <label htmlFor="final-hashtags">Final Hashtags</label>
            <textarea
              id="final-hashtags"
              value={finalHashtags}
              onChange={(e) => setFinalHashtags(e.target.value)}
            />
            <p className="helper-text">
              Optional. Space-delimited hashtags are supported here.
            </p>
          </div>

          {parseHashtags(finalHashtags).length > 0 && (
            <div className="form-row">
              <label>Current Hashtags</label>
              <div className="token-row">
                {parseHashtags(finalHashtags).map((tag) => (
                  <span key={tag} className="token-chip">
                    {normalizeHashtag(tag)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {suggestedHashtags.length > 0 && (
            <div className="form-row">
              <label>Other Hashtags?</label>
              <p className="helper-text">
                Suggested from generated SEO keywords. Click to add without
                duplicates.
              </p>
              <div className="token-row">
                {suggestedHashtags.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    className="token-chip token-chip-button"
                    onClick={() => addHashtag(tag)}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="form-row">
            <label htmlFor="final-accessibility">
              Final Accessibility Text
            </label>
            <p className="helper-text">
              Optional. Generated from media analysis. Edit this if the
              description needs correction.
            </p>
            <textarea
              id="final-accessibility"
              value={finalAccessibility}
              onChange={(e) => setFinalAccessibility(e.target.value)}
            />
          </div>

          <div className="approval-action-row">
            <button
              type="button"
              disabled={saveState.loading}
              onClick={handleSaveDraft}
            >
              {saveState.loading ? "Saving..." : "Save Draft"}
            </button>

            <button
              type="button"
              disabled={approvalState.loading}
              onClick={handleSendToApprovals}
            >
              {approvalState.loading ? "Sending..." : "Send to Approvals"}
            </button>
          </div>

          <StatusMessage
            loading={saveState.loading}
            status={saveState.status}
            error={saveState.error}
          />

          <StatusMessage
            loading={approvalState.loading}
            status={approvalState.status}
            error={approvalState.error}
          />
        </section>
      </section>

      <div className="approval-review-layout">
        <div className="approval-preview-column">
          <section aria-labelledby="context-heading">
            <h3 id="context-heading">Context</h3>

            <div className="card">
              {event ? (
                <>
                  <h4>{event.title}</h4>

                  <p>
                    <strong>Type:</strong> {event.event_type || "None"}
                  </p>
                  <p>
                    <strong>Location:</strong> {event.location || "None"}
                  </p>
                  <p>
                    <strong>Recap:</strong>{" "}
                    {event.recap || "No recap provided."}
                  </p>
                  <p>
                    <strong>Guidance:</strong>{" "}
                    {event.event_guidance || "No guidance provided."}
                  </p>
                </>
              ) : (
                <>
                  <h4>No Event Context</h4>
                  <p className="helper-text">
                    This draft is being generated from the asset alone. Event
                    context is optional.
                  </p>
                </>
              )}

              {asset?.media_type === "video" && (
                <>
                  <p>
                    <strong>Analysis Mode:</strong> Visual analysis from sampled
                    frames
                  </p>

                  {asset.vision_summary_generated && (
                    <>
                      <p>
                        <strong>Video Summary:</strong>{" "}
                        {asset.vision_summary_generated}
                      </p>
                      <p className="helper-text">
                        Generated from sampled video frames. You can reanalyze
                        if this misses the subject, setting, or action.
                      </p>
                    </>
                  )}
                </>
              )}

              {asset?.media_type === "image" &&
                asset?.vision_summary_generated && (
                  <>
                    <p>
                      <strong>Analysis Mode:</strong> Image analysis
                    </p>
                    <p>
                      <strong>Image Summary:</strong>{" "}
                      {asset.vision_summary_generated}
                    </p>
                  </>
                )}

              {event?.id && asset?.id && (
                <p>
                  <Link to={`/events/${event.id}`}>
                    Reanalyze this media from the event page
                  </Link>
                </p>
              )}

              {asset && <AssetPreview asset={asset} />}
            </div>
          </section>
        </div>

        <div className="approval-details-column">
          <section aria-labelledby="settings-heading">
            <h3 id="settings-heading">Draft Settings</h3>

            <form onSubmit={handleGenerate}>
              <div className="form-row">
                <label htmlFor="brand-voice">Brand Voice *</label>
                <input
                  id="brand-voice"
                  value={brandVoice}
                  onChange={(e) => setBrandVoice(e.target.value)}
                  required
                />
                <p className="helper-text">
                  Shapes the tone and personality of the caption.
                </p>
              </div>

              <div className="form-row">
                <label htmlFor="cta-goal">CTA Goal *</label>
                <input
                  id="cta-goal"
                  value={ctaGoal}
                  onChange={(e) => setCtaGoal(e.target.value)}
                  required
                />
                <p className="helper-text">
                  Example: drive follows, inquiries, bookings, or clicks.
                </p>
              </div>

              <div className="form-row">
                <label htmlFor="generation-notes">Generation Notes</label>
                <textarea
                  id="generation-notes"
                  value={generationNotes}
                  onChange={(e) => setGenerationNotes(e.target.value)}
                />
                <p className="helper-text">
                  Optional. Add extra direction, constraints, or ideas for this
                  specific draft.
                </p>
              </div>

              <div className="approval-action-row">
                <button type="submit" disabled={generateState.loading}>
                  {generateState.loading
                    ? "Generating..."
                    : "Generate Suggestions"}
                </button>

                <button
                  type="button"
                  disabled={generateState.loading}
                  onClick={handleGenerateVariants}
                >
                  {generateState.loading
                    ? "Generating..."
                    : "Generate Variants from Final Caption"}
                </button>
              </div>
            </form>

            <StatusMessage
              loading={generateState.loading}
              status={generateState.status}
              error={generateState.error}
            />
          </section>
        </div>
      </div>
    </section>
  );
}
