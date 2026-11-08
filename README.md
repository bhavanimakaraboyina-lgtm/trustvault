# TrustVault – Secure Document Management System

A secure document management platform with role-based access control, document-level permissions and audit tracking.

## Live Website

https://trustvault-p0kj.onrender.com

## Project Overview

TrustVault is a secure document management platform designed to protect confidential documents and prevent unauthorized access.

It provides user authentication, role-based access control, document-level permissions, permission expiry, access revocation and audit logging.

Users can upload, manage, search, share and access documents according to their assigned roles and permissions.

## Key Features

- User registration and secure login.
- Three roles: Administrator, Document Owner and Viewer.
- Secure document upload and private storage.
- Document sharing with Read and Edit permissions.
- Permission expiry and immediate access revocation.
- Document search by filename, owner, category and date.
- Server-side authorization checks.
- Access-denial tracking.
- SHA-256 hash-linked audit records.
- Administrator audit dashboard.
- Administrator password reset with forced password change.
- File validation and 10 MB upload limit.
- LeakTrace document watermarking.

## Technologies Used

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite (local development), PostgreSQL (production)
- **ORM:** Flask-SQLAlchemy
- **Authentication:** Flask-Login
- **CSRF Protection:** Flask-WTF
- **Rate Limiting:** Flask-Limiter
- **Testing:** Pytest
- **Code Editor:** Visual Studio Code
- **Version Control:** Git and GitHub
- **Deployment:** Render

## Project Structure

```text
trustvault/
│
├── app/
│   ├── routes/
│   ├── services/
│   ├── templates/
│   ├── static/
│   ├── models.py
│   ├── extensions.py
│   └── __init__.py
│
├── tests/
├── private_storage/
├── instance/
├── run.py
├── requirements.txt
├── .env.example
├── .gitignore
├── PROMPTS.md
├── THREATS.md
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/bhavanimakaraboyina-lgtm/trustvault.git
```

### 2. Open the project folder

```bash
cd trustvault
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the virtual environment

For Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Configure environment variables

Create a local `.env` file using `.env.example` as a template.

Set a strong, unique `SECRET_KEY` before running the application.

For production, configure `DATABASE_URL` with your PostgreSQL connection string.

Never commit the `.env` file or expose database credentials.

### 7. Run the application

```bash
python run.py
```

Open the local URL displayed in the terminal in your web browser.

## Running Tests

Run the automated test suite using:

```bash
python -m pytest -v -p no:cacheprovider
```

The latest automated test run passed **26 tests**.

## Security Measures

- Password hashing.
- Server-side role and document permission checks.
- Private document storage outside the public static directory.
- File extension and signature validation.
- UUID-based internal filenames.
- CSRF protection.
- Secure session cookie settings in production.
- Permission expiry and immediate revocation.
- SHA-256 hash-linked audit records.
- Logging of successful and denied security-sensitive actions.

For additional security information, see [THREATS.md](THREATS.md).

## Current Limitations and Future Improvements

- Add malware scanning for uploaded documents.
- Use persistent object storage for production documents.
- Configure external immutable audit-log backups.
- Perform independent security testing.
- Improve monitoring and security alerts.

**Storage note:** The current Render free deployment uses temporary filesystem storage. Uploaded files may not survive service restarts or redeployments. The production database is hosted separately on PostgreSQL.

## AI Development Documentation

The AI-assisted development process, prompts, outcomes and implementation changes are documented in [PROMPTS.md](PROMPTS.md).

## Project Status

TrustVault is deployed and available online. The application has passed 26 automated tests, and key authentication, document permission, access revocation and audit logging scenarios have been tested.

## Author

**Makaraboyina Durga Bhavani**