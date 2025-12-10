## Admin Login
- **Username:** `admin@gptplpt`
- **Passkey:** `gpt155`

## Setup
```bash
python -m venv .venv
# Windows:
#   .venv\Scripts\activate
# macOS/Linux:
#   source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

### Data & Files
- Database: `data/sms.db` (auto-created)
- Student photos upload: `static/uploads/`
- Generated TC PDFs: `static/tc/`

### Features
- Students: Add/Edit, status (Active/Passout), photo upload, TC generation (asks completion date)
- Inventory: Seeded items, add/edit
- Exams & Results: Create exams, enter internal/external, total auto-calculated

