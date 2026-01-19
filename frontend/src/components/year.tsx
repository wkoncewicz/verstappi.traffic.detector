'use client'
import { keycloak } from "@/app/keycloak";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import styles from "@/styles/Year.module.css";
import { useParams } from "next/navigation";
import axios from 'axios';
export default function Year(){
    const params = useParams<{year:string}>();
    const router = useRouter();
    const url = "https://verstappi.pl:5000/traffic"
    const [data,setData] = useState([])
    const months = ['Styczeń','Luty','Marzec','Kwiecień','Maj','Czerwiec','Lipiec','Sierpień','Wrzesień','Październik','Listopad','Grudzień']
    useEffect(()=>{
      const load = async() =>{
        try{
          await keycloak.updateToken(30)
          const res = await axios.get(`${url}`,{
            headers: {
              Authorization: `Bearer ${keycloak.token}`
            }
          })
          setData(res.data)
        }
        catch(err){
          console.log(err)
        }
      }
      load()
    },[])
    useEffect(() => {
        if (keycloak.authenticated) {
            router.push("/logged-user");
        }
    }, [router]);
    function goToMonth(month:string){
      router.push(`/analysis/${params.year}/${month}`)
    }
    return (
          <div>
            {keycloak.authenticated ? (
              <>
                <div className={styles.tilesGrid}>
                  {months.map((month)=>(
                    <div className={styles.tile}>
                      <div className={styles.tileTitle}>{month}</div>
                      <button onClick={()=>goToMonth(month)}>Zobacz więcej</button>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div>Musisz być zalogowany!</div>
            )}
          </div>
    )
}