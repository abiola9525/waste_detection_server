# Setup

## Prerequisites

- Python 3.8 or higher
- pip

## Steps

1. Create a virtual environment
```bash
python -m venv .venv
```

2. Activate the virtual environment
```bash
.venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment variables
```bash
cp .env.example .env
```
Update `.env` with your values if it differs from the default.

5. Make migrations
```bash
python manage.py makemigrations
```

6. Migrate
```bash
python manage.py migrate
```

7. Run the server
```bash
python manage.py runserver
```

8. Seed the database
```bash
python manage.py seed_demo_data
```

9. Access the dashboard
```bash
http://localhost:8000/admin/
```

10. Access the API
```bash
http://localhost:8000/api/
```

11. Access the demo data
```bash
http://localhost:8000/api/bins/status/
```

12. Access the demo data
```bash
http://localhost:8000/api/bins/status/
```