import Keycloak from "keycloak-js";

export const keycloak = new Keycloak({
  url: "http://localhost:31514/",
  realm: "RealtimeTraffic",
  clientId: "VerstappiClient",
});
