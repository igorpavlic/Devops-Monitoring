# Parking App Monitoring Stack

## Prometheus + Grafana - ZASEBNI DOCKER STACK

Monitoring stack koji je **potpuno odvojen** od aplikacije. Dva nezavisna docker-compose-a koji dijele istu network.

---

## 🏗️ Arhitektura

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SHARED: parking-network                          │
│                                                                     │
│  ┌─────────────────────┐         ┌────────────────────────────────┐│
│  │   APP STACK         │         │      MONITORING STACK          ││
│  │   (docker-compose)  │         │      (docker-compose)          ││
│  │                     │         │                                ││
│  │  ┌──────────────┐   │  HTTP   │  ┌──────────────────┐          ││
│  │  │ parking-app  │◄──┼─────────┼──│ metrics-exporter │          ││
│  │  │    :5000     │   │         │  │      :9090       │          ││
│  │  └──────────────┘   │         │  └────────┬─────────┘          ││
│  │                     │         │           │                    ││
│  └─────────────────────┘         │           ▼                    ││
│                                  │  ┌──────────────────┐          ││
│                                  │  │   Prometheus     │          ││
│                                  │  │      :9091       │          ││
│                                  │  └────────┬─────────┘          ││
│                                  │           │                    ││
│                                  │           ▼                    ││
│                                  │  ┌──────────────────┐          ││
│                                  │  │    Grafana       │          ││
│                                  │  │      :3000       │          ││
│                                  │  └──────────────────┘          ││
│                                  └────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Struktura direktorija

```
project/
├── app/                          # APP STACK
│   ├── docker-compose.yml        # ← Pokreće SAMO app
│   ├── Dockerfile
│   ├── app.py                    # NEPROMIJENJEN!
│   ├── requirements.txt
│   ├── gunicorn_conf.py
│   └── templates/
│
└── monitoring/                   # MONITORING STACK
    ├── docker-compose.yml        # ← Pokreće SAMO monitoring
    ├── Dockerfile.metrics
    ├── metrics_exporter.py
    ├── prometheus/
    │   └── prometheus.yml
    └── grafana/
        └── provisioning/
            ├── datasources/
            │   └── datasource.yml
            └── dashboards/
                ├── dashboard.yml
                └── parking-dashboard.json
```

---

## 🚀 Pokretanje

### Korak 1: Pokreni aplikaciju PRVO

```bash
cd app
docker-compose up -d --build
```

Ovo kreira `parking-network` network.

### Korak 2: Pokreni monitoring

```bash
cd ../monitoring
docker-compose up -d --build
```

Monitoring se spaja na postojeći `parking-network`.

### Redoslijed je BITAN!

App mora biti pokrenut prije monitoringa jer on kreira network.

---

## 🔄 Neovisno upravljanje

```bash
# Samo app restart
cd app && docker-compose restart

# Samo monitoring restart  
cd monitoring && docker-compose restart

# Ugasi monitoring, app radi dalje
cd monitoring && docker-compose down

# Ugasi sve
cd app && docker-compose down
cd monitoring && docker-compose down
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

---

## 🔧 Troubleshooting

### Network ne postoji?
```bash
# Provjeri da je app pokrenut
docker network ls | grep parking

# Ako ne postoji, pokreni app prvi
cd app && docker-compose up -d
```

### Metrics exporter ne vidi app?
```bash
# Provjeri povezanost
docker exec metrics-exporter ping parking-app
```

### Provjera logova
```bash
# App logs
cd app && docker-compose logs -f

# Monitoring logs
cd monitoring && docker-compose logs -f
```

---

## 🎯 Prednosti zasebnih stackova

✅ **Nezavisni deploy** - Update monitoring bez restarta app-a  
✅ **Izolirani problemi** - Monitoring crash ne utječe na app  
✅ **Fleksibilno skaliranje** - Različiti resursi za svaki stack  
✅ **Čist code** - app.py ostaje nepromijenjen  
✅ **Production-ready** - Ovako se radi u produkciji
