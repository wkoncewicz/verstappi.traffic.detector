"use client";

import styles from "@/styles/Navbar.module.css";
import { keycloak } from "@/app/keycloak";
import { useRouter } from "next/navigation";
export default function Navbar() {
  const router = useRouter()
  function goToMain(){
    router.push('/logged-user')
  }
  function goToHelp(){
    router.push('/help')
  }
  return (
    <header className={styles.nav}>
      <div className={styles.inner}>
        <div className={styles.brand}>
          <div className={styles.text}>
            <a className={styles.name} onClick={() => goToMain()}>Verstappi.pl</a>
          </div>
        </div>

        <nav className={styles.links} aria-label="Nawigacja">
            {keycloak.authenticated ? (
                <>
                <a className={styles.link} onClick={()=>goToMain()}>Strona główna</a>
                <a className={styles.link} onClick={()=>goToHelp()}>Pomoc</a>
                <button
                    className={styles.primaryBtn}
                    onClick={() => keycloak.logout()}
                  >
                    Wyloguj się
                </button>
                </>
            ) : (<div>Login</div>)}
        </nav>
      </div>
    </header>
  );
}
