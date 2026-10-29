r"""
Quick tool to view all registered voters in the local Oracle Database.
Usage:
    cd backend
    .venv\Scripts\python.exe view_voters.py
"""
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import oracledb
from app.core.config import settings


def main():
    print("=" * 75)
    print("           SECUREVOTE - REGISTERED VOTER LIST (ORACLE DATABASE)")
    print(f"  Connected to: {settings.ORACLE_USER}@{settings.ORACLE_HOST}:{settings.ORACLE_PORT}/{settings.ORACLE_SERVICE_NAME}")
    print("=" * 75)

    try:
        conn = oracledb.connect(
            user=settings.ORACLE_USER,
            password=settings.ORACLE_PASSWORD,
            host=settings.ORACLE_HOST,
            port=settings.ORACLE_PORT,
            service_name=settings.ORACLE_SERVICE_NAME,
        )
    except Exception as e:
        print(f"[!] Database connection error: {e}")
        return

    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, id_type, id_last4, has_voted, TO_CHAR(enrolled_at, 'YYYY-MM-DD HH24:MI') as enrolled, voter_id
        FROM VOTER
        ORDER BY enrolled_at DESC
    """)
    rows = cursor.fetchall()

    if not rows:
        print("  No voters found in database.")
    else:
        print(f"  Total Voters: {len(rows)}\n")
        header = f"  {'NAME':<20} | {'ID TYPE':<15} | {'LAST 4':<8} | {'VOTED':<6} | {'ENROLLED AT':<16}"
        print(header)
        print("  " + "-" * (len(header) - 2))

        for r in rows:
            name, id_type, last4, has_voted, enrolled, _ = r
            status = "YES (Y)" if has_voted == "Y" else "NO (N)"
            print(f"  {name:<20} | {id_type:<15} | •••• {last4:<3} | {status:<6} | {enrolled:<16}")

    print("=" * 75)
    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
