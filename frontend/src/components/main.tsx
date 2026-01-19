"use client";

import { useRouter } from "next/navigation";
import { keycloak } from "@/app/keycloak";
import styles from "@/styles/Main.module.css";
import { useEffect } from "react";

export default function Main() {
  const router = useRouter();
  useEffect(() => {
    if (keycloak.authenticated) {
      router.push("/logged-user"); // albo "/profile"
    }
  }, [router]);
  return (
    <main className={styles.page}>
      {/* <section className={styles.panel}>*/}

        <div className={styles.body}>
          {keycloak.authenticated && (
            <button
              className={styles.loginBtn}
              onClick={() => keycloak.login()}
            >
              Zaloguj się do systemu
            </button>
          )}
        </div>

      {/* </section> */}
    </main>
  );
}
