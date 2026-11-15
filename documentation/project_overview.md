# LUNAR GUARDIANS — Project Overview & Objectives

> **NASA Space Apps Challenge | Educational Space Simulation**

---

## 1. Concept Summary

LUNAR GUARDIANS is a browser-based educational simulation in which children aged 7–12 take on the role of junior astronauts managing a lunar outpost. The player must keep their crew alive by making decisions about critical life-support resources.

The core philosophy is **learning through consequence** — decisions have visible effects on the base's survival meters, teaching cause-and-effect reasoning, resource thinking, and scientific literacy in a fun, low-pressure environment.

---

## 2. Educational Objectives

By playing LUNAR GUARDIANS, children will:

- **Understand why astronauts need oxygen, water, and food** in space.
- **Learn how solar power works** and why energy conservation matters on the Moon.
- **Discover what space weather is** (solar flares, coronal mass ejections) and how NASA monitors it.
- **Practice decision-making under limited resources** — a core STEM skill.
- **Be introduced to real NASA tools and datasets** in an age-appropriate way.
- **Build curiosity about space exploration** and STEM careers.

---

## 3. Target Audience

| Audience | Description |
|----------|-------------|
| Primary Players | Children aged 7–12 |
| Guided Use | Teachers using it in a classroom STEM setting |
| Home Use | Parents and children exploring space science together |

The interface will use simple language, visual indicators (icons, colors, gauges), and animations to minimize reading barriers for younger players.

---

## 4. Game Concept (High-Level)

The player manages a lunar outpost with the following survival systems:

### 🌬️ Oxygen & Life Support
Breathable air is consumed every in-game day. Equipment can break or be damaged during solar storms. Players must decide how to allocate power to life support.

### 💧 Water Management
Water is used for drinking, growing food, and cooling equipment. It can be harvested from lunar ice deposits (a real NASA concept). Players must balance usage and recycling.

### ⚡ Power Allocation
Solar panels generate limited electricity. Players distribute power between life support, communications, food production, and radiation shielding. Night periods on the Moon reduce solar generation.

### ☢️ Radiation Protection
Radiation indicators and shelter effects are fictional game units. Recent NASA DONKI records are displayed as real observations; a dated SEP report can introduce an educational shelter choice, but it does not calculate lunar astronaut dose or exposure.

### 🌱 Food Production
A greenhouse module grows food using water, light, and power. Players manage crop cycles and decide when to harvest versus conserve resources.

### 🌩️ Space Weather Events
The backend retrieves recent solar energetic particle (SEP) and solar flare records from the **NASA DONKI API** (Space Weather Database Of Notifications, Knowledge, Information). A timed SEP observation may create a clearly labeled educational shelter decision. The real NASA observation is kept separate from fictional game-unit consequences; DONKI event records are not lunar radiation-dose measurements.

### 🏅 Mission Survival
The game is played over a series of mission days. The crew survives if all systems stay above critical levels. Players receive a mission score and a mission debrief explaining the science behind events.

---

## 5. NASA Data Integration

| NASA Dataset / API | How It Will Be Used |
|--------------------|---------------------|
| [DONKI SEP and FLR APIs](https://api.nasa.gov/) | Recent solar energetic particle and solar flare observations are displayed; timed SEP records can support a separate simulated shelter scenario |
| [NASA Open Data Portal](https://data.nasa.gov/) | Reference data for lunar environment parameters |
| [NASA APOD API](https://api.nasa.gov/) | Background imagery and educational picture of the day |
| Artemis Mission Data | Contextual references for lunar base design |

> **Note:** No NASA data will be fabricated. All data shown will come from real NASA APIs or be clearly labeled as game simulation values.

See [NASA data sources](./nasa_data_sources.md) for the endpoints, classifications, failure handling, cache policy, and data/gameplay distinction.

---

## 6. Technology Decisions & Rationale

### Why React + Vite?
- Fast development server and hot module replacement speed up iteration.
- React's component model maps well to independent game system UI panels (oxygen gauge, water tank, power meter).
- Vite produces optimized builds for browser deployment.

### Why FastAPI (Python)?
- Python has strong libraries for data processing (pandas, numpy).
- FastAPI is easy to extend and produces automatic OpenAPI documentation.
- Python is the dominant language in the NASA/data science ecosystem, making future NASA dataset integration natural.

### Why No Database Yet?
In the initial phase, game state is managed in-memory or in browser localStorage. A database will be introduced only when persistent user accounts or save-game features are planned.

---

## 7. Project Phases (Rough Roadmap)

| Phase | Milestone |
|-------|-----------|
| ✅ Phase 0 | Development environment setup (current) |
| Phase 1 | Backend NASA API integration (DONKI, APOD) |
| Phase 2 | Core game loop — resource simulation engine |
| Phase 3 | Frontend game UI — base dashboard |
| Phase 4 | Space weather events integration |
| Phase 5 | Polishing, accessibility, and kid-friendly UX |
| Phase 6 | Testing with target age group |
| Phase 7 | Submission preparation |

---

## 8. Design Principles

- **Accuracy over fiction:** Space science facts must be correct. Game mechanics can simplify but not contradict real science.
- **Age-appropriate language:** No jargon without explanation. Use visual metaphors.
- **No dark themes:** Failure messages should be encouraging, not scary.
- **Accessibility:** High color contrast, large interactive targets, keyboard navigable.
- **Performance:** Must run on a standard school Chromebook or tablet browser.

---

## 9. What This Project Is NOT

- Not a full physics simulation.
- Not a multiplayer game (at this stage).
- Not a database-driven application (at this stage).
- Not a mobile-first app (desktop browser first; mobile adaptation later).

---

*Last updated: Initial setup phase — November 2026*
*NASA Space Apps Challenge*
