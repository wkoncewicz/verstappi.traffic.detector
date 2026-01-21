'use client'
import { keycloak } from "@/app/keycloak";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import styles from "@/styles/Month.module.css";
import { useParams } from "next/navigation";
import axios from "axios";
import BasicChart from "./testChart";
import HlsPlayer from "./HlsPlayer";
export default function Month(){
    const [data, setData] = useState<any[]>([]);
    const [days,setDays] = useState<string[]>([]);
    const params = useParams<{year:string,month:string}>();
    const router = useRouter();
    function goToDay(day:string){
      router.push(`/analysis/${params.year}/${params.month}/${day}`)
    }
    const url = `https://verstappi.pl:31514/api/traffic`
      useEffect(()=>{
      const load = async() =>{
        try{
          await keycloak.updateToken(30)
          const res = await axios.get(`${url}/${params.year}/${params.month}`,{
            headers: {
              Authorization: `Bearer ${keycloak.token}`
            }
          })
          const chartData = Object.entries(res.data).map(([day, v]: any) => {
            const inSum  = v.carsIn + v.trucksIn + v.busesIn + v.motorcyclesIn;
            const outSum = v.carsOut + v.trucksOut + v.busesOut + v.motorcyclesOut;
            return { name: day, in: inSum, out: outSum, ...v };
          });
          setData(chartData)
          setDays(Object.keys(res.data))
        }
        catch(err){
          console.log(err)
        }
      }
      load()
    },[])
    const [length,setLength] = useState(0)
        return (
  <div>
    {keycloak.authenticated ? (
      <div className={styles.page}>

        <div className={styles.topRowWrap}>
          <div className={styles.topRow}>

            <div className={styles.streamBox}>
              <HlsPlayer src="https://wzmedia.dot.ca.gov/D3/99_JCT162E_BUT99_NB.stream/chunklist_w646513265.m3u8" />
            </div>

            <div className={styles.rightBox}>
              <h1 className={styles.heading}>{params.month}</h1>

              <div className={styles.parentTilesGrid}>
                <div className={styles.tileChoose} onMouseEnter={() => setLength(10)}>Dni 01 - 10</div>
                <div className={styles.tileChoose} onMouseEnter={() => setLength(20)}>Dni 11 - 20</div>
                <div className={styles.tileChoose} onMouseEnter={() => setLength(30)}>Dni 21 - 31</div>
              </div>

              <div className={styles.tilesGrid}>
                {Object.keys(days).map((day) => (
                  <div key={day} className={styles.tile}>
                    <div className={styles.tileTitle}>Dzień {day}</div>
                    <button className={styles.tileBtn} onClick={() => goToDay(day)}>Zobacz</button>
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
);

}