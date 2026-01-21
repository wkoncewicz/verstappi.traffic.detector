import { use, useEffect, useState } from "react";
import {keycloak} from "@/app/keycloak";
import axios from "axios";
import styles from "@/styles/LoggedUser.module.css";
import { useRouter } from "next/navigation";
import HlsPlayer from "./HlsPlayer";
export default function LoggedUser() {
    const years = ['2026']
    const router = useRouter();
    function goToYear(year:string){
      router.push(`/analysis/${year}`)
    }
    return (
      <>
        <div className={styles.page}>
          <div className={styles.container}>
          <div>
            {keycloak.authenticated ? (
              <>
              <div className={styles.streamBox}>
              <HlsPlayer src="https://wzmedia.dot.ca.gov/D3/99_JCT162E_BUT99_NB.stream/chunklist_w646513265.m3u8" />
            </div>
                <div className={styles.tilesGrid}>
                  {years.map((year)=>(
                    <div className={styles.tile}>
                      <div className={styles.tileTitle}>{year}</div>
                      <button onClick={()=>goToYear(year)}>Zobacz więcej</button>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div>Musisz być zalogowany!</div>
            )}
          </div>
          </div>
          </div>
      </>
      );
}
