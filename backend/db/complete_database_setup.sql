-- ============================================================================
-- SECUREVOTE - COMPLETE ORACLE DATABASE SETUP SCRIPT
-- Paste this entire script into SQL*Plus or Oracle SQL Developer.
-- Connect as: securevote_app / madesh777 @ localhost:1521/XEPDB1
-- ============================================================================

SET FEEDBACK ON;

-- ----------------------------------------------------------------------------
-- 1. DROP EXISTING TABLES (Optional: Clean slate, ignore errors if tables don't exist)
-- ----------------------------------------------------------------------------
BEGIN EXECUTE IMMEDIATE 'DROP TABLE VOTE CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE CANDIDATE CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE VOTER CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE ADMIN_USER CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE ELECTION_STATE CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE VERIFICATION_LOG CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE CONSUMED_VOTE_TOKENS CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP TABLE VERIFICATION_LOCKOUT CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;
/

-- ----------------------------------------------------------------------------
-- 2. CREATE TABLES
-- ----------------------------------------------------------------------------

-- Table 1: Staff / Admin / Booth Operators
CREATE TABLE ADMIN_USER (
    admin_id VARCHAR2(36) PRIMARY KEY,
    username VARCHAR2(50) NOT NULL,
    password_hash VARCHAR2(255) NOT NULL,
    role VARCHAR2(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_admin_username UNIQUE (username),
    CONSTRAINT chk_admin_role CHECK (role IN ('admin', 'booth-operator', 'operator'))
);

-- Table 2: Eligible Registered Voters
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

-- Table 3: Election Candidates
CREATE TABLE CANDIDATE (
    candidate_id VARCHAR2(36) PRIMARY KEY,
    name VARCHAR2(100) NOT NULL,
    party VARCHAR2(100) NOT NULL,
    description VARCHAR2(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Table 4: Anonymous Ballots (Strictly decoupled from voter identity)
CREATE TABLE VOTE (
    vote_id VARCHAR2(36) PRIMARY KEY,
    candidate_id VARCHAR2(36) NOT NULL,
    vote_date DATE NOT NULL,
    CONSTRAINT fk_vote_candidate FOREIGN KEY (candidate_id) REFERENCES CANDIDATE(candidate_id)
);
CREATE INDEX idx_vote_candidate ON VOTE(candidate_id);

-- Table 5: Election Lifecycle State
CREATE TABLE ELECTION_STATE (
    state_key VARCHAR2(50) PRIMARY KEY,
    state_value VARCHAR2(50) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Table 6: Audit Trail
CREATE TABLE VERIFICATION_LOG (
    log_id VARCHAR2(36) PRIMARY KEY,
    voter_id VARCHAR2(36) NULL,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    result VARCHAR2(50) NOT NULL,
    reason VARCHAR2(255) NOT NULL,
    workstation_id VARCHAR2(50) DEFAULT 'booth-default'
);

-- Table 7: Single-use Tokens
CREATE TABLE CONSUMED_VOTE_TOKENS (
    token_jti VARCHAR2(36) PRIMARY KEY,
    consumed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Table 8: Lockout Windows
CREATE TABLE VERIFICATION_LOCKOUT (
    voter_id VARCHAR2(36) PRIMARY KEY,
    failed_count NUMBER(3) DEFAULT 0 NOT NULL,
    locked_until TIMESTAMP NULL,
    last_failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ----------------------------------------------------------------------------
-- 3. INSERT STAFF / OPERATOR / ADMIN DATA
-- ----------------------------------------------------------------------------

-- Staff Account 1: General Administrator (admin / admin123)
INSERT INTO ADMIN_USER (admin_id, username, password_hash, role, created_at)
VALUES (
    'staff-admin-001',
    'admin',
    'pbkdf2:sha256:100000$2bdefb884fd5c9ec8369ea4e058a8b08$82580728eed3cd3de23d190283193659149a86511e4c1370c9526d7854c25172',
    'admin',
    CURRENT_TIMESTAMP
);

-- Staff Account 2: Booth Operator (operator / operator123)
INSERT INTO ADMIN_USER (admin_id, username, password_hash, role, created_at)
VALUES (
    'staff-op-002',
    'operator',
    'pbkdf2:sha256:100000$aa1c7b63a0d700e79064ab2bdc700044$d69fdb386992cf11af6c3e80f83f5f1debf16808b37192bf88573c3007764899',
    'booth-operator',
    CURRENT_TIMESTAMP
);

-- Staff Account 3: Election Staff Officer (staff / staff123)
INSERT INTO ADMIN_USER (admin_id, username, password_hash, role, created_at)
VALUES (
    'staff-member-003',
    'staff',
    'pbkdf2:sha256:100000$7a4349b1d2203e78ed4842d38a4f04c4$c8c072e83b5d03944dcc62c6d818389aec9db3c491def6a3f62b7cfeb470ea1d',
    'operator',
    CURRENT_TIMESTAMP
);

-- Staff Account 4: Prabhu Staff / Officer Account (prabhu_staff / prabhu123)
INSERT INTO ADMIN_USER (admin_id, username, password_hash, role, created_at)
VALUES (
    'staff-prabhu-004',
    'prabhu_staff',
    'pbkdf2:sha256:100000$ae9e5c8bdbfaff62d1c16f1616e4f596$4d37097aa5712135fabef301591558ff3cd369c4dd814413b245d50a1eee2c94',
    'admin',
    CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 4. INSERT ELECTION STATE (Polling open so citizens can vote)
-- ----------------------------------------------------------------------------
INSERT INTO ELECTION_STATE (state_key, state_value, updated_at)
VALUES ('polling_status', 'open', CURRENT_TIMESTAMP);

-- ----------------------------------------------------------------------------
-- 5. INSERT ELECTION CANDIDATES
-- ----------------------------------------------------------------------------
INSERT INTO CANDIDATE (candidate_id, name, party, description, created_at)
VALUES ('cand-001', 'Elena Rostova', 'Democratic Alliance', 'Focus on transparent governance and privacy.', CURRENT_TIMESTAMP);

INSERT INTO CANDIDATE (candidate_id, name, party, description, created_at)
VALUES ('cand-002', 'Marcus Vance', 'Forward Progress Coalition', 'Platform supporting technological innovation and civic education.', CURRENT_TIMESTAMP);

INSERT INTO CANDIDATE (candidate_id, name, party, description, created_at)
VALUES ('cand-003', 'Amina Chen', 'Ecological Union', 'Dedicated to sustainable city planning and green energy.', CURRENT_TIMESTAMP);

-- ----------------------------------------------------------------------------
-- 6. INSERT REGISTERED VOTERS (Only these citizens can vote)
-- ----------------------------------------------------------------------------

-- Voter 1: Prabhu
INSERT INTO VOTER (
    voter_id, name, id_type, id_last4, id_hash,
    fingerprint_template, has_voted, enrolled_at
) VALUES (
    'voter-prabhu-001',
    'Prabhu',
    'National ID',
    '4321',
    STANDARD_HASH('GOV_ID_PRABHU_4321', 'SHA256'),
    HEXTORAW('674141414141427132795545565964326b5048635a486235735672526b337450745555694f6952544f3043665f61434f43316e59395a5a506d594345484f6678412d746a7048735057664d666643614935394461735336396856713669754b737a684b44366d743866385472704e78485035576671797147355074674275674b62495277543935435f65333356634a54502d65486539366b79783474555742774835454f366d354e4c4d59616d583043526f45634d41383d'),
    'N',
    CURRENT_TIMESTAMP
);

-- Voter 2: Madeshwaran
INSERT INTO VOTER (
    voter_id, name, id_type, id_last4, id_hash,
    fingerprint_template, has_voted, enrolled_at
) VALUES (
    'voter-madesh-002',
    'Madeshwaran',
    'Voter Card',
    '5678',
    STANDARD_HASH('GOV_ID_MADESH_5678', 'SHA256'),
    HEXTORAW('674141414141427132795545565964326b5048635a486235735672526b337450745555694f6952544f3043665f61434f43316e59395a5a506d594345484f6678412d746a7048735057664d666643614935394461735336396856713669754b737a684b44366d743866385472704e78485035576671797147355074674275674b62495277543935435f65333356634a54502d65486539366b79783474555742774835454f366d354e4c4d59616d583043526f45634d41383d'),
    'N',
    CURRENT_TIMESTAMP
);

-- Voter 3: Ramesh
INSERT INTO VOTER (
    voter_id, name, id_type, id_last4, id_hash,
    fingerprint_template, has_voted, enrolled_at
) VALUES (
    'voter-ramesh-003',
    'Ramesh',
    'Aadhaar',
    '9012',
    STANDARD_HASH('GOV_ID_RAMESH_9012', 'SHA256'),
    HEXTORAW('674141414141427132795545565964326b5048635a486235735672526b337450745555694f6952544f3043665f61434f43316e59395a5a506d594345484f6678412d746a7048735057664d666643614935394461735336396856713669754b737a684b44366d743866385472704e78485035576671797147355074674275674b62495277543935435f65333356634a54502d65486539366b79783474555742774835454f366d354e4c4d59616d583043526f45634d41383d'),
    'N',
    CURRENT_TIMESTAMP
);

-- ----------------------------------------------------------------------------
-- 7. SAVE EVERYTHING
-- ----------------------------------------------------------------------------
COMMIT;

-- ----------------------------------------------------------------------------
-- 8. VERIFICATION QUERIES (Check everything is active)
-- ----------------------------------------------------------------------------
SELECT 'Staff Accounts:' AS title, username, role FROM ADMIN_USER;
SELECT 'Eligible Voters:' AS title, name, has_voted FROM VOTER;
SELECT 'Election State:' AS title, state_key, state_value FROM ELECTION_STATE;
SELECT 'Candidates:' AS title, name, party FROM CANDIDATE;
