# System Limitations & Threat Analysis

While SecureVote implements robust cryptographic controls, biometric deduplication, and zero-link ballot isolation, any real-world electronic election platform must account for foundational sociotechnical and operational limitations.

---

## 1. Enrollment Operator Trust & Inception Attacks

### Description
The security of biometric deduplication relies fundamentally on the integrity of the enrollment event. If the human operator at the enrollment station is malicious or coerced, they could:
- Associate a real citizen's national ID with an attacker's biometric fingerprint template.
- Enroll nonexistent "phantom" citizens using counterfeit documents.

### Architectural Mitigations & Residual Risk
* **Mitigation**: SecureVote logs every enrollment attempt and mandates cryptographic role-based tokens. In a national deployment, enrollment should require **dual-custody signing** (two operators independently verifying physical government credentials).
* **Residual Risk**: A compromised enrollment official acting alone remains a primary threat vector unless physical counter-verification audits are enforced.

---

## 2. Prototype Hardware & Environmental Biometric Variations

### Description
Optical, capacitive, and ultrasonic fingerprint sensors have variable performance characteristics influenced by:
- **Skin Condition**: Extreme dryness, manual labor abrasions, humidity, and skin elasticity can lower minutiae match scores (False Rejection Rate - FRR).
- **Presentation Attacks (Spoofing)**: Commercial optical scanners without active liveness detection (pulse oximetry, subdermal dermal scanning) are vulnerable to gelatin or latex spoof molds.

### Architectural Mitigations & Residual Risk
* **Mitigation**: SecureVote features an abstract `FingerprintProvider` interface allowing seamless transition to certified FBI PIV / FIPS 201 compliant scanners with hardware liveness detection.
* **Residual Risk**: High False Rejection Rates (FRR) at polling stations can disenfranchise elderly citizens or manual laborers, requiring fallback administrative affidavit procedures.

---

## 3. Insider Database Access & Side-Channel Timing

### Description
If an adversary obtains direct, privileged root access to the database server (e.g., DBA with `sysdba` privileges):
- They cannot retroactively link a vote to a voter through foreign keys, because none exist.
- However, if the database transaction log (Oracle redo/undo logs or WAL) records the physical block commit order of the `UPDATE VOTER` and `INSERT VOTE` statements during low-turnout periods, the sequence of transactions might allow correlation.

### Architectural Mitigations & Residual Risk
* **Mitigation**: SecureVote stores only coarse calendar dates (`vote_date DATE`) with zero time components and uses non-sequential UUIDv4 primary keys.
* **Residual Risk**: Redo log inspection by an adversary with continuous OS/storage level memory dumps during single-voter polling intervals could correlate operations. In high-security jurisdictions, transactions should be pooled in an asynchronous shuffle queue or batched.

---

## 4. Legal & Regulatory Status of Biometric Voting

### Description
* **Voter Secrecy Constitutional Protections**: Most democratic constitutions explicitly mandate universal, secret, and direct suffrage. Storing biometric templates in relation to voting systems faces stringent scrutiny under data protection laws (e.g., EU GDPR Article 9 special category biometric data, Kenya Supreme Court rulings on biometric register fallbacks).
* **Mandatory Fallback Laws**: Almost all legal frameworks require paper-trail audits (Voter Verified Paper Audit Trail - VVPAT). A purely digital system without a paper receipt is legally impermissible in jurisdictions such as Germany, India, and various US states.

### Architectural Recommendation
SecureVote is designed to serve as the **digital deduplication and check-in authority**. At the voting kiosk, the vote transaction can be paired with an isolated VVPAT printer producing a physical paper ballot deposited into a traditional ballot box.
