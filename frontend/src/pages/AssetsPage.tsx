import { useEffect, useState } from "react";
import { listAssets } from "../api/assets";
import { listEvents } from "../api/events";
import type { AssetRecord, EventRecord } from "../types/api";
import UploadStagingPanel from "../components/UploadStagingPanel";
import AssetLibraryPanel from "../components/AssetLibraryPanel";

export default function AssetsPage() {
  const [assets, setAssets] = useState<AssetRecord[]>([]);
  const [events, setEvents] = useState<EventRecord[]>([]);

  async function loadData(showLoadingMessage = true) {
    try {
      const [assetData, eventData] = await Promise.all([
        listAssets(),
        listEvents(),
      ]);

      setAssets(assetData);
      setEvents(eventData);
    } catch (err) {
      console.error(err);
    }
  }

  useEffect(() => {
    void loadData();
  }, []);

  return (
    <section aria-labelledby="assets-heading">
      <div className="page-header">
        <div>
          <h2 id="assets-heading">Assets</h2>
          <p>Manage uploaded media, analysis, and event associations.</p>
        </div>
      </div>

      <UploadStagingPanel onUploadComplete={loadData} />

      <AssetLibraryPanel assets={assets} events={events} onRefresh={loadData} />
    </section>
  );
}
