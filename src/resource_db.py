import sqlite3
from pathlib import Path

DB_PATH = Path("data/resources.db")

# Fictional people for testing. Skills are comma-separated, lower case.
PEOPLE = [
    ("P01", "Asha Verma", "Cloud Architect", "azure architecture, azure landing zone, azure migration, aws architecture"),
    ("P02", "Rohan Mehta", "Cloud Architect", "aws architecture, azure architecture, cost management"),
    ("P03", "Neha Kapoor", "Migration Engineer", "azure migration, vmware, azure vmware solution"),
    ("P04", "Arjun Rao", "Migration Engineer", "azure migration, windows server, sql server"),
    ("P05", "Kiran Joshi", "Network Engineer", "azure networking, expressroute, vwan, palo alto"),
    ("P06", "Meera Iyer", "DR Specialist", "disaster recovery, commvault, azure site recovery"),
    ("P07", "Vikram Singh", "End-User Computing Engineer", "azure virtual desktop, vdi, intune"),
    ("P08", "Sana Qureshi", "Project Manager", "project management, pmp, itil"),
    ("P09", "Dev Malhotra", "Security Consultant", "security compliance, pci, hipaa, cjis"),
    ("P10", "Tara Nair", "Monitoring Engineer", "azure monitor, observability, cost management"),
]

# Current commitments: (person, project, start, end, percent of their time)
ALLOCATIONS = [
    ("P01", "Retail data platform", "2026-10-01", "2027-02-28", 50),
    ("P02", "Bank AWS migration", "2026-09-01", "2027-06-30", 100),
    ("P03", "Hospital VMware exit", "2026-11-01", "2027-01-31", 100),
    ("P05", "Telecom network refresh", "2026-12-01", "2027-03-31", 50),
    ("P06", "Insurer DR programme", "2026-08-01", "2027-03-31", 100),
    ("P07", "University VDI rollout", "2026-10-01", "2027-12-31", 80),
    ("P09", "Health records audit", "2027-01-01", "2027-02-28", 50),
]


def build():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = sqlite3.connect(DB_PATH)
    con.executescript("""
        CREATE TABLE people (id TEXT PRIMARY KEY, name TEXT, role TEXT, skills TEXT);
        CREATE TABLE allocations (person_id TEXT, project TEXT,
                                  start_date TEXT, end_date TEXT, percent INTEGER);
    """)
    con.executemany("INSERT INTO people VALUES (?, ?, ?, ?)", PEOPLE)
    con.executemany("INSERT INTO allocations VALUES (?, ?, ?, ?, ?)", ALLOCATIONS)
    con.commit()
    con.close()


if __name__ == "__main__":
    build()
    print(f"Built {DB_PATH} with {len(PEOPLE)} people and {len(ALLOCATIONS)} allocations.")