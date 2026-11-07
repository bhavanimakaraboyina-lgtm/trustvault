# TrustVault

A secure document management platform with role-based access control and audit tracking.

## Live Website

https://trustvault-p0kj.onrender.com
# TrustVault – Secure Document Management System

## Project Overview

TrustVault is a secure document management platform designed to protect confidential documents. It provides user authentication, document-level access permissions, permission expiry and audit logging.

Users can upload, manage, search, share and access documents based on their assigned permissions.

## Key Features

- User registration and secure login.
- Administrator, document owner and authorized viewer/editor access.
- Secure document upload and private storage.
- Document sharing with Read and Edit permissions.
- Permission expiry and immediate revocation.
- Document search by filename, owner, category and date.
- Access-denial tracking.
- Audit logs with SHA-256 hash-chain verification.
- Administrator audit dashboard.
- Password reset by administrator with forced password change.
- File validation and 10 MB upload limit.

## Technologies Used

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite
- **ORM:** Flask-SQLAlchemy
- **Authentication:** Flask-Login
- **CSRF Protection:** Flask-WTF
- **Rate Limiting:** Flask-Limiter
- **Testing:** Pytest
- **Code Editor:** Visual Studio Code
- **Version Control:** Git and GitHub

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

The current automated test suite contains **23 passing tests**.

## Security Measures

- Password hashing.
- Server-side document permission checks.
- Private document storage outside the public static directory.
- File extension and signature validation.
- UUID-based internal filenames.
- CSRF protection.
- Secure session cookie settings.
- Permission expiry and revocation.
- SHA-256 hash-linked audit records.

For additional security information, see [THREATS.md](THREATS.md).

## Current Limitations and Future Improvements

- Add malware scanning for uploaded documents.
- Implement a secure administrator bootstrap process.
- Improve authentication rate limiting.
- Use PostgreSQL for production.
- Configure HTTPS and production secrets.
- Use persistent private storage.
- Add external immutable audit-log backups.
- Perform additional security testing.

## AI Development Documentation

The AI-assisted development process, prompts, outcomes and changes are documented in [PROMPTS.md](PROMPTS.md).

## Project Status

The application has been implemented and tested locally. Production deployment and additional security hardening are still required.

## Author

**Makaraboyina Durga Bhavani**
