"use client";

import { ReactNode, useEffect, useState } from "react";
import { keycloak } from "../keycloak";

export default function KeycloakProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);

  // useEffect(() => {
  //   keycloak.init({
  //       onLoad: "check-sso",
  //       pkceMethod: "S256",
  //       checkLoginIframe: false,
  //   })
  //           .then((authenticated) => {
  //       // console.log("Authenticated:", authenticated);
  //       // console.log("Token:", keycloak.token);
  //       // console.log("Parsed token:", keycloak.tokenParsed);

  //       setReady(true);
  //     });
  // }, []);

  if (!ready) return <>Ładowanie...</>;

  return <>{children}</>;
}
