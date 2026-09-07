"use client";

import { useState } from "react";
import { usePermission } from "./admin-context";
import Candidates from "./admin.kandidat-dataset";
import ImportDataset from "./admin.import-dataset";
import Distribution from "./admin.distribusi-dataset";
import styles from "./admin.module.css";

export default function DatasetPage() {
  const [tab, setTab] = useState<"candidates" | "import" | "distribution">("candidates");
  const canImport = usePermission("datasets.import");
  return (
    <>
      <div className={styles.featureTabs} role="tablist" aria-label="Pengelolaan dataset">
        <button
          className={tab === "candidates" ? styles.selected : ""}
          onClick={() => setTab("candidates")}
        >
          Kandidat
        </button>
        {canImport && (
          <button
            className={tab === "import" ? styles.selected : ""}
            onClick={() => setTab("import")}
          >
            Import CSV
          </button>
        )}
        <button
          className={tab === "distribution" ? styles.selected : ""}
          onClick={() => setTab("distribution")}
        >
          Distribusi
        </button>
      </div>
      {tab === "candidates" ? (
        <Candidates />
      ) : tab === "import" ? (
        <ImportDataset />
      ) : (
        <Distribution />
      )}
    </>
  );
}
