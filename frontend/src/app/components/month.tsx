'use client'
import { keycloak } from "../keycloak";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import styles from "@/styles/Month.module.css";
import { useParams } from "next/navigation";
export default function Month(){
    const params = useParams<{year:string,month:string}>();
    const router = useRouter();
    function goToDay(day:number){
      router.push(`/analysis/${params.year}/${params.month}/${day}`)
    }
    const [length,setLength] = useState(0)
        const days = Array.from({ length: length }, (_, i) => i + 1).splice(length-10,length)
        return (
        // <section className={styles.wrapper}>
          // <div className={styles.card}>
          <div>
            {!keycloak.authenticated ? (
              <>
              
              <div className={styles.parentTilesGrid}>
                <div className={styles.tileChoose} onMouseEnter={()=>setLength(10)}>Dni 01 - 10</div>
                <div className={styles.tileChoose} onMouseEnter={()=>setLength(20)}>Dni 11 - 20</div>
                <div className={styles.tileChoose} onMouseEnter={()=>setLength(30)}>Dni 21 - 31</div>
              </div>
              <div className={styles.tilesGrid}>
                {days.map((day) => (
                  <div key={day} className={styles.tile}>
                    <div className={styles.tileTitle}>Dzień {day}</div>
                    <button className={styles.tileBtn} onClick={() => goToDay(day)}>Zobacz</button>
                  </div>
                ))}
              </div>
              </>
            ) : (
              <button
                className={styles.primaryBtn}
                onClick={() => keycloak.login()}
              >
                Zaloguj się do systemu
              </button>
            )}
          </div>
        // </section>
      );
}