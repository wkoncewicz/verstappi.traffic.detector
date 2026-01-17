import { use, useEffect, useState } from "react";
import {keycloak} from "../keycloak";
import axios from "axios";
export default function LoggedUser() {
    const url = `https://verstappi.pl:5000/getDataBaseData`
    // await keycloak.updateToken(30);
    // headers: {
    //   Authorization: `Bearer ${keycloak.token}`
    // }
    const [data,fetchData] = useState()
    return (
    <main>
      <div>Witaj w Verstappi</div>

      <button onClick={() => keycloak.logout()}>Wyloguj się</button>
    </main>
  );
}
