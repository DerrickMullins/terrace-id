# TerraceID: Football Chant Scraper & Database

**TerraceID** is a Python-based data collection tool designed to aggregate and organize football fan chants. It crawls fan-media sites to extract direct audio links and maps them to specific clubs, storing the structured data in a Supabase (PostgreSQL) backend.

## 🚀 Features

* **Automated Multi-Level Scraping**: Navigates from league directories to individual team pages to ensure a comprehensive chant library.
* **Direct Media Extraction**: Identifies and captures raw `.mp3` and `.mp4` source links from embedded play elements.
* **Cloud Persistence**: Automatically syncs chant metadata and team affiliations to **Supabase** using an efficient `upsert` logic to prevent duplicates.
* **Secure Configuration**: Fully integrated with `python-dotenv` to keep database credentials and project settings out of source control.

## 🛠️ Tech Stack

* **Language**: Python 3.10+
* **Scraping**: BeautifulSoup4, Requests
* **Database**: Supabase (PostgreSQL)
* **Environment**: Dotenv, Virtual Environments (venv)

## 📋 Database Schema

The project is optimized for a Supabase table named `chants` with the following structure:

| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | uuid | Primary Key (Auto-generated) |
| `team` | text | The football club name |
| `chant_name` | text | The name of the specific chant |
| `audio_url` | text | Direct link to the source file (Unique) |
| `created_at` | timestamptz | Entry timestamp |

## ⚙️ Setup & Installation

### 1. Clone & Navigate
```bash
git clone [https://github.com/your-username/terrace-id.git](https://github.com/your-username/terrace-id.git)
cd terrace-id
