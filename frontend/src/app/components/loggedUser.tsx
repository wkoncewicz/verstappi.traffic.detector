import { use, useEffect, useState } from "react";
import {keycloak} from "../keycloak";
import axios from "axios";
import styles from "@/styles/LoggedUser.module.css";
import { useRouter } from "next/navigation";
export default function LoggedUser() {
    const url = `https://verstappi.pl:5000/getDataBaseData`
    // await keycloak.updateToken(30);
    // headers: {
    //   Authorization: `Bearer ${keycloak.token}`
    // }
    const years = ['2026']
    const [data,fetchData] = useState()
    const router = useRouter();
      useEffect(() => {
        if (keycloak.authenticated) {
          router.push("/logged-user");
        }
      }, [router]);
    function goToYear(year:string){
      router.push(`/analysis/${year}`)
    }
    return (
      <>
        <div className={styles.page}>
          <div className={styles.container}>
          <div>
            {!keycloak.authenticated ? (
              <>
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
              <button
                className={styles.primaryBtn}
                onClick={() => keycloak.login()}
              >
                Zaloguj się do systemu
              </button>
            )}
          </div>
          </div>
          </div>
      </>
      );
}
