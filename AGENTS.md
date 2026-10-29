# SecureVote - Agent & Developer Design Rules

This document specifies the non-negotiable architectural and design rules for **SecureVote**, a duplicate-vote prevention system. All AI agents, contributors, and developers working on this codebase must adhere strictly to these constraints.

---

## Non-Negotiable Design Rules

### 1. Absolute Separation Between Voter and Vote Records
* **Constraint**: The `VOTE` table must have **NO** link to the `VOTER` table.
* **Prohibited**:
  - Foreign keys referencing `VOTER`.
  - Voter identifiers (`voter_id`, national ID, biometric ID, IP address, device fingerprints).
  - Timestamps with precision finer than a calendar date (e.g., store only `vote_date DATE` / `YYYY-MM-DD`, never store hours, minutes, seconds, or milliseconds).
* **Rationale**: Prevents deanonymization through correlation attacks or side-channel timing analysis.

### 2. Random UUIDs for Vote Identifiers
* **Constraint**: `vote_id` MUST always be generated as a cryptographically secure random UUID (UUIDv4).
* **Prohibited**: Sequential integers, auto-incrementing identity columns, database sequences, or time-ordered UUIDs (UUIDv1/v6/v7).
* **Rationale**: Eliminates ballot submission order tracking and sequence enumeration.

### 3. Atomic Eligibility Flip and Vote Insertion
* **Constraint**: Flipping the voter's status and inserting the ballot MUST occur within the same database transaction:
  ```sql
  UPDATE VOTER
  SET has_voted = 'Y', voted_at = SYSDATE
  WHERE voter_id = :voter_id AND has_voted = 'N';
  ```
  - The application must inspect row count: if `rows_updated == 0`, immediately abort and rollback (preventing race conditions / double voting).
  - The ballot insertion into `VOTE` occurs within this exact transaction before committing.
* **Prohibited**: Separate transactions, pre-checking `has_voted` in Python without row-level lock or conditional update, or decoupled event-driven writes.

### 4. Zero Storage of Raw National / Government ID Numbers
* **Constraint**: Never store plaintext ID numbers.
* **Permitted Storage**:
  - Only the last 4 digits (for operator verification assistance: e.g., `id_last4 CHAR(4)`).
  - A salted cryptographic hash (e.g., SHA-256 or Argon2/PBKDF2 with a per-voter or high-entropy system salt).
* **Prohibited**: Full identity numbers, reversible encryption of national IDs, or unsalted hashes.

### 5. Application-Level Biometric Template Encryption
* **Constraint**: Fingerprint minutiae/templates MUST be encrypted at the application layer prior to being written to the database.
* **Mechanism**: Use strong symmetric encryption (AES-256-GCM / authenticated encryption) with keys managed strictly via environment configuration / KMS.
* **Prohibited**: Storing raw biometric templates, unencrypted binary blobs, or relying solely on database-at-rest encryption.

### 6. Comprehensive Verification Audit Logging
* **Constraint**: Every voter verification attempt—whether allowed, denied, duplicate, or errored—MUST be logged to the `VERIFICATION_LOG` table.
* **Logged Fields**: Timestamp, verification result (`SUCCESS`, `DUPLICATE_ATTEMPT`, `INVALID_CREDENTIALS`, `BIOMETRIC_MISMATCH`), reason, workstation/booth ID, and hashed identifier.
* **Prohibited**: Silent rejections or bypassing the audit log on failed matches.

### 7. Strict Environment-Based Configuration
* **Constraint**: All configuration, database credentials, encryption keys, and environment-specific settings MUST be injected via environment variables.
* **Requirements**:
  - Maintain a comprehensive `.env.example` documenting all configuration keys with safe sample values.
  - No credentials, salts, API keys, or database passwords hardcoded in code or committed to version control.
