# TrustVault – Threat Model

## 1. Project Overview

TrustVault is a secure document management platform designed to protect confidential documents through authentication, document-level permissions, access expiry and audit logging.

The system supports administrators, document owners and authorized viewers/editors.

## 2. Assets to Protect

- Confidential documents uploaded by users.
- User accounts and password hashes.
- Document ownership and access permissions.
- Document metadata.
- Audit logs and integrity hashes.
- User sessions and authentication information.

## 3. Potential Threats and Security Controls

### Threat 1: Unauthorized Document Access

**Risk:** An unauthorized user may try to access another user's document using a direct URL.

**Security controls:**
- Authentication is required for protected document routes.
- Document-level permissions are checked on the server.
- Unauthorized download and edit attempts are rejected.
- Denied access attempts are recorded in the audit log.

**Testing:** Automated tests verify that unauthorized users cannot download or edit documents.

### Threat 2: Weak Password Security

**Risk:** Attackers may obtain passwords if they are stored as plain text.

**Security controls:**
- Passwords are stored as password hashes.
- Passwords must contain at least eight characters during registration.
- Login verifies the submitted password against the stored hash.

**Testing:** Registration and login tests verify password hashing and incorrect-password rejection.

### Threat 3: Excessive Document Permissions

**Risk:** A document may be shared with users who should not have access.

**Security controls:**
- Owners can grant read or edit permissions.
- Owners can revoke permissions.
- Access permissions can have an expiry date.
- Expired permissions are rejected by the permission service.

**Testing:** Permission tests cover read-only access, edit access, unauthorized access and expired permissions.

### Threat 4: Malicious File Uploads

**Risk:** Attackers may upload executable or incorrectly formatted files.

**Security controls:**
- Only PDF, PNG, JPG, JPEG and TXT extensions are allowed.
- File signatures are checked for supported binary formats.
- Text files are checked for valid UTF-8 encoding.
- Upload size is limited to 10 MB.
- Internal filenames are generated using UUIDs.
- Uploaded documents are stored outside the public static directory.

**Limitations:** File signature checks do not guarantee that a file is harmless. Malware scanning and deeper file-content inspection are not currently implemented.

### Threat 5: Path Traversal

**Risk:** An attacker may try to access or delete files outside the document storage directory.

**Security controls:**
- Internal filenames are generated using UUIDs.
- Deletion accepts only valid UUID-based filenames with allowed extensions.
- The resolved file path is checked against the private storage directory.

**Testing:** Storage tests verify rejection of path traversal and invalid filenames.

### Threat 6: Audit Log Tampering

**Risk:** Someone may modify audit records to hide unauthorized activity.

**Security controls:**
- Audit entries use SHA-256 hashes.
- Each entry contains the previous entry's hash.
- The audit verification function checks the hash chain.
- Modified records are detected by integrity verification.

**Limitations:** A person with full database control could potentially modify all records and recalculate the hashes. External immutable audit storage is not currently implemented.

### Threat 7: Session Attacks

**Risk:** An attacker may attempt to misuse an authenticated user's session.

**Security controls:**
- HTTP-only session cookies are enabled.
- SameSite cookie protection is configured.
- Secure cookies are enabled when the application runs in production.

**Further protection:** HTTPS must be configured in production. Session expiry and additional session monitoring should also be considered.

### Threat 8: Cross-Site Request Forgery (CSRF)

**Risk:** A malicious website may attempt to submit unwanted actions using an authenticated user's session.

**Security controls:**
- Flask-WTF CSRF protection is initialized.
- State-changing forms should include valid CSRF tokens.

**Testing note:** CSRF is disabled in the automated test configuration only. It must remain enabled in normal application operation.

## 4. Security Testing

The project includes automated tests for:

- Registration and login.
- Password hashing and incorrect passwords.
- Unauthorized document downloads and edits.
- Owner, editor and read-only permissions.
- Expired document permissions.
- Audit chain verification and tampering detection.
- Invalid file uploads and unsafe deletion filenames.

The current automated test suite contains 21 passing tests.

## 5. Remaining Security Improvements

The following improvements are planned or require further verification:

- Add malware scanning for uploaded files.
- Add stronger authentication rate limiting.
- Review administrator account creation and privilege assignment.
- Use persistent private file storage in production.
- Use PostgreSQL for production database storage.
- Configure HTTPS and production secrets.
- Consider external immutable audit-log backups.
- Perform additional security testing before production use.

## 6. Conclusion

TrustVault uses authentication, server-side document permissions, private file storage, file validation and hash-linked audit records to improve document security.

The system has passed its current 21 automated tests. However, passing these tests does not prove that the application is completely secure. Additional security testing and production hardening are required before handling real confidential documents.