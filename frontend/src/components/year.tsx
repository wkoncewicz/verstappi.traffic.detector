'use client'
import { keycloak } from "@/app/keycloak";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import styles from "@/styles/Year.module.css";
import { useParams } from "next/navigation";
import axios from 'axios';
import BasicChart from "./testChart";
import HlsPlayer from "./HlsPlayer";
export default function Year(){  
    const params = useParams<{year:string}>();
    const router = useRouter();
    const url = `https://verstappi.pl:31514/api/traffic`
    const [data, setData] = useState<any[]>([]);
    const [months, setMonths] = useState<string[]>([]);
    useEffect(()=>{
      const load = async() =>{
        try{
          await keycloak.updateToken(30)
          const res = await axios.get(`${url}/${params.year}`,{
            headers: {
              Authorization: `Bearer ${keycloak.token}`
            }
          })
          const chartData = Object.entries(res.data.data).map(([day, v]: any) => {
            const inSum  = v.carsIn + v.trucksIn + v.busesIn + v.motorcyclesIn;
            const outSum = v.carsOut + v.trucksOut + v.busesOut + v.motorcyclesOut;
            return { name: day, in: inSum, out: outSum,sum:inSum+outSum, ...v };
          });
          // console.log(res.data)
          // console.log(chartData)
          setData(chartData)
          setMonths(Object.keys(res.data.data))
        }
        catch(err){
          console.log(err)
        }
      }
      load()
    },[])
    function goToMonth(month:string){
      router.push(`/analysis/${params.year}/${month}`)
    }
    return (
          <div>
            {keycloak.authenticated ? (
                <div className={styles.page}>
                  <div className={styles.topRowWrap}>
                  <div className={styles.topRow}>
                    <div className={styles.streamBox}>
                      <HlsPlayer src="https://wzmedia.dot.ca.gov/D3/99_JCT162E_BUT99_NB.stream/chunklist_w646513265.m3u8" />
                    </div>

                    <div className={styles.tilesBox}>
                      <div className={styles.tilesGrid}>
                        {months.map((month) => (
                          <div key={month} className={styles.tile}>
                            <div className={styles.tileTitle}>{month}</div>
                            <button onClick={() => goToMonth(month)}>Zobacz więcej</button>
                          </div>
                        ))}
                      </div>
                    </div>
                    </div>
                  </div>

                  <div className={styles.chartWrap}>
                    <BasicChart data={data} />
                  </div>
                </div>
            ) : (
              <div>Musisz być zalogowany!</div>
            )}
          </div>
    )
}