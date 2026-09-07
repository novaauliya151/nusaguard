"use client";

import { useState } from "react";
import { usePermission } from "./admin-context";
import Validation from "./admin.validasi-nseae";
import Lexicons from "./admin.leksikon-nseae";
import styles from "./admin.module.css";

export default function NseaePage() {
  const [tab, setTab] = useState<"validation" | "lexicon">("validation");
  const canViewLexicon = usePermission("lexicons.view");
  return (
    <>
      <div className={styles.featureTabs} role="tablist" aria-label="Pengelolaan N-SEAE">
        <button
          className={tab === "validation" ? styles.selected : ""}
          onClick={() => setTab("validation")}
        >
          Validasi
        </button>
        {canViewLexicon && (
          <button
            className={tab === "lexicon" ? styles.selected : ""}
            onClick={() => setTab("lexicon")}
          >
            Leksikon
          </button>
        )}
      </div>
      {tab === "validation" ? <Validation /> : <Lexicons />}
    </>
  );
}
