-- ============================================================================
-- SecureVote - Insert Eligible Voters into Oracle Database
-- Run this in SQL*Plus or Oracle SQL Developer:
--   sqlplus securevote_app/madesh777@localhost:1521/XEPDB1 @backend\db\insert_sample_voters.sql
-- ============================================================================

-- 1. Insert "Prabhu"
INSERT INTO VOTER (
    voter_id,
    name,
    id_type,
    id_last4,
    id_hash,
    fingerprint_template,
    has_voted,
    enrolled_at
) VALUES (
    'voter-prabhu-001',
    'Prabhu',
    'National ID',
    '1234',
    -- SHA-256 hash for unique ID constraint
    STANDARD_HASH('SECUREVOTE_PRABHU_1234', 'SHA256'),
    -- Valid encrypted mock fingerprint template (BLOB)
    HEXTORAW('674141414141427132795545565964326b5048635a486235735672526b337450745555694f6952544f3043665f61434f43316e59395a5a506d594345484f6678412d746a7048735057664d666643614935394461735336396856713669754b737a684b44366d743866385472704e78485035576671797147355074674275674b62495277543935435f65333356634a54502d65486539366b79783474555742774835454f366d354e4c4d59616d583043526f45634d41383d'),
    'N',
    CURRENT_TIMESTAMP
);

-- 2. Insert "Madeshwaran"
INSERT INTO VOTER (
    voter_id,
    name,
    id_type,
    id_last4,
    id_hash,
    fingerprint_template,
    has_voted,
    enrolled_at
) VALUES (
    'voter-madesh-002',
    'Madeshwaran',
    'Voter ID',
    '5678',
    STANDARD_HASH('SECUREVOTE_MADESH_5678', 'SHA256'),
    HEXTORAW('674141414141427132795545565964326b5048635a486235735672526b337450745555694f6952544f3043665f61434f43316e59395a5a506d594345484f6678412d746a7048735057664d666643614935394461735336396856713669754b737a684b44366d743866385472704e78485035576671797147355074674275674b62495277543935435f65333356634a54502d65486539366b79783474555742774835454f366d354e4c4d59616d583043526f45634d41383d'),
    'N',
    CURRENT_TIMESTAMP
);

-- 3. Commit changes to Oracle DB
COMMIT;

-- ============================================================================
-- Verification Query Test:
-- Run this query to test searching by name (similar to what the portal runs):
-- ============================================================================
SELECT voter_id, name, id_type, id_last4, has_voted, enrolled_at
FROM VOTER
WHERE UPPER(name) = UPPER('Prabhu');
