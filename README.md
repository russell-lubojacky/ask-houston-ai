# 🏙️ Ask Houston AI Data Explorer
Welcome to **Ask Houston AI** - a data exploration and visualization tool that lets users ask natural language questions about Houston. Starting with 311 incident data, this project will expand to include 911 calls, real estate listings, deomgraphics and more. Whether you're a resident, researcher, or curious explorer, this platform aims to provide clear, interactive insights using maps, graphs, and AI-powered prompts.

🌐 Planned live deployment: [askhouston.ai](https://askhouston.ai) (coming soon)

## 📚 Table of Contents
- [🔍 Project Vision](#-project-vision)
- [🧱 Tech Stack](#-tech-stack)
- [🚀 Quick Start (Local Dev)](#-quick-start-local-dev)
- [📦 Data Sources](#-data-sources)
- [🤖 AI Integration](#-ai-integration)
- [🗺️ Features](#️-features)
- [🛣️ Roadmap](#️-roadmap)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [📫 Contact](#-contact)

---

## 🔍 Project Vision
>
> "What are the most common 311 complaints in my neighborhood over the past 10 years?"
>
> "Show me which areas have the most 911 calls in the last month."
>
> "How do property values correlate with noise complaints?"

This project brings public data to life by allowing people to:
- Ask **natural language questions**
- View answers in **dynamic maps**, **charts**, and **reports**
- Gain insights from Houston's historical and real-time datasets

## 🧱 Tech Stack
| Layer               | Tech                                 |
|---------------------|--------------------------------------|
| 🌐 Frontend         | [SvelteKit](https://kit.svelte.dev/) |
| 🧠 AI/NLP Engine    | OpenAI / Prompt Engineering          |
| 🗺️ Mapping          | Leaflet / MapLibre / Mapbox GL JS    |
| 📊 Visualization    | D3.js / Plotly / ApexCharts          |
| 🐘 Database         | PostgreSQL + PostGIS                 |
| ⚙️ Backend API      | Node.js / Python (TBD)               |
| 🐳 DevOps           | Docker, Docker Compose               |
| ☁️ Hosting          | Linode (Cloud Compute)               |

## 🚀 Quick Start (Local Dev)

### Prerequisites
- [Docker](https://www.docker.com/)
- [Git](https://git-scm.com/)

### Steps
```bash
# 1. Clone the repo
git clone https://github.com/russell-lubojacky/ask-houston-ai.git
cd ask-houston-ai

# 2. Setup environment config
cp .env.sample .env # edit as needed

# 3. Run with Docker
docker-compose up
```

App will be available at http://localhost:5173

## 📦 Data Sources
| Source        | Description                        | Format         |
|---------------|------------------------------------|----------------|
| Houston 311   | Service requests (last 10+ years)  | Pipe-delimited |
| Houston 911   | Emergency call logs                | (Planned)      |
| Real Estate   | Property listings + valuations     | (Planned)      |
| Census        | Demographics by neighborhood       | (Planned)      |

## 🤖 AI Integration
The application will use:
- AI Prompt Engineering to interpret natural language
- LLMs (OpenAI, open-source) to translate questions into SQL or map queries
- Caching & Indexing for fast results and optimized query patterns

## 🗺️ Features
- 🧭 Ask questions and get maps, charts, and insights
- 📍 Explore incidents by neighborhood, type of time range
- 📈 Visual analytics powered by your queries
- 🧠 AI assistance for query generation and exploration
- 🔒 All containerized with secure deployment to Linode

## 🛣️ Roadmap
- Initial data load from Houston 311
- PostgreSQL + PostGIS schema design
- AI prompt-to-query engine
- Dynamic map + chart integration
- Public deployment to [askhouston.ai](https://askhouston.ai)
- Expand to 911 data and real estate analytics
- Add saved reports and shareable dashboards

## 🤝 Contributing
We welcome contributors! If you're passionate about civic tech, mapping, data viz, or AI - get in touch or fork the repo!

## 📄 License
MIT License

## 📫 Contact
Built with ❤️ by [Russell Lubojacky](https://github.com/russell-lubojacky)
