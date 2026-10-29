-- ============================================================================
-- SecureVote - Oracle 21c XE Database Schema (001_schema.sql)
-- Architecture Constraint: ABSOLUTE SEPARATION BETWEEN VOTER AND VOTE TABLES
-- ============================================================================

-- 1. VOTER Table
-- Tracks eligible citizens, application-encrypted biometric templates, and voting status
CREATE TABLE VOTER (
    voter_id VARCHAR2(36) PRIMARY KEY,
    name VARCHAR2(100) NOT NULL,
    id_type VARCHAR2(50) NOT NULL,
    id_last4 CHAR(4) NOT NULL,
    id_hash VARCHAR2(64) NOT NULL,
    fingerprint_template BLOB NOT NULL,
    has_voted CHAR(1) DEFAULT 'N' NOT NULL,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    voted_at TIMESTAMP NULL,
    CONSTRAINT chk_voter_has_voted CHECK (has_voted IN ('Y', 'N')),
    CONSTRAINT uq_voter_id_hash UNIQUE (id_hash)
);

CREATE INDEX idx_voter_name ON VOTER(name);
CREATE INDEX idx_voter_has_voted ON VOTER(has_voted);

-- 2. CANDIDATE Table
-- Running candidates for the election
CREATE TABLE CANDIDATE (
    candidate_id VARCHAR2(36) PRIMARY KEY,
    name VARCHAR2(100) NOT NULL,
    party VARCHAR2(100) NOT NULL,
    description VARCHAR2(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 3. VOTE Table
-- Stores cast ballots.
-- CRITICAL AGENTS.md RULE 1:
-- Absolutely NO link to VOTER. No FK to VOTER, no voter_id, no fine-grained timestamps.
-- vote_date stores ONLY calendar date (DATE) to eliminate side-channel timing correlation.
-- vote_id MUST be a random UUIDv4.
CREATE TABLE VOTE (
    vote_id VARCHAR2(36) PRIMARY KEY,
    candidate_id VARCHAR2(36) NOT NULL,
    vote_date DATE NOT NULL,
    CONSTRAINT fk_vote_candidate FOREIGN KEY (candidate_id) REFERENCES CANDIDATE(candidate_id)
);

CREATE INDEX idx_vote_candidate ON VOTE(candidate_id);
CREATE INDEX idx_vote_date ON VOTE(vote_date);

-- 4. VERIFICATION_LOG Table
-- Audit trail of every biometric verification attempt (allowed, denied, duplicate, mismatch)
CREATE TABLE VERIFICATION_LOG (
    log_id VARCHAR2(36) PRIMARY KEY,
    voter_id VARCHAR2(36) NULL,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    result VARCHAR2(50) NOT NULL,
    reason VARCHAR2(255) NOT NULL,
    workstation_id VARCHAR2(50) DEFAULT 'booth-default'
);

CREATE INDEX idx_verif_attempted ON VERIFICATION_LOG(attempted_at);
CREATE INDEX idx_verif_result ON VERIFICATION_LOG(result);
CREATE INDEX idx_verif_voter ON VERIFICATION_LOG(voter_id);

-- 5. ADMIN_USER Table
-- Operators and system administrators
CREATE TABLE ADMIN_USER (
    admin_id VARCHAR2(36) PRIMARY KEY,
    username VARCHAR2(50) NOT NULL,
    password_hash VARCHAR2(255) NOT NULL,
    role VARCHAR2(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_admin_username UNIQUE (username),
    CONSTRAINT chk_admin_role CHECK (role IN ('admin', 'booth-operator', 'operator'))
);

-- 6. ELECTION_STATE Table
-- Tracks election lifecycle (created, polling_open, polling_closed)
CREATE TABLE ELECTION_STATE (
    state_key VARCHAR2(50) PRIMARY KEY,
    state_value VARCHAR2(50) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 7. CONSUMED_VOTE_TOKENS Table
-- Tracks consumed (used) single-use vote authorization tokens for replay prevention
CREATE TABLE CONSUMED_VOTE_TOKENS (
    token_jti VARCHAR2(36) PRIMARY KEY,
    consumed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 8. VERIFICATION_LOCKOUT Table
-- Tracks failed biometric verification attempts and lockout windows per voter
CREATE TABLE VERIFICATION_LOCKOUT (
    voter_id VARCHAR2(36) PRIMARY KEY,
    failed_count NUMBER(3) DEFAULT 0 NOT NULL,
    locked_until TIMESTAMP NULL,
    last_failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
