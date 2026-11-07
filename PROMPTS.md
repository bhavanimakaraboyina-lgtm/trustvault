# TrustVault – AI Prompt Log

This file records the AI assistance used during the development of TrustVault. The entries summarize the prompts, AI guidance, problems encountered, and actions taken.

## Entry 1 – 4 November 2026: Project Architecture

**Prompt:** Help me build TrustVault, a secure document management platform with administrator, document owner, and viewer permissions.

**AI Output:** Suggested a Flask-based application with authentication, document management, role-based access control, database models, and audit logging.

**Problem Encountered:** The initial project structure was confusing, especially creating Python files and folders correctly in VS Code.

**Changed Action:** Created the application structure using Flask, SQLAlchemy, and separate routes and services.

**Commit:** [Initial TrustVault commit](https://github.com/bhavanimakaraboyina-lgtm/trustvault/commit/03726f5)

## Entry 2 – 4 November 2026: Authorization and Access Control

**Prompt:** How can I ensure that users can access only documents shared with them and cannot access other users' confidential files?

**AI Output:** Recommended server-side document permission checks for every protected request, with separate Read and Edit permissions.

**Problem Encountered:** A user without permission must not be able to access a document by directly entering its URL.

**Changed Action:** Implemented permission checks for document reading, downloading, and editing. Added permission expiry and access revocation.

**Commit:** [Initial TrustVault commit](https://github.com/bhavanimakaraboyina-lgtm/trustvault/commit/03726f5)

## Entry 3 – 5 November 2026: Audit Trail and Security

**Prompt:** How can TrustVault record who accessed a document and when, including unsuccessful access attempts?

**AI Output:** Suggested audit records containing the actor, document, action, outcome, timestamp, and hash-chain information.

**Problem Encountered:** Audit records should also capture denied access attempts, not only successful activities.

**Changed Action:** Implemented audit logging for document activities and hash-chain verification. Added tests for valid and tampered audit records.

**Commit:** [Initial TrustVault commit](https://github.com/bhavanimakaraboyina-lgtm/trustvault/commit/03726f5)

## Entry 4 – 5 November 2026: Secure File Storage

**Prompt:** How can I securely upload and store confidential documents without exposing their original filenames or allowing unsafe file uploads?

**AI Output:** Recommended file extension and content-signature validation, random UUID-based stored filenames, and private server-side storage.

**Problem Encountered:** Files with unsupported extensions or invalid file content must be rejected.

**Changed Action:** Implemented file validation, generated random storage filenames, and added storage tests for invalid files and filenames.

**Commit:** [Initial TrustVault commit](https://github.com/bhavanimakaraboyina-lgtm/trustvault/commit/03726f5)

## Entry 5 – 6 November 2026: Testing and Authorization Verification

**Prompt:** Help me test authentication, document permissions, file storage, and audit logging to identify security problems.

**AI Output:** Suggested automated tests for registration, login, unauthorized access, expired permissions, file validation, document deletion, and audit-chain integrity.

**Problem Encountered:** Unauthorized users must not be able to download, edit, or delete another user's documents.

**Changed Action:** Added and executed automated tests. All 23 tests passed.

**Commit:** [Initial TrustVault commit](https://github.com/bhavanimakaraboyina-lgtm/trustvault/commit/03726f5)

---

**Note:** These entries summarize the actual development work and AI assistance used during the project. Future prompts, changes, and commits will be recorded as development continues.