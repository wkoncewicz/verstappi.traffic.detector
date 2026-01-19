'use client'
import { keycloak } from "@/app/keycloak";
import { useRouter } from "next/navigation";
import styles from "@/styles/Day.module.css";
import { useParams } from "next/navigation";
export default function Day(){
    const params = useParams<{year:string,month:string}>();
    const router = useRouter();
        return (
        // <section className={styles.wrapper}>
          // <div className={styles.card}>
          <div>
            {keycloak.authenticated ? (
              <>
                <div>godziny</div>
              </>
            ) : (
              <div>Musisz być zalogowany!</div>
            )}
          </div>
        // </section>
      );
}