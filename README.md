# ReATOA - Voice-Driven School ERP System

A voice-driven ERP system for schools that enables teachers to enter marks, mark attendance, and view student details using voice commands.

## Features

- **Voice-Driven Interface**: Teachers use voice commands to interact with the system
- **Marks Entry**: Enter marks for multiple subjects via voice
- **Attendance Tracking**: Mark attendance for entire classes
- **Student Management**: View comprehensive student information
- **Automatic Grade Calculation**: Grades calculated automatically based on marks
- **Audit Logging**: Complete audit trail of all actions
- **Confirmation Flow**: Preview and confirm before executing commands

## Tech Stack

### Backend
- Django 5.0 + Django REST Framework
- PostgreSQL database
- Whisper (OpenAI) for speech-to-text
- JWT authentication

### Frontend
- React 18 + Vite
- Redux Toolkit for state management
- Axios for API calls
- MediaRecorder API for audio recording

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+ (or use Docker)
- Git

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ReATOA
```

### 2. Backend Setup

#### Create Virtual Environment

```bash
cd backend
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

#### Install Dependencies

```bash
pip install -r requirements/development.txt
```

#### Setup Environment Variables

Create a `.env` file in the `backend` directory:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
SECRET_KEY=your-secret-key-here
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

#### Setup PostgreSQL

**Option 1: Using Docker (Recommended)**

```bash
# From project root
docker-compose up -d
```

**Option 2: Manual PostgreSQL Setup**

Install PostgreSQL and create database:

```bash
psql -U postgres
CREATE DATABASE reatoa_db;
\q
```

#### Run Migrations

```bash
cd backend
python manage.py migrate
```

#### Seed Database with Test Data

```bash
python ../scripts/seed_database.py
```

This creates:
- 10 classes (1st to 10th)
- 3 sections (A, B, C) per class
- 20 students per class section (600 total students)
- 5 subjects (Math, Hindi, English, Science, Social)
- 3 exam types (Unit Test, Midterm, Final)
- 5 teacher accounts
- 1 admin account

**Default Login Credentials:**
- Admin: `admin` / `admin123`
- Teachers: `teacher1` to `teacher5` / `password123`

#### Start Django Server

```bash
python manage.py runserver
```

Backend will be available at: `http://localhost:8000`

### 3. Frontend Setup

#### Install Dependencies

```bash
cd frontend
npm install
```

#### Create Environment File

Create `.env` in the `frontend` directory:

```env
VITE_API_URL=http://localhost:8000/api/v1
```

#### Start Development Server

```bash
npm run dev
```

Frontend will be available at: `http://localhost:5173`

## Usage

### Voice Commands

#### Marks Entry

**Command:**
> "Enter marks for roll number 22, class 9B. Maths 85, Hindi 78, English 92"

**System Response:**
1. Transcribes your voice
2. Shows confirmation dialog with:
   - Student name and details
   - Marks table preview
3. Click "Confirm" to save marks
4. Grades calculated automatically

#### Attendance Marking

**Command:**
> "Mark attendance for class 9B"

**System Response:**
1. Shows class details
2. Marks all students present by default
3. Confirm to save attendance

#### Student Details

**Command:**
> "Show details of student roll number 22, class 9B"

**System Response:**
- Student information
- Marks summary by exam type
- Attendance percentage

## Project Structure

```
ReATOA/
├── backend/
│   ├── apps/
│   │   ├── authentication/       # User authentication & teachers
│   │   ├── academics/            # Students, classes, sections
│   │   ├── marks/                # Marks & grade management
│   │   ├── attendance/           # Attendance tracking
│   │   ├── voice_processing/     # Voice command pipeline
│   │   └── audit/                # Audit logging
│   ├── config/
│   │   └── settings/             # Django settings
│   ├── media/                    # Uploaded audio files
│   └── manage.py
│
├── frontend/
│   ├── src/
│   │   ├── components/           # React components
│   │   ├── hooks/                # Custom hooks
│   │   ├── services/             # API services
│   │   ├── store/                # Redux store
│   │   └── pages/                # Page components
│   └── package.json
│
├── scripts/
│   └── seed_database.py          # Database seeding
│
├── docker-compose.yml            # PostgreSQL setup
└── README.md
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login/` - Login
- `POST /api/v1/auth/token/refresh/` - Refresh token

### Voice Processing
- `POST /api/v1/voice/upload/` - Upload voice command
- `POST /api/v1/voice/commands/{id}/confirm/` - Confirm command
- `POST /api/v1/voice/commands/{id}/reject/` - Reject command
- `GET /api/v1/voice/commands/` - Command history

### Admin Panel

Access Django admin at: `http://localhost:8000/admin/`

Login with admin credentials to manage:
- Users and teachers
- Students and classes
- Marks and grades
- Attendance records
- Voice commands
- Audit logs

## Whisper Model

On first voice command, Whisper will automatically download the base model (~150MB) to `~/.cache/whisper/`. This happens once.

**Processing Time:** ~5-10 seconds per 30-second audio clip on CPU

**GPU Acceleration:** If CUDA-enabled GPU available, set `WHISPER_DEVICE=cuda` in `.env` for 3-5x faster processing.

## Testing Voice Commands

1. Login as a teacher (e.g., `teacher1` / `password123`)
2. Click the microphone button
3. Speak clearly: "Enter marks for roll number 1, class 9B. Maths 85, Hindi 78"
4. Review the confirmation dialog
5. Click "Confirm" to execute

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality

```bash
# Backend linting
cd backend
flake8

# Format code
black .
```

## Troubleshooting

### Whisper Model Not Loading

If Whisper fails to load:
1. Check internet connection (first-time download)
2. Ensure sufficient disk space (~200MB)
3. Check logs: `python manage.py runserver` output

### Database Connection Error

1. Verify PostgreSQL is running: `docker ps` or check PostgreSQL service
2. Check credentials in `.env`
3. Test connection: `psql -U postgres -d reatoa_db`

### Audio Recording Not Working

1. Grant microphone permission in browser
2. Use HTTPS in production (required for MediaRecorder API)
3. Check browser console for errors

### CORS Errors

Ensure `CORS_ALLOWED_ORIGINS` in Django settings includes your frontend URL:
- Development: `http://localhost:5173`
- Production: Your production frontend URL

## Production Deployment

### Backend

1. Set `DEBUG=False` in `.env`
2. Configure `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`
3. Use `gunicorn` instead of Django dev server
4. Setup proper database (managed PostgreSQL)
5. Use environment-specific settings: `config.settings.production`

### Frontend

```bash
cd frontend
npm run build
```

Deploy the `dist` directory to your hosting service.

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.

---

Built with Claude Code
