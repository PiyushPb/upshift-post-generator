# Upshift - India Job Scraper & Telegram Pipeline 🚀

A modular, lightweight, and clean pipeline to scrape, clean, select, format, and publish tech jobs in **India** from top platforms (**Indeed, LinkedIn, Google Jobs, Glassdoor, Naukri**).

---

## 📁 Pipeline Architecture

```
upshift/
├── data/                       # Scraped and cleaned datasets (CSV & JSON)
│   ├── jobs_india.csv
│   └── jobs_india.json
├── src/
│   ├── config/settings.py      # India search parameters, sites & limits
│   ├── scrapers/job_scraper.py # Multi-platform scraper using JobSpy (descriptions dropped)
│   ├── cleaners/job_cleaner.py # Deduplication, Indian salary formatting (₹ LPA), URL cleanup
│   ├── formatters/             # Telegram HTML post formatter with tags & direct links
│   ├── publishers/             # Telegram Bot API dispatcher with dry-run support
│   ├── pipeline/               # Orchestrates Scrape -> Clean -> Format -> Publish
│   └── utils/logger.py         # Formatted terminal logging
├── main.py                     # CLI entrypoint
└── .env                        # Telegram credentials (optional)
```

---

## ⚡ Quick Start

### 1. Curate Pure Category Carousels (100% Matching Theme)
```bash
# Pure Software Engineering batch (Blue Theme)
python main.py --category engineering --location "Bengaluru" --results 15 --top 10

# Pure Data & Analytics / AI batch (Pink Theme)
python main.py --category data --location "Bengaluru" --results 15 --top 10

# Pure DevOps & Cloud batch (Green Theme)
python main.py --category devops --location "Bengaluru" --results 15 --top 10

# Pure Product & Design batch (Yellow Theme)
python main.py --category product --location "Bengaluru" --results 15 --top 10
```

### 2. Fast-Track Mode (Render directly from saved dataset)
```bash
python main.py --from-file data/jobs_india.json --category engineering --top 10
python main.py --from-file data/jobs_india.json --category data --top 10
```

### 3. Telegram Publishing / Dry Run
To send posts to your Telegram channel:
1. Copy `.env.example` to `.env` and fill in your `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.
2. Run:
```bash
python main.py --publish
```
*(By default, if no credentials are set, it runs in safe **DRY RUN** mode and prints message previews to console).*

---

## 📊 Dataset Output Columns
The scraped dataset is lightweight (long descriptions stripped) and includes rich metadata:
- `site`: indeed / linkedin / google / glassdoor / naukri
- `title`: Job Title
- `company`: Employer name & company URL
- `location`: Indian city / state / Remote
- `salary_display`: Formatted salary (e.g., `12.5 LPA - 18 LPA` or `₹ Not Disclosed`)
- `job_url`: Direct application link
- `skills`, `job_type`, `experience_range`, `company_rating` (when available)
