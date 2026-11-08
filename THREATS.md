# TrustVault – Threat Model

## 1. Project Overview

TrustVault is a secure document management platform designed to protect confidential documents through authentication, role-based access control, document-level permissions, access expiry and audit logging.

The system supports three roles:

- **Administrator:** Manages users, assigns roles and reviews security activity.
- **Document Owner:** Uploads and manages documents and controls sharing permissions.
- **Viewer:** Accesses documents shared with them according to their assigned permissions.

Authorization is enforced on the server rather than relying only on frontend controls.

## 2. Assets to Protect

- Confidential documents uploaded by users.
- User accounts and password hashes.
- Document ownership and access permissions.
- Document metadata.
- Audit logs and integrity hashes.
- User sessions and authentication information.
- Administrator privileges and role assignments.

## 3. Potential Threats and Security Controls

### Threat 1: Unauthorized Document Access

**Risk:** An unauthorized user may try to access another user's document using a direct URL.

**Security Controls:**
- Authentication is required for protected document routes.
- Document-level permissions are checked on the server.
- Unauthorized download and edit attempts are rejected.
- Administrator accounts do not automatically receive document-content access.
- Denied access attempts are recorded in the audit log.

**Testing:** Automated tests verify that unauthorized users cannot download or edit documents. Live testing also verified that an administrator without document permission cannot download an Owner's document.

### Threat 2: Weak Password Security

**Risk:** Attackers may obtain passwords if they are stored as plain text or use easily guessed passwords.

**Security Controls:**
- Passwords are stored as password hashes.
- Passwords must contain at least eight characters, including uppercase letters, lowercase letters, numbers and special characters.
- Login verifies submitted passwords against stored hashes.
- Administrator-issued temporary passwords require users to change their password after login.

**Testing:** Registration and login tests verify password hashing and incorrect-password rejection.

### Threat 3: Excessive Document Permissions

**Risk:** A document may be shared with users who should not have access, or a user may retain access after permission is revoked.

**Security Controls:**
- Owners can grant Read or Edit permissions.
- Owners can revoke permissions.
- Access permissions can have an expiry date.
- Expired permissions are rejected by the permission service.
- Revoked permissions no longer authorize document access.
- Viewers cannot upload, delete or share documents.

**Testing:** Permission tests cover read-only access, edit access, unauthorized access, expired permissions and revoked access.

### Threat 4: Malicious File Uploads

**Risk:** Attackers may upload executable, oversized or incorrectly formatted files.

**Security Controls:**
- Only PDF, PNG, JPG, JPEG and TXT extensions are allowed.
- File signatures are checked for supported binary formats.
- Text files are checked for valid UTF-8 encoding.
- Upload size is limited to 10 MB.
- Internal filenames are generated using UUIDs.
- Uploaded documents are stored outside the public static directory.

**Limitations:** File signature checks do not guarantee that a file is harmless. Malware scanning and deeper file-content inspection are not currently implemented.

### Threat 5: Path Traversal

**Risk:** An attacker may try to access or delete files outside the document storage directory.

**Security Controls:**
- Internal filenames are generated using UUIDs.
- Deletion accepts only valid UUID-based filenames with allowed extensions.
- The resolved file path is checked against the private storage directory.

**Testing:** Storage tests verify rejection of path traversal and invalid filenames.

### Threat 6: Audit Log Tampering

**Risk:** Someone may modify audit records to hide unauthorized activity.

**Security Controls:**
- Audit entries use SHA-256 hashes.
- Each entry contains the previous entry's hash.
- The audit verification function checks the hash chain.
- Modified records are detected by integrity verification.
- Successful and denied security-sensitive actions are recorded.
- Denied administrator role-change attempts are also recorded with their reasons.

**Limitations:** A person with full database control could potentially modify all records and recalculate the hashes. External immutable audit storage is not currently implemented.

**Testing:** Automated tests verify audit-chain integrity and tampering detection. Live testing also confirmed that an attempted downgrade of an Owner with active documents was denied and recorded.

### Threat 7: Session Attacks

**Risk:** An attacker may attempt to misuse an authenticated user's session.

**Security Controls:**
- HTTP-only session cookies are enabled.
- SameSite cookie protection is configured.
- Secure cookies are enabled in production.
- The live application is deployed over HTTPS.

**Further Protection:** Additional session monitoring and security testing should be considered.

### Threat 8: Cross-Site Request Forgery (CSRF)

**Risk:** A malicious website may attempt to submit unwanted actions using an authenticated user's session.

**Security Controls:**
- Flask-WTF CSRF protection is initialized.
- State-changing forms use CSRF protection.
- CSRF is disabled in the automated test configuration only and remains enabled during normal application operation.

**Testing:** The automated tests run with CSRF disabled to simplify test requests. Production operation should retain CSRF protection.

### Threat 9: Unauthorized Role Changes

**Risk:** A user may attempt to gain administrator or document-owner privileges without authorization, or an administrator may accidentally downgrade an Owner who still owns active documents.

**Security Controls:**
- New registrations receive the Viewer role by default.
- Only an administrator can assign or change user roles.
- Administrator role changes and self-demotion are protected.
- Owners with active documents cannot be downgraded to Viewers.
- Denied role-change attempts are recorded in the audit log.

**Testing:** Live testing confirmed that the attempted downgrade of user ID 5 was blocked and recorded as `ROLE_CHANGE — DENIED`.

## 4. Security Testing

The automated test suite covers:

- Registration and login.
- Password hashing and incorrect passwords.
- Unauthorized document downloads and edits.
- Owner, editor and read-only permissions.
- Expired document permissions.
- Audit-chain verification and tampering detection.
- Invalid file uploads and unsafe deletion filenames.
- Document access and storage operations.

The latest completed automated test run passed **26 tests**.

Live testing also covered document sharing, access revocation, administrator access restrictions, password reset and denied role-change logging.

## 5. Remaining Security Improvements

The following improvements are planned or require further verification:

- Add malware scanning for uploaded files.
- Use persistent private object storage for production documents.
- Configure external immutable audit-log backups.
- Perform independent penetration and security testing.
- Improve security monitoring and alerting.
- Review administrator account bootstrap and recovery procedures.
- Continue testing authentication and rate-limiting protections.

**Deployment limitation:** The current Render free deployment uses temporary filesystem storage. Uploaded files may not survive service restarts or redeployments. The production database is hosted separately on PostgreSQL.

## 6. Conclusion

TrustVault uses authentication, server-side document permissions, private file storage, file validation and hash-linked audit records to improve document security.

The application has passed its latest 26 automated tests, and important security scenarios have also been tested on the live website.

However, passing these tests does not prove that the application is completely secure. Additional security testing, persistent file storage and external immutable audit backups are necessary before handling real confidential documents.