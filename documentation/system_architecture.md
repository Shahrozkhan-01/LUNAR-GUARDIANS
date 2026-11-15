# System Architecture

## Overview

The frontend is a React/Vite single-page application. `MissionProvider` owns
the current mission ID, setup preferences, authoritative backend state,
loading/error state, actions, and replay operations. FastAPI is the authority
for simulation state and exposes separate game, DONKI, and static-dataset
routers.

## High-level architecture

```mermaid
flowchart LR
  User --> React[React/Vite frontend]
  React --> Context[MissionContext]
  Context --> GameAPI[Axios gameApi]
  GameAPI --> GameRoutes[FastAPI game routes]
  GameRoutes --> Simulation[simulation.py]
  Simulation --> Store[In-memory mission store]
  React --> NasaAPI[Axios NASA/dataset calls]
  NasaAPI --> NasaRoutes[FastAPI NASA routes]
  NasaRoutes --> Donki[nasa_service + processor + classifier]
  NasaAPI --> DatasetRoutes[FastAPI dataset routes]
  DatasetRoutes --> DatasetService[dataset_service]
  DatasetService --> Files[(processed datasets + metadata)]
```

## Component diagram

```mermaid
flowchart TB
  subgraph Frontend
    App --> Home
    App --> Setup[MissionSetup]
    App --> Control[MissionControl]
    App --> Explorer[NasaDataExplorer]
    Control --> Weather[NasaSpaceWeather]
    Control --> Training[NasaTrainingEvents]
    Control --> Debrief[Mission debrief]
    Setup --> Briefing[NasaMissionBriefing]
    Context[MissionContext] --> Setup
    Context --> Control
  end
  subgraph Backend
    Main[app.main] --> Game[game router]
    Main --> NASA[nasa router]
    Main --> Datasets[datasets router]
    Game --> Sim[simulation engine]
    Sim --> Events[event_manager]
    Sim --> Resources[resource rules]
    NASA --> DonkiService[nasa_service]
    DonkiService --> Processor[nasa_data_processor]
    Processor --> Classifier[nasa_event_classifier]
    Datasets --> Dataset[dataset_service]
  end
  Context --> Main
  Explorer --> Datasets
  Weather --> NASA
  Training --> Game
```

## Mission initialization sequence

```mermaid
sequenceDiagram
  participant U as User
  participant S as MissionSetup
  participant C as MissionContext
  participant A as FastAPI
  participant E as Simulation
  participant M as Mission store
  U->>S: Select configuration
  S->>C: startNewMission(config)
  C->>A: POST /api/game/start
  A->>E: create_mission(request)
  E->>M: Save GameState
  E-->>A: GameState
  A-->>C: GameState
  C-->>S: Navigate to MissionControl
```

## Daily progression sequence

```mermaid
sequenceDiagram
  participant U as User
  participant C as MissionControl
  participant M as MissionContext
  participant A as FastAPI
  participant E as Simulation
  U->>C: Click NEXT DAY
  C->>M: advanceDay()
  M->>A: POST /api/game/{id}/advance
  A->>E: advance_mission_day(id)
  E->>E: Apply resources, systems, crew, events
  E->>E: Read cached DONKI context only
  E-->>A: AdvanceDayResponse
  A-->>M: Updated GameState
  M-->>C: Feedback and new dashboard
```

## NASA data integration flow

```mermaid
flowchart LR
  Env[NASA_API_KEY + cache settings] --> Service[nasa_service]
  Service --> NASA[api.nasa.gov/DONKI]
  Service --> Fallback[CCMC DONKI fallback]
  Service --> Cache[In-memory cached snapshot]
  Cache --> Processor[nasa_data_processor]
  Processor --> Classifier[nasa_event_classifier]
  Classifier --> Routes[/api/nasa/*]
  Routes --> Panel[NASA Space Weather]
  Cache --> Simulation
  Catalog[dataset_catalog.csv] --> DatasetService[dataset_service]
  Processed[datasets/processed] --> DatasetService
  DatasetService --> DatasetRoutes[/api/datasets/*]
  DatasetRoutes --> Explorer[NASA Data Explorer]
  DatasetRoutes --> Briefing[Mission Briefing]
```

## Mission completion flow

```mermaid
flowchart TD
  Advance[Advance final mission day] --> State[Updated GameState]
  State --> Status{Mission status}
  Status -->|Successful/failed/partial| Report[Mission debrief]
  Report --> Score[Existing Science Points game score]
  Report --> History[Persistent decision and event history]
  Report --> Replay[Relaunch Day 1 or configure new mission]
  Replay --> Fresh[New GameState with reset resources/history]
```

## State and scientific boundaries

Resources, events, decisions, `mission_decisions`, `mission_events`, and
training events are stored in the Pydantic `GameState` and returned by the
backend. NASA values are contextual inputs only. They are never converted into
astronaut dose, habitat temperature, landing safety, network delay, or resource
amounts.
