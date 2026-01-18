"use client";

import styles from "@/styles/Footer.module.css";

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.left}>
          <div className={styles.top}>© 2026 Verstappi</div>
        </div>
        <a href='https://github.com/wiktorkapusniak' className={styles.muted}>Wiktor Kapuśniak</a>
        <a href='https://github.com/wkoncewicz' className={styles.muted}>Wiktor Koncewicz</a>
        <a href='https://github.com/milankwiatkowski' className={styles.muted}>Milan Kwiatkowski</a>
        <div className={styles.right}>
          <span className={styles.badge}>PROD</span>
          <span className={styles.sep} aria-hidden="true">•</span>
          <span className={styles.muted}>v1.0</span>
        </div>
      </div>
    </footer>
  );
}
