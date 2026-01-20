# Parking App Monitoring Stack

## Prometheus + Grafana - ZASEBNI DOCKER STACK

Monitoring stack koji je **potpuno odvojen** od aplikacije. Dva nezavisna docker-compose-a koji dijele istu network.

---

## 🏗️ Arhitektura

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SHARED: parking-network                          │
│                                                                     │
│  ┌─────────────────────┐         ┌────────────────────────────────┐ │
│  │   APP STACK         │         │      MONITORING STACK          │ │
│  │   (docker-compose)  │         │      (docker-compose)          │ │
│  │                     │         │                                │ │
│  │  ┌──────────────┐   │  HTTP   │  ┌──────────────────┐          │ │
│  │  │ parking-app  │◄──┼─────────┼──│ metrics-exporter │          │ │
│  │  │    :5000     │   │         │  │      :9090       │          │ │
│  │  └──────────────┘   │         │  └────────┬─────────┘          │ │
│  │                     │         │           │                    │ │
│  └─────────────────────┘         │           ▼                    │ │
│                                  │  ┌──────────────────┐          │ │
│                                  │  │   Prometheus     │          │ │
│                                  │  │      :9091       │          │ │
│                                  │  └────────┬─────────┘          │ │
│                                  │           │                    │ │
│                                  │           ▼                    │ │
│                                  │  ┌──────────────────┐          │ │
│                                  │  │    Grafana       │          │ │
│                                  │  │      :3000       │          │ │
│                                  │  └──────────────────┘          │ │
│                                  └────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Pokretanje

### Korak 1: Pokreni aplikaciju PRVO

Obavezno najprije pokrenuti App.

### Korak 2: Pokreni monitoring

```bash
cd ../monitoring
./start-monitoring.sh
```

### Korak 3: Otvaranje tunela sa lokalnog računala

```bash
ssh -N -L 5000:localhost:5000 -L 9090:localhost:9090 -L 9091:localhost:9091 -L 3000:localhost:3000 USERNAME@FIPU-SERVER -p 2127
```
---

## 🌐 Pristup servisima

| Servis | URL | Stack |
|--------|-----|-------|
| Parking App | http://localhost:5000 | app |
| Metrics | http://localhost:9090/metrics | monitoring |
| Prometheus | http://localhost:9091 | monitoring |
| Grafana | http://localhost:3000 | monitoring |

**Grafana login:** admin / admin123

---

## 📊 Metrike

| Metrika | Opis |
|---------|------|
| `parking_app_up` | Aplikacija dostupna (1/0) |
| `parking_app_response_time_seconds` | Response time histogram |
| `parking_app_health_checks_total` | Health check counter |
| `parking_spots_occupied` | Zauzeta mjesta |
| `parking_spots_free` | Slobodna mjesta |
| `parking_occupancy_ratio` | Zauzetost (0-1) |
