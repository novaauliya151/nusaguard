"use client";

import { useState } from "react";
import Model from "./admin.model";
import System from "./admin.sistem";
import styles from "./admin.module.css";

export default function MonitoringPage() {
  const [tab, setTab] = useState<"model" | "system">("model");
  return (
    <>
      <div className={styles.featureTabs} role="tablist" aria-label="Monitoring model dan sistem">
        <button className={tab === "model" ? styles.selected : ""} onClick={() => setTab("model")}>
          Model AI
        </button>
        <button
          className={tab === "system" ? styles.selected : ""}
          onClick={() => setTab("system")}
        >
          Status sistem
        </button>
      </div>
      {tab === "model" ? <Model /> : <System />}
    </>
  );
}
