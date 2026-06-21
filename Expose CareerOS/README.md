# Expose Autospy Career OS

A lightweight, production-quality career management and preparation workstation designed specifically for software engineers. It tracks profile highlights, job application pipelines, learning paths, and interview preparation question-banks.

## Tech Stack
- **Backend:** Python 3.12, FastAPI, SQLite, SQLAlchemy, Pydantic
- **Frontend:** Jinja2 templates, HTMX, TailwindCSS (CDN-based customized styling), Lucide Icons

---

## Installation & Setup

### Prerequisites
- Python 3.12+ installed on your system.

### Steps
1. Navigate to the project directory:
   ```bash
   cd expose-autospy
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - **Windows PowerShell:**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows CMD / Git Bash:**
     ```bash
     source venv/Scripts/activate
     ```

4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Application

Start the local development server:
```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once running, navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000) in your web browser.

---

## Project Structure
```
expose-autospy/
├── app/
│   ├── main.py            # Entrypoint & startup configuration
│   ├── routes/            # Route modules (dashboard, profile, jobs, learning, interviews)
│   ├── services/          # Business logic & Database CRUD operations
│   ├── models/            # SQLAlchemy database and Pydantic schemas
│   ├── templates/         # HTML structure & Jinja template engine files
│   ├── static/            # Static assets (custom css & javascripts)
│   ├── database/          # SQLite database connection setup and seeding script
│   └── utils/             # Helper utilities
├── requirements.txt       # Dependencies
└── README.md              # Documentations
```
