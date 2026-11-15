import sqlite3
from mcp.server.fastmcp import FastMCP

DB_PATH = "data/resources.db"
mcp = FastMCP("resource-planner")


def query(sql, params=()):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = [dict(row) for row in con.execute(sql, params)]
    con.close()
    return rows


@mcp.tool()
def find_people(skill: str) -> list[dict]:
    """Find people who have a given skill, e.g. 'azure migration', 'expressroute'
    or 'project management'. Returns each person's id, name, role and skills."""
    return query("SELECT id, name, role, skills FROM people WHERE skills LIKE ?",
                 (f"%{skill.lower()}%",))


@mcp.tool()
def check_availability(person_id: str, start_date: str, end_date: str) -> dict:
    """Check how much of a person's time is free between two dates (format YYYY-MM-DD).
    person_id must be an id returned by find_people, e.g. 'P03'.
    Returns percent_available and the commitments that overlap that period."""
    if not query("SELECT id FROM people WHERE id = ?", (person_id,)):
        return {"error": f"Unknown person_id '{person_id}'. Use the id from find_people, e.g. 'P03'."}
    # Simplification: any commitment overlapping the period counts for the whole period.
    commitments = query(
        """SELECT project, start_date, end_date, percent FROM allocations
           WHERE person_id = ? AND start_date <= ? AND end_date >= ?""",
        (person_id, end_date, start_date))
    busy = min(100, sum(c["percent"] for c in commitments))
    return {"person_id": person_id, "percent_available": 100 - busy,
            "overlapping_commitments": commitments}


@mcp.tool()
def list_skills() -> list[str]:
    """List every skill anyone in the team has. Use this to find related or
    adjacent skills when no one has an exact match."""
    rows = query("SELECT skills FROM people")
    return sorted({skill.strip() for row in rows for skill in row["skills"].split(",")})


if __name__ == "__main__":
    mcp.run()