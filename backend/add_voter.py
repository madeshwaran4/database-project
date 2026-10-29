r"""
Interactive / CLI script to add eligible voters directly into the Oracle Database.
Works with the SecureVote application.

Usage:
  cd backend
  .venv\Scripts\python.exe add_voter.py --name "Prabhu" --id "12345678"
  (or simply run without arguments for interactive prompt)
"""
import sys
import uuid
import argparse
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import oracledb
from app.core.config import settings
from app.core.security import hash_id
from app.fingerprint import get_fingerprint_provider, biometric_cipher


def add_voter(name: str, id_number: str = "12345678", id_type: str = "Voter Card"):
    print("=" * 60)
    print(f"Adding Voter: '{name}' to Oracle Database ({settings.ORACLE_SERVICE_NAME})")
    print("=" * 60)

    try:
        conn = oracledb.connect(
            user=settings.ORACLE_USER,
            password=settings.ORACLE_PASSWORD,
            host=settings.ORACLE_HOST,
            port=settings.ORACLE_PORT,
            service_name=settings.ORACLE_SERVICE_NAME,
        )
        print(f"[+] Connected to Oracle DB as {settings.ORACLE_USER}")
    except Exception as e:
        print(f"[!] Oracle connection failed: {e}")
        print("    Ensure Oracle Service is running and credentials in .env are correct.")
        return False

    cursor = conn.cursor()

    # 1. Compute ID hash and last 4 digits
    id_last4, id_hash = hash_id(id_number)

    # 2. Check for duplicate ID
    cursor.execute("SELECT voter_id, name FROM VOTER WHERE id_hash = :1", (id_hash,))
    existing = cursor.fetchone()
    if existing:
        print(f"[!] Warning: ID hash already exists under voter '{existing[1]}' (voter_id: {existing[0]})")
        conn.close()
        return False

    # 3. Generate mock biometric template & encrypt it
    provider = get_fingerprint_provider()
    raw_sample = provider.capture()
    minutiae = provider.extract_template(raw_sample)
    encrypted_template = biometric_cipher.encrypt_template(minutiae)

    voter_id = str(uuid.uuid4())

    # 4. Insert into Oracle VOTER table
    try:
        cursor.execute(
            """
            INSERT INTO VOTER (
                voter_id, name, id_type, id_last4, id_hash,
                fingerprint_template, has_voted, enrolled_at
            ) VALUES (:1, :2, :3, :4, :5, :6, 'N', CURRENT_TIMESTAMP)
            """,
            (voter_id, name.strip(), id_type.strip(), id_last4, id_hash, encrypted_template),
        )
        conn.commit()
        print(f"[SUCCESS] Voter '{name}' has been added to Oracle!")
        print(f"    Voter ID:    {voter_id}")
        print(f"    Status:      Ready to Vote (has_voted = 'N')")
        print(f"    Masked ID:   •••• {id_last4}")
        print()
        print("Now in the voting portal / booth:")
        print(f"  - Search for '{name}' -> Access GRANTED.")
        print("  - Search for any name NOT in Oracle -> 'User not found' / Denied.")
        return True
    except Exception as e:
        print(f"[!] Failed to insert voter: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Add voter to Oracle DB")
    parser.add_argument("--name", type=str, help="Full name of voter (e.g. Prabhu)")
    parser.add_argument("--id", type=str, default=None, help="Government/Voter ID number")
    parser.add_argument("--type", type=str, default="National ID", help="ID document type")

    args = parser.parse_args()

    name = args.name
    id_num = args.id

    if not name:
        name = input("Enter Voter Name (e.g. Prabhu): ").strip()
        if not name:
            print("Name cannot be empty.")
            return

    if not id_num:
        default_id = f"VOTER{uuid.uuid4().hex[:6].upper()}"
        id_input = input(f"Enter ID number [default: {default_id}]: ").strip()
        id_num = id_input if id_input else default_id

    add_voter(name=name, id_number=id_num, id_type=args.type)


if __name__ == "__main__":
    main()
