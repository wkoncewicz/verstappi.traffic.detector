'use client'
import { keycloak } from "@/app/keycloak";
import { useRouter } from "next/navigation";
import styles from "@/styles/Day.module.css";
import { useParams } from "next/navigation";
import axios from "axios";
import { useEffect, useState } from "react";
import BasicChart from "./testChart";
import HlsPlayer from "./HlsPlayer";
export default function Day(){
    const params = useParams<{year:string,month:string,day:string}>();
    const router = useRouter();
    const [data,setData] = useState<any[]>([]);
    const url = `https://verstappi.pl:31514/api/traffic`
    useEffect(()=>{
      const load = async() =>{
        try{
          await keycloak.updateToken(30)
          const res = await axios.get(`${url}/${params.year}/${params.month}/${params.day}`,{
            headers: {
              Authorization: `Bearer ${keycloak.token}`
            }
          })
          const chartData = Object.entries(res.data.data)
          .sort(([a], [b]) => new Date(a).getTime() - new Date(b).getTime())
          .map(([ts, v]: any) => {
            const inSum =
              (Number(v.carsIn) || 0) +
              (Number(v.trucksIn) || 0) +
              (Number(v.busesIn) || 0) +
              (Number(v.motorcyclesIn) || 0);

            const outSum =
              (Number(v.carsOut) || 0) +
              (Number(v.trucksOut) || 0) +
              (Number(v.busesOut) || 0) +
              (Number(v.motorcyclesOut) || 0);

            const label = String(v.timeStamp).slice(11, 16);

            return { name: label, ts, in: inSum, out: outSum, ...v };
          });
          setData(chartData)
          // console.log(res.data)
        }
        catch(err){
          console.log(err)
        }
      }
      load()
    },[])
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
                <h1 className={styles.heading}>
                  {params.year}/{params.month}/{params.day}
                </h1>
                <div className={styles.sub}>
                  Szczegóły dla wybranego dnia
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