# SecureVote REST API Reference

All requests and responses use `application/json` format unless otherwise specified.
Protected endpoints require a Bearer token in the `Authorization` header: `Authorization: Bearer <access_token>`.

---

## 1. System & Authentication Endpoints

### `GET /health`
* **Description**: Application health check endpoint.
* **Authentication**: None (Public)
* **Response (200 OK)**:
  ```json
  {
    "status": "ok",
    "app": "SecureVote API",
    "version": "0.1.0",
    "environment": "development"
  }
  ```

### `POST /api/auth/login`
* **Description**: Authenticate administrators or booth operators.
* **Authentication**: None (Rate limited: 120 req/min)
* **Request Body**:
  ```json
  {
    "username": "admin",
    "password": "admin123"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5...",
    "token_type": "bearer",
    "role": "admin",
    "username": "admin",
    "expires_in_seconds": 3600
  }
  ```
* **Errors**: `401 Unauthorized` for invalid credentials.

---

## 2. Voter Enrollment Endpoints

### `POST /api/enroll`
* **Description**: Register an eligible citizen with biometric minutiae template and salted ID hash.
* **Authentication**: Operator or Admin (`Authorization: Bearer <token>`)
* **Pre-condition**: Polling must be `closed`. Blocked with `400 Bad Request` if polling is `open`.
* **Request Body**:
  ```json
  {
    "name": "Elena Rostova",
    "id_type": "National Identity Card",
    "id_number": "NAT-987654321",
    "fingerprint_image": "<base64_encoded_sample>"
  }
  ```
* **Response (201 Created)**:
  ```json
  {
    "voter_id": "c1f7a4d2-7c3e-4f3b-9e3d-2b7e5f1a9c3d",
    "name": "Elena Rostova",
    "id_type": "National Identity Card",
    "id_last4": "4321",
    "has_voted": "N",
    "enrolled_at": "2026-10-16T14:00:00Z"
  }
  ```
* **Errors**:
  - `400 Bad Request`: Polling is currently open, or biometric extraction failed.
  - `409 Conflict`: ID number already registered, or duplicate-person biometric match detected.

### `GET /api/voters`
* **Description**: Search registered citizens by legal name. Returns safe verification fields only.
* **Authentication**: Operator or Admin
* **Query Parameters**:
  - `name` (optional): Partial or full name string
* **Response (200 OK)**:
  ```json
  [
    {
      "voter_id": "c1f7a4d2-7c3e-4f3b-9e3d-2b7e5f1a9c3d",
      "name": "Elena Rostova",
      "id_type": "National Identity Card",
      "id_last4": "4321",
      "has_voted": "N",
      "enrolled_at": "2026-10-16T14:00:00Z"
    }
  ]
  ```

---

## 3. Verification & Voting Booth Endpoints

### `POST /api/verify`
* **Description**: 1:1 biometric minutiae matching at the booth. Issues short-lived single-use vote token on success.
* **Authentication**: Operator or Admin (Rate limited)
* **Pre-condition**: Polling must be `open`.
* **Request Body**:
  ```json
  {
    "voter_id": "c1f7a4d2-7c3e-4f3b-9e3d-2b7e5f1a9c3d",
    "fingerprint_scan": "<base64_encoded_scan>",
    "workstation_id": "kiosk-north-01"
  }
  ```
* **Response (200 OK - Allowed)**:
  ```json
  {
    "allowed": true,
    "result": "SUCCESS",
    "reason": "Biometric identity verified successfully. Proceed to ballot kiosk.",
    "vote_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "expires_in_seconds": 120
  }
  ```
* **Response (200 OK - Denied)**:
  ```json
  {
    "allowed": false,
    "result": "DUPLICATE_ATTEMPT",
    "reason": "Duplicate attempt: Voter has already cast a ballot in this election.",
    "vote_token": null,
    "expires_in_seconds": null
  }
  ```

### `POST /api/vote`
* **Description**: Cast an anonymous ballot in an atomic database transaction.
* **Authentication**: None (Protected by signed single-use `vote_token`)
* **Request Body**:
  ```json
  {
    "candidate_id": "cand-001",
    "vote_token": "eyJhbGciOiJIUzI1NiIsIn..."
  }
  ```
* **Response (201 Created)**:
  ```json
  {
    "success": true,
    "message": "Ballot successfully cast and recorded anonymously.",
    "vote_id": "7b8a9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d",
    "vote_date": "2026-10-16"
  }
  ```
* **Errors**:
  - `401 Unauthorized`: Expired or forged vote token.
  - `403 Forbidden`: Polling is closed.
  - `404 Not Found`: Candidate ID does not exist.
  - `409 Conflict`: Token already consumed, or voter eligibility flip conflict (race condition).

---

## 4. Admin & Election Management Endpoints

### `GET /api/admin/polling/status`
* **Description**: Retrieve current election lifecycle status.
* **Response (200 OK)**:
  ```json
  {
    "polling_status": "open",
    "is_open": true,
    "updated_at": "2026-10-16T14:15:00Z"
  }
  ```

### `POST /api/admin/polling/open`
* **Description**: Open polling session. Locks voter enrollment and candidate slate changes.
* **Authentication**: Admin Only

### `POST /api/admin/polling/close`
* **Description**: Close polling session. Unlocks election results tally.
* **Authentication**: Admin Only

### `GET /api/candidates`
* **Description**: List all candidates on ballot.

### `POST /api/candidates`
* **Description**: Add candidate. Blocked with `400 Bad Request` if polling is `open`.
* **Authentication**: Admin Only

### `GET /api/results`
* **Description**: Retrieve official ballot tallies and percentages per candidate.
* **Pre-condition**: Polling must be `closed`.
* **Errors**: `403 Forbidden` if polling is currently `open`.
* **Response (200 OK)**:
  ```json
  {
    "total_votes": 1250,
    "polling_status": "closed",
    "results": [
      {
        "candidate_id": "cand-001",
        "name": "Elena Rostova",
        "party": "Democratic Alliance",
        "vote_count": 650,
        "percentage": 52.0
      }
    ]
  }
  ```

### `GET /api/stats`
* **Description**: Summary metrics of enrolled voters, votes cast, and denied attempts.
* **Authentication**: Operator or Admin

### `GET /api/logs`
* **Description**: Paginated audit log of all verification attempts.
* **Authentication**: Operator or Admin
* **Query Parameters**: `result`, `voter_id`, `page`, `page_size`.
