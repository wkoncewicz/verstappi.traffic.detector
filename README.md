# Verstappi.pl — System monitorowania ruchu drogowego w czasie rzeczywistym

> Projekt zespołowy — rozpoznawanie i zliczanie pojazdów z kamer drogowych przy użyciu modelu YOLOv8, z agregacją danych w MongoDB i prezentacją wyników w aplikacji webowej zabezpieczonej Keycloakiem. Całość wdrożona na klastrze Kubernetes.

---

## Spis treści

1. [Opis systemu](#1-opis-systemu)
2. [Architektura](#2-architektura)
3. [Komponenty](#3-komponenty)
   - [Detektor](#31-detektor)
   - [Backend (API)](#32-backend-api)
   - [Frontend](#33-frontend)
   - [Baza danych (MongoDB)](#34-baza-danych-mongodb)
   - [Keycloak (autoryzacja)](#35-keycloak-autoryzacja)
   - [NGINX Ingress & cert-manager](#36-nginx-ingress--cert-manager)
4. [Model YOLOv8 — opis i warianty](#4-model-yolov8--opis-i-warianty)
5. [Modele danych (MongoDB)](#5-modele-danych-mongodb)
6. [API — dokumentacja endpointów](#6-api--dokumentacja-endpointów)
7. [Wdrożenie na Kubernetes](#7-wdrożenie-na-kubernetes)
8. [Przewodnik dewelopera](#8-przewodnik-dewelopera)
9. [Zmienne środowiskowe](#9-zmienne-środowiskowe)
10. [Stos technologiczny](#10-stos-technologiczny)

---

## 1. Opis systemu

Verstappi.pl to system analizy ruchu drogowego w czasie rzeczywistym. Kamera drogowa transmituje strumień HLS, który jest pobierany przez moduł Detektora. Detektor co klatkę uruchamia model **YOLOv8m** śledzący pojazdy (samochody, motocykle, autobusy, ciężarówki) i wykrywa moment przekroczenia wirtualnej linii rozdzielającej dwa kierunki ruchu. Zliczone dane są agregowane co 10 minut i zapisywane do bazy MongoDB poprzez REST API. Zalogowany użytkownik może przeglądać wykresy i statystyki z podziałem na lata → miesiące → dni → 10-minutowe interwały.

---

## 2. Architektura

```
Kamera HLS ──► Detektor (YOLOv8m + VLC/FFmpeg)
                        │ POST /api/traffic  (X-Detector-Token)
                        ▼
               Backend Flask API ──► MongoDB 7.0
                        │
               NGINX Ingress (verstappi.pl)
                /api  ──► Backend :5000
                /     ──► Frontend :3000
                /keycloak ──► Keycloak :8080
                        │
               Frontend (Next.js 16)
                 - Keycloak JWT auth
                 - HLS player (hls.js)
                 - Wykresy (Recharts)
```

Wszystkie komponenty działają jako pody w klastrze **Kubernetes** na serwerze VPS OVH. Certyfikaty TLS są wystawiane automatycznie przez **cert-manager** (Let's Encrypt). Dane Keycloaka i bazy MongoDB są utrwalane na wolumenach PersistentVolume.

---

## 3. Komponenty

### 3.1 Detektor

**Lokalizacja:** `backend/detector/`

Detektor to autonomiczny proces Pythona odpowiedzialny za:

- Pobieranie klatek ze strumienia HLS (dwa tryby: `--reader vlc` lub `--reader ffmpeg`)
- Uruchomienie modelu `yolov8m.pt` w trybie **śledzenia** (`model.track(...)`)
- Zliczanie pojazdów przekraczających wirtualną linię poprzeczną (zdefiniowaną punktami `lane_a` i `lane_b`)
- Wysyłanie zagregowanych danych co 10 minut do backendu przez HTTP POST

**Czytniki strumienia:**

| Czytnik | Klasa                | Opis                                                                                                                      |
| ------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| VLC     | `VLCStreamReader`    | Pobiera klatki snapchotami przez `libvlc`; odporny na przerwy w strumieniu; utrzymuje deque ostatnich N poprawnych klatek |
| FFmpeg  | `FFmpegStreamReader` | Rura `stdout` z procesu `ffmpeg`; niższe opóźnienie; wymaga obecności `ffmpeg` w `$PATH`                                  |

**Logika zliczania pojazdów:**

```
lane_mid_y = (lane_a.y + lane_b.y) // 2

Pojazd wjeżdżający (In):  poprzednia pozycja y < lane_mid_y < aktualna y
Pojazd wyjeżdżający (Out): poprzednia pozycja y > lane_mid_y > aktualna y
```

Każdy track_id jest rejestrowany tylko raz, aby uniknąć wielokrotnego liczenia tego samego pojazdu. Zliczanie odbywa się wyłącznie dla `mid_x > max_x` (500 px), co eliminuje pojazdy daleko od kamery.

```
results = model.track(frame, persist=True, classes=[2,3,5,7], conf=0.3, verbose=False)
```

```
            mid_x, mid_y = (x1+x2)//2, (y1+y2)//2

            if track_id in last_position and cls in allowed and mid_x > max_x:
                last_x, last_y = last_position[track_id]

                if mid_y > lane_mid_y > last_y:
                    if track_id not in vehicles[vehicleIds_key]:
                        vehicles[vehicleIn_key] += 1
                        vehicles[vehicleIds_key].add(track_id)
                        print("Vehicle detected")

                elif mid_y < lane_mid_y < last_y:
                    if track_id not in vehicles[vehicleIds_key]:
                        vehicles[vehicleOut_key] += 1
                        vehicles[vehicleIds_key].add(track_id)
                        print("Vehicle detected")

            last_position[track_id] = (mid_x, mid_y)
```

**Klasy COCO używane przez detektor:**

| ID klasy COCO | Typ pojazdu           |
| ------------- | --------------------- |
| 2             | car (samochód)        |
| 3             | motorcycle (motocykl) |
| 5             | bus (autobus)         |
| 7             | truck (ciężarówka)    |

**Zależności Pythona (`detector/requirements.txt`):**

```
ultralytics==8.3.228
numpy==2.2.6
opencv-python-headless==4.10.0.84
python-vlc==3.0.21203
lap>=0.5.12
mongoengine==0.29.1
```

---

### 3.2 Backend (API)

**Lokalizacja:** `backend/app/`  
**Framework:** Flask + MongoEngine  
**Port:** `5000`  
**Obraz Docker:** `underwoodsteam/prod-backend:latest`

Backend jest aplikacją Flask udostępniającą REST API do zapisu i odczytu danych o ruchu. Autoryzacja dostępu do endpointu zapisu odbywa się przez nagłówek `X-Detector-Token` (shared secret). Endpointy odczytu chronione są przez JWT Keycloaka weryfikowany po stronie Frontendu.

Każda operacja jest logowana do kolekcji MongoDB z unikalnym identyfikatorem transakcji (`uuid7`).

---

### 3.3 Frontend

**Lokalizacja:** `frontend/`  
**Framework:** Next.js 16 + React 19 + TypeScript  
**Port:** `3000`  
**Obraz Docker:** `underwoodsteam/prod-frontend:latest`

Aplikacja webowa z następującymi widokami:

| Ścieżka                          | Widok        | Opis                                             |
| -------------------------------- | ------------ | ------------------------------------------------ |
| `/`                              | `Main`       | Strona główna — przekierowanie, jeśli zalogowany |
| `/logged-user`                   | `LoggedUser` | Lista dostępnych lat, podgląd streamu            |
| `/analysis/[year]`               | `Year`       | Wykres roczny + kafelki miesięcy                 |
| `/analysis/[year]/[month]`       | `Month`      | Wykres miesięczny + kafelki dni                  |
| `/analysis/[year]/[month]/[day]` | `Day`        | Wykres dzienny (10-min interwały)                |
| `/help`                          | `Help`       | Strona pomocy                                    |

**Kluczowe biblioteki:**

| Biblioteka    | Wersja | Zastosowanie                                             |
| ------------- | ------ | -------------------------------------------------------- |
| `next`        | 16.1.1 | Framework SSR/CSR                                        |
| `react`       | 19.2.3 | UI                                                       |
| `keycloak-js` | 26.2.1 | Autoryzacja OIDC                                         |
| `hls.js`      | 1.6.15 | Odtwarzacz HLS (fallback dla browsers bez natywnego HLS) |
| `recharts`    | 3.6.0  | Wykresy liniowe                                          |
| `axios`       | 1.13.2 | HTTP client                                              |

**Autoryzacja Keycloak:**

```typescript
// frontend/src/app/keycloak.ts
export const keycloak = new Keycloak({
  url: "https://verstappi.pl:31514/keycloak",
  realm: "RealtimeTraffic",
  clientId: "VerstappiClient",
});
```

Przed każdym wywołaniem API token jest odświeżany (`keycloak.updateToken(30)`), a następnie przesyłany w nagłówku `Authorization: Bearer <token>`.

---

### 3.4 Baza danych (MongoDB)

**Wersja:** MongoDB 7.0  
**Typ wdrożenia:** Kubernetes `StatefulSet` (1 replika)  
**Port:** `27017`  
**Utrwalanie danych:** `PersistentVolumeClaim`

MongoDB przechowuje trzy kolekcje:

- **`traffic`** — surowe odczyty co 10 minut
- **`daily_traffic`** — agregaty dobowe (generowane automatycznie o 00:00)
- **`logs`** — logi aplikacyjne z backendu (service, level, message, transactionId)

Połączenie konfigurowane przez zmienne środowiskowe `DB_HOST`, `DB_USER`, `DB_PASSWORD` wstrzykiwane przez Kubernetes Secret.

---

### 3.5 Keycloak (autoryzacja)

**Wersja:** `quay.io/keycloak/keycloak:26.4.6`  
**Port:** `8080`  
**Tryb uruchomienia:** `start-dev`  
**Realm:** `RealtimeTraffic`  
**Client:** `VerstappiClient`

Keycloak pełni rolę Identity Provider (IdP) zgodnego z protokołem OIDC/OAuth2. Dane konfiguracyjne Keycloaka są utrwalane na wolumenie PVC (`/opt/keycloak/data`). Keycloak jest wystawiony za NGINX Ingress pod ścieżką `/keycloak`.

---

### 3.6 NGINX Ingress & cert-manager

**Plik:** `certmanager/ingress.yml`

NGINX Ingress Controller kieruje ruch przychodzący na domenę `verstappi.pl`:

| Ścieżka          | Serwis             | Port |
| ---------------- | ------------------ | ---- |
| `/api/(.*)`      | `backend-service`  | 5000 |
| `/keycloak/(.*)` | `keycloak-service` | 8080 |
| `/(.*)`          | `frontend-service` | 3000 |

Certyfikat TLS dla domeny `verstappi.pl` jest automatycznie wystawiany i odnawiany przez **cert-manager** z użyciem ClusterIssuer `letsencrypt-prod`.

---

## 4. Model YOLOv8 — opis i warianty

### Czym jest YOLO?

**YOLO** (You Only Look Once) to rodzina modeli do detekcji obiektów w czasie rzeczywistym. W odróżnieniu od podejść dwuetapowych (np. R-CNN), YOLO wykonuje detekcję w jednym przejściu przez sieć neuronową, co zapewnia bardzo wysoką szybkość działania przy zachowaniu dobrej dokładności.

**YOLOv8** (Ultralytics, 2023) to ósma generacja architektury, wprowadzająca:

- nową głowicę detekcyjną **anchor-free** (bez predefiniowanych kotwic)
- modularne bloki **C2f** (Cross Stage Partial with 2 bottlenecks)
- ujednolicone API dla detekcji, segmentacji, klasyfikacji i śledzenia obiektów
- wbudowany tracker **BoT-SORT** / **ByteTrack** (`model.track()`)

### Warianty YOLOv8

Ultralytics oferuje pięć rozmiarów modelu o rosnącej złożoności:

| Wariant    | Plik         | Parametry | GFLOPs | mAP50-95 (COCO) | Prędkość (A100, ms) |
| ---------- | ------------ | --------- | ------ | --------------- | ------------------- |
| **Nano**   | `yolov8n.pt` | ~3.2 M    | ~8.7   | 37.3            | ~0.99               |
| **Small**  | `yolov8s.pt` | ~11.2 M   | ~28.6  | 44.9            | ~1.20               |
| **Medium** | `yolov8m.pt` | ~25.9 M   | ~78.9  | 50.2            | ~1.83               |
| **Large**  | `yolov8l.pt` | ~43.7 M   | ~165.2 | 52.9            | ~2.39               |
| **XLarge** | `yolov8x.pt` | ~68.2 M   | ~257.8 | 53.9            | ~3.53               |

> Wartości mAP i prędkości podane dla obrazów 640×640 na GPU NVIDIA A100. Wyniki mogą się różnić w zależności od sprzętu i danych.

### Szczegółowe porównanie

**YOLOv8n (Nano)**

- Najmniejszy i najszybszy wariant, dedykowany do urządzeń brzegowych (edge devices), mikrokontrolerów, Raspberry Pi
- Niska dokładność przy małych obiektach i w trudnych warunkach oświetleniowych
- Idealny gdy zasoby obliczeniowe są krytycznie ograniczone

**YOLOv8s (Small)**

- Dobry kompromis dla urządzeń mobilnych i embedded Linux
- Znacząca poprawa dokładności względem `n` przy umiarkowanym wzroście zużycia zasobów
- Nadaje się do prostych scenariuszy nadzoru wideo w czasie rzeczywistym na CPU

**YOLOv8m (Medium) ← używany w tym projekcie**

- Wybrany do projektu Verstappi.pl jako optymalny balans szybkość/dokładność na GPU
- Dobrze wykrywa pojazdy różnych rozmiarów; radzi sobie z nakładaniem się obiektów
- Wymagane GPU z minimum ~4 GB VRAM do płynnego śledzenia 25 FPS
- `conf=0.3` — próg pewności detekcji ustawiony empirycznie

**YOLOv8l (Large)**

- Wysoka dokładność przy trudnych scenariuszach (tłum pojazdów, mgła, noc)
- Znacznie wyższe wymagania obliczeniowe; potrzebne GPU klasy ~8 GB VRAM
- Zalecany gdy dokładność jest ważniejsza niż szybkość i dostępny jest mocny hardware

**YOLOv8x (XLarge)**

- Największy i najdokładniejszy wariant — zbliżony do state-of-the-art na benchmarkach COCO
- Przeznaczony do systemów off-line lub batch processing
- Czas inferencji ~3.5× dłuższy niż `m`; intensywne użycie VRAM (10+ GB)
- Nieopłacalny do streamingu real-time bez klasyteryzacji GPU

### Dlaczego YOLOv8m dla tego projektu?

Projekt przetwarza strumień HLS z kamery drogowej (docelowo ~25 FPS). Model musi:

1. Śledzić pojazdy między klatkami (persist tracking)
2. Klasyfikować 4 klasy obiektów (2, 3, 5, 7 z COCO)
3. Działać w sposób ciągły bez degradacji pamięci

Model `yolov8m.pt` spełnia te wymagania oferując mAP50-95 = **50.2** przy czasie inferencji poniżej 2 ms na GPU, co zostawia wystarczający budżet czasowy na preprocessing i postprocessing klatki.

---

## 5. Modele danych (MongoDB)

### `Traffic` — surowe dane (co 10 minut)

```python
class Traffic(Document):
    time          = DateTimeField(required=True)  # czas okna 10-minutowego
    carsIn        = IntField(required=True)
    carsOut       = IntField(required=True)
    motorcyclesIn = IntField(required=True)
    motorcyclesOut= IntField(required=True)
    busesIn       = IntField(required=True)
    busesOut      = IntField(required=True)
    trucksIn      = IntField(required=True)
    trucksOut     = IntField(required=True)
```

### `DailyTraffic` — agregat dobowy

```python
class TrafficData(EmbeddedDocument):
    carsIn, carsOut, motorcyclesIn, motorcyclesOut,
    busesIn, busesOut, trucksIn, trucksOut  # IntField

class DailyTraffic(Document):
    day     = DateTimeField(required=True)
    traffic = EmbeddedDocumentField(TrafficData, required=True)
```

Agregat dobowy tworzony jest automatycznie przez backend o północy (gdy `timeStamp.time() == 00:00:00`), sumując wszystkie rekordy `Traffic` z poprzedniego dnia.

### `Logs` — logi aplikacyjne

```python
class Logs(Document):
    service       = StringField(required=True)
    type          = StringField(choices=("INFO","WARNING","ERROR","CRITICAL"))
    time          = DateTimeField(required=True)
    message       = StringField(required=True)
    transactionId = StringField(required=True)
```

---

## 6. API — dokumentacja endpointów

Bazowy URL: `https://verstappi.pl:31514/api`

### `POST /traffic`

Zapis nowego 10-minutowego odczytu z detektora.

**Nagłówki:**

```
X-Detector-Token: <DETECTOR_TOKEN>
Content-Type: application/json
```

**Ciało żądania:**

```json
{
  "timeStamp": "2026-04-15T14:20:00",
  "carsIn": 12,
  "carsOut": 8,
  "motorcyclesIn": 2,
  "motorcyclesOut": 1,
  "busesIn": 1,
  "busesOut": 0,
  "trucksIn": 3,
  "trucksOut": 4
}
```

**Odpowiedzi:**

| Kod   | Opis                             |
| ----- | -------------------------------- |
| `201` | Dane zapisane pomyślnie          |
| `400` | Brakujące wymagane pola          |
| `401` | Nieprawidłowy token              |
| `500` | Błąd serwera / brak konfiguracji |

> Jeśli `timeStamp` wskazuje na północ (`00:00:00`), backend automatycznie tworzy agregat dobowy dla poprzedniego dnia.

---

### `GET /traffic/{year}`

Dane roczne zagregowane według miesięcy.

**Nagłówki:** `Authorization: Bearer <keycloak_token>`

**Przykładowa odpowiedź:**

```json
{
  "data": {
    "01": { "carsIn": 1500, "carsOut": 1420, ... },
    "04": { "carsIn": 2100, "carsOut": 2050, ... }
  }
}
```

---

### `GET /traffic/{year}/{month}`

Dane miesięczne zagregowane według dni.

**Przykładowa odpowiedź:**

```json
{
  "data": {
    "01": { "timeStamp": "2026-04-01T00:00:00", "carsIn": 80, ... },
    "15": { "timeStamp": "2026-04-15T00:00:00", "carsIn": 95, ... }
  }
}
```

---

### `GET /traffic/{year}/{month}/{day}`

Surowe dane dla konkretnego dnia z rozdzielczością 10 minut.

**Przykładowa odpowiedź:**

```json
{
  "data": {
    "2026-04-15T08:00:00": { "timeStamp": "2026-04-15T08:00:00", "carsIn": 12, ... },
    "2026-04-15T08:10:00": { "timeStamp": "2026-04-15T08:10:00", "carsIn": 9, ... }
  }
}
```

---

## 7. Wdrożenie na Kubernetes

### Struktura deploymentów

```
backend/deployments/       deployment.yml  configMap.yml  secret.yml  service.yml
frontend/deployments/      deployment.yml  service.yml
database/deployments/      statefulSet.yml configMap.yml  secret.yml  service.yml
keycloak/deployments/      deployment.yml  service.yml  persistentVolume.yml  persistentVolumeClaim.yml
certmanager/               clusterIssuer.yml  ingress.yml
```

### Kolejność wdrożenia od zera

```bash
# 1. Baza danych
kubectl apply -f database/deployments/

# 2. Keycloak
kubectl apply -f keycloak/deployments/

# 3. Backend
kubectl apply -f backend/deployments/

# 4. Frontend
kubectl apply -f frontend/deployments/

# 5. Cert-manager (ClusterIssuer musi istnieć przed Ingress)
kubectl apply -f certmanager/clusterIssuer.yml
kubectl apply -f certmanager/ingress.yml
```

### Pushing do dev

Przed uruchomieniem poniższych poleceń upewnij się, że w `(backend/frontend)/deployments/deployment.yml` używasz obrazu `dev` zamiast `prod`.

```bash
# Zbuduj i wypchnij obraz do Docker Hub
./run-makefile.sh frontend
./run-makefile.sh backend

# Jeśli zmieniono plik deployment.yml:
kubectl apply -f <komponent>/deployments/

# Jeśli zmieniono tylko kod (nie deployment):
kubectl rollout restart deployment backend-deployment
kubectl rollout restart deployment frontend-deployment
```

### Sekrety Kubernetes

**`mongo-auth`** (database/deployments/secret.yml):

```
MONGO_INITDB_ROOT_USERNAME
MONGO_INITDB_ROOT_PASSWORD
```

**`backend-auth`** (backend/deployments/secret.yml):

```
DETECTOR_TOKEN
```

**`backend-app-config`** (configMap):

```
DB_HOST
```

---

## 8. Przewodnik dewelopera

### Lokalne uruchomienie backendu

```bash
cd backend/app
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=password
export DETECTOR_TOKEN=tajnehaslodetectora

flask --app app run --port 5000
```

### Lokalne uruchomienie detektora

```bash
cd backend/detector/app
pip install -r requirements.txt

# Z czytnikiem VLC (domyślny):
python main.py --reader vlc

# Z czytnikiem FFmpeg:
python main.py --reader ffmpeg

# Własny URL strumienia:
python main.py --reader ffmpeg --url <hls_url>
```

> Model `yolov8m.pt` musi znajdować się w katalogu roboczym lub zostanie automatycznie pobrany przez `ultralytics`.

### Lokalne uruchomienie frontendu

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### Budowanie obrazów Docker

```bash
# Backend
docker build -t underwoodsteam/dev-backend:latest backend/

# Frontend
docker build -t underwoodsteam/dev-frontend:latest frontend/

# Detektor
docker build -t underwoodsteam/dev-detector:latest backend/detector/
```

---

## 9. Zmienne środowiskowe

| Zmienna          | Serwis            | Opis                                            |
| ---------------- | ----------------- | ----------------------------------------------- |
| `DB_HOST`        | backend, detector | Hostname MongoDB (= nazwa serwisu k8s)          |
| `DB_USER`        | backend, detector | Użytkownik MongoDB                              |
| `DB_PASSWORD`    | backend, detector | Hasło MongoDB                                   |
| `DETECTOR_TOKEN` | backend           | Shared secret dla weryfikacji żądań z detektora |

---

## 10. Stos technologiczny

| Warstwa           | Technologia                  | Wersja              |
| ----------------- | ---------------------------- | ------------------- |
| Detekcja obiektów | Ultralytics YOLOv8           | 8.3.228             |
| Odczyt strumienia | python-vlc / FFmpeg          | 3.0.21203 / system  |
| Backend API       | Flask + MongoEngine          | —                   |
| Baza danych       | MongoDB                      | 7.0                 |
| Frontend          | Next.js + React + TypeScript | 16.1.1 / 19.2.3 / 5 |
| Wykresy           | Recharts                     | 3.6.0               |
| HLS Player        | hls.js                       | 1.6.15              |
| Autoryzacja       | Keycloak                     | 26.4.6              |
| Konteneryzacja    | Docker                       | —                   |
| Orkiestracja      | Kubernetes                   | —                   |
| Ingress           | NGINX Ingress Controller     | —                   |
| TLS               | cert-manager + Let's Encrypt | —                   |
| Hosting           | OVH VPS                      | —                   |
