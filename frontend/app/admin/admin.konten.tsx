"use client";

import { useState } from "react";
import { usePermission } from "./admin-context";
import Education from "./admin.edukasi";
import Recommendations from "./admin.rekomendasi-tindakan";
import styles from "./admin.module.css";

export default function ContentPage() {
  const [tab, setTab] = useState<"education" | "recommendations">("education");
  const canManageRecommendations = usePermission("recommendations.manage");
  return (
    <>
      <div className={styles.featureTabs} role="tablist" aria-label="Pengelolaan konten">
        <button
          className={tab === "education" ? styles.selected : ""}
          onClick={() => setTab("education")}
        >
          Konten edukasi
        </button>
        {canManageRecommendations && (
          <button
            className={tab === "recommendations" ? styles.selected : ""}
            onClick={() => setTab("recommendations")}
          >
            Rekomendasi tindakan
          </button>
        )}
      </div>
      {tab === "education" ? <Education /> : <Recommendations />}
    </>
  );
}
