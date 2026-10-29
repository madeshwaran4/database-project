-- ============================================================================
-- SecureVote - Oracle 21c XE Seed Data (002_seed.sql)
-- ============================================================================

-- 1. Initial Election State: 'closed' before polling opens
INSERT INTO ELECTION_STATE (state_key, state_value, updated_at)
VALUES ('polling_status', 'closed', CURRENT_TIMESTAMP);

-- 2. Default Seed Users
-- Passwords:
-- admin / admin123
-- operator / operator123
INSERT INTO ADMIN_USER (admin_id, username, password_hash, role, created_at)
VALUES (
    'admin-root-0001',
    'admin',
    'pbkdf2:sha256:100000$2bdefb884fd5c9ec8369ea4e058a8b08$82580728eed3cd3de23d190283193659149a86511e4c1370c9526d7854c25172',
    'admin',
    CURRENT_TIMESTAMP
);

INSERT INTO ADMIN_USER (admin_id, username, password_hash, role, created_at)
VALUES (
    'operator-booth-0001',
    'operator',
    'pbkdf2:sha256:100000$aa1c7b63a0d700e79064ab2bdc700044$d69fdb386992cf11af6c3e80f83f5f1debf16808b37192bf88573c3007764899',
    'booth-operator',
    CURRENT_TIMESTAMP
);

-- 3. Initial Sample Candidates
INSERT INTO CANDIDATE (candidate_id, name, party, description, created_at)
VALUES (
    'cand-001',
    'Elena Rostova',
    'Democratic Alliance',
    'Focus on transparent governance, renewable infrastructure, and digital privacy.',
    CURRENT_TIMESTAMP
);

INSERT INTO CANDIDATE (candidate_id, name, party, description, created_at)
VALUES (
    'cand-002',
    'Marcus Vance',
    'Forward Progress Coalition',
    'Platform supporting technological innovation, public healthcare expansion, and civic education.',
    CURRENT_TIMESTAMP
);

INSERT INTO CANDIDATE (candidate_id, name, party, description, created_at)
VALUES (
    'cand-003',
    'Amina Chen',
    'Ecological Union',
    'Dedicated to sustainable city planning, clean energy transition, and ethical technology.',
    CURRENT_TIMESTAMP
);

COMMIT;
