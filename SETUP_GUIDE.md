# ReATOA Setup Guide

Complete step-by-step guide to get the voice-driven school ERP system up and running.

## Prerequisites Check

Before starting, ensure you have:

- [ ] Python 3.10 or higher installed
- [ ] Node.js 18 or higher installed
- [ ] PostgreSQL 15+ or Docker installed
- [ ] Git installed (optional)
- [ ] At least 2GB free disk space (for dependencies and Whisper model)

Verify installations:

```bash
python --version    # Should show 3.10+
node --version      # Should show 18+
npm --version       # Should show 9+
docker --version    # If using Docker for PostgreSQL
```

## Part 1: Backend Setup (Django)

### Step 1: Navigate to Backend Directory

```bash
cd backend
```

### Step 2: Create Python Virtual Environment

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal.

### Step 3: Install Python Dependencies

```bash
pip install -r requirements/development.txt
```

This will take 2-5 minutes. It installs:
- Django and DRF
- PostgreSQL driver
- Whisper and PyTorch
- JWT authentication
- Other utilities

### Step 4: Setup PostgreSQL Database

**Option A: Using Docker (Recommended)**

From the project root directory:

```bash
docker-compose up -d
```

Verify it's running:
```bash
docker ps
```

You should see `reatoa_postgres` container running.

**Option B: Manual PostgreSQL Setup**

1. Install PostgreSQL from https://www.postgresql.org/download/
2. Create database:

```bash
# Open PostgreSQL prompt
psql -U postgres

# Create database
CREATE DATABASE reatoa_db;

# Exit
\q
```

### Step 5: Configure Environment Variables

Create `.env` file in `backend` directory:

```bash
cp .env.example .env
```

Edit `.env` file (use any text editor):

```env
SECRET_KEY=django-insecure-change-this-in-production-abc123xyz
DEBUG=True

DB_NAME=reatoa_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

WHISPER_MODEL_SIZE=base
WHISPER_DEVICE=cpu

DEFAULT_EXAM_TYPE=UNIT_TEST
```

**Important:** If you set a different PostgreSQL password, update `DB_PASSWORD`.

### Step 6: Run Database Migrations

```bash
python manage.py migrate
```

You should see output showing migrations being applied.

### Step 7: Seed Database with Test Data

```bash
cd ..
python scripts/seed_database.py
```

This creates:
- 10 classes (1st to 10th grade)
- 3 sections per class (A, B, C)
- 600 students (20 per section)
- 5 subjects
- 3 exam types
- 5 teacher accounts
- 1 admin account

**Login Credentials Created:**
- Admin: `admin` / `admin123`
- Teachers: `teacher1` to `teacher5` / `password123`

### Step 8: Create Superuser (Optional)

If you want a custom admin account:

```bash
cd backend
python manage.py createsuperuser
```

Follow the prompts to create your admin account.

### Step 9: Start Django Development Server

```bash
python manage.py runserver
```

**Expected Output:**
```
Django version 5.0.1, using settings 'config.settings.development'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

**Test the backend:**
Open browser and visit: `http://localhost:8000/admin/`

You should see the Django admin login page.

**Leave this terminal running** and open a new terminal for frontend setup.

---

## Part 2: Frontend Setup (React + Vite)

### Step 10: Navigate to Frontend Directory

Open a **new terminal** and run:

```bash
cd frontend
```

### Step 11: Install Node.js Dependencies

```bash
npm install
```

This will take 1-2 minutes. It installs:
- React and React DOM
- Redux Toolkit
- React Router
- Axios
- Tailwind CSS
- Heroicons
- Vite

### Step 12: Verify Environment File

Check that `.env` file exists in `frontend` directory with:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

If it doesn't exist, create it with this content.

### Step 13: Start Frontend Development Server

```bash
npm run dev
```

**Expected Output:**
```
  VITE v5.0.11  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h to show help
```

**Test the frontend:**
Open browser and visit: `http://localhost:5173/`

You should see the ReATOA login page.

---

## Part 3: Test the System

### Step 14: Login to the System

1. Open browser: `http://localhost:5173/`
2. Use demo credentials:
   - Username: `teacher1`
   - Password: `password123`
3. Click "Sign In"

You should be redirected to the dashboard.

### Step 15: Test Voice Command

1. On the dashboard, click the **blue microphone button**
2. Allow microphone access when browser prompts
3. Speak clearly:
   > "Enter marks for roll number 1, class 9B. Maths 85, Hindi 78, English 92"
4. Click the **red stop button** when done
5. Wait for processing (5-10 seconds)

**First-Time Note:** On the first voice command, Whisper will download its model (~150MB). This takes 2-5 minutes depending on internet speed. Subsequent commands will be faster.

6. Review the confirmation dialog showing:
   - Student name (should be a student from class 9B, roll 1)
   - Marks table
   - Subject scores

7. Click **"Confirm"** to save the marks

8. You should see a success notification

### Step 16: Verify Data Saved

Visit Django admin panel: `http://localhost:8000/admin/`

Login with:
- Username: `admin`
- Password: `admin123`

Navigate to:
- **Marks** → **Marks** to see the entered marks
- **Student Grades** to see calculated grades

---

## Troubleshooting

### Backend Issues

**Issue: "No module named 'django'"**
```bash
# Ensure virtual environment is activated
# You should see (venv) in terminal
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements/development.txt
```

**Issue: "django.db.utils.OperationalError: could not connect to server"**
```bash
# Check PostgreSQL is running
docker ps  # Should show reatoa_postgres

# If not running:
docker-compose up -d

# Or if using manual PostgreSQL:
# Windows: Check Services for PostgreSQL
# macOS: brew services start postgresql
# Linux: sudo systemctl start postgresql
```

**Issue: "Whisper model download stuck"**
- Check internet connection
- Check firewall settings
- Wait patiently (can take 5 minutes)
- Check disk space (need ~200MB free)

**Issue: Port 8000 already in use**
```bash
# Find and kill process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -i :8000
kill -9 <PID>
```

### Frontend Issues

**Issue: "Cannot find module" or dependency errors**
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Issue: Port 5173 already in use**
```bash
# Kill process on port 5173
# Windows:
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# macOS/Linux:
lsof -i :5173
kill -9 <PID>
```

**Issue: "Failed to fetch" errors in browser**
- Check Django backend is running (`http://localhost:8000`)
- Check CORS settings in Django `settings.py`
- Check `.env` file has correct API URL

### Audio/Microphone Issues

**Issue: Microphone not working**
- Check browser permissions (usually icon in address bar)
- Try different browser (Chrome/Edge recommended)
- Check system microphone settings
- Test microphone in other apps

**Issue: "MediaRecorder is not supported"**
- Update browser to latest version
- Use Chrome, Edge, or Firefox
- Safari may have limited support

**Issue: Audio processing takes too long**
- First time is slow (model download)
- Subsequent times should be 5-10 seconds
- Speak shorter commands
- Check CPU usage (Whisper is CPU-intensive)
- Consider GPU acceleration: Set `WHISPER_DEVICE=cuda` in `.env` if you have NVIDIA GPU

### Common Voice Command Issues

**Issue: "Unknown intent" error**
Try these phrases:
- "Enter marks for roll number one, class nine B. Maths eighty five"
- "Mark attendance for class nine B"
- "Show details of student roll number one class nine B"

**Tips for better recognition:**
- Speak clearly and slowly
- Use a quiet environment
- Mention roll number AND class
- Say full subject names (Mathematics instead of Math)
- Pause between subjects when entering marks

**Issue: "Student not found" error**
- Verify class and section exist (1-10, A/B/C)
- Check roll number is 1-20
- Verify database was seeded correctly
- Check Django admin to see available students

---

## Quick Start Commands Summary

**Start everything (3 terminals):**

**Terminal 1 - PostgreSQL (if using Docker):**
```bash
docker-compose up -d
```

**Terminal 2 - Backend:**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python manage.py runserver
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/v1
- Django Admin: http://localhost:8000/admin

**Login:**
- Teacher: `teacher1` / `password123`
- Admin: `admin` / `admin123`

---

## Next Steps

1. **Explore Admin Panel:** Visit `http://localhost:8000/admin` to see all data
2. **Try Different Commands:** Test attendance marking and student details lookup
3. **Add More Data:** Use Django admin to add more students, classes, or subjects
4. **Check Audit Logs:** View all voice commands in admin panel
5. **Review Code:** Explore the codebase to understand the architecture

## Development Tips

### Hot Reload
Both frontend and backend support hot reload:
- **Backend:** Django auto-reloads on file changes
- **Frontend:** Vite hot-reloads React components instantly

### Viewing Logs
- **Backend logs:** Terminal running Django server
- **Frontend logs:** Browser console (F12)
- **Database logs:** Django admin or PostgreSQL directly

### Database Management
```bash
# Access PostgreSQL shell
docker exec -it reatoa_postgres psql -U postgres -d reatoa_db

# Or if manual install:
psql -U postgres -d reatoa_db

# Useful queries:
SELECT * FROM students LIMIT 5;
SELECT * FROM marks;
SELECT * FROM voice_commands ORDER BY created_at DESC LIMIT 10;
```

### Reset Database
```bash
cd backend
python manage.py flush  # Deletes all data
python manage.py migrate
python ../scripts/seed_database.py  # Re-seed
```

---

## Production Deployment Notes

**Not covered in this guide, but key points:**

1. Set `DEBUG=False` in production
2. Use proper `SECRET_KEY`
3. Configure `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`
4. Use gunicorn instead of Django dev server
5. Use managed PostgreSQL (AWS RDS, Heroku Postgres, etc.)
6. Serve static files via CDN
7. Use HTTPS (required for microphone access)
8. Consider GPU server for faster Whisper processing
9. Setup proper logging and monitoring
10. Regular database backups

---

## Support

If you encounter issues not covered here:

1. Check error messages carefully
2. Search error messages online
3. Check Django and React documentation
4. Review GitHub issues (if repository available)

---

**Congratulations!** You now have a fully functional voice-driven school ERP system.

Try entering marks for all 20 students in class 9B using voice commands to test the MVP functionality.
