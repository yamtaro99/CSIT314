import os
import random
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from werkzeug.security import generate_password_hash

from app import create_app
from app.db import get_db, init_db

SEED_PASSWORD = "Password123!"
RNG = random.Random(314)

FIRST = ["Aisha", "Ben", "Chloe", "Daniel", "Elaine", "Farhan", "Grace", "Hui Min", "Ivan", "Jia Hui",
         "Kumar", "Li Wei", "Mei Ling", "Nur", "Owen", "Priya", "Qi Xuan", "Rachel", "Siti", "Tan",
         "Umar", "Vanessa", "Wei Jie", "Xin Yi", "Yusuf", "Zoe"]
LAST = ["Tan", "Lim", "Lee", "Ng", "Wong", "Goh", "Chua", "Ong", "Koh", "Teo", "Rahman", "Singh",
        "Kumar", "Ismail", "Chen", "Ho", "Yeo", "Low"]
STUDIOS = ["Studio", "Interiors", "Design Co", "Atelier", "Living", "Spaces", "Concepts", "Workshop"]
STUDIO_WORDS = ["Oak", "Linen", "Haven", "Nest", "Canvas", "Ember", "Mosaic", "Prism", "Sage",
                "Terra", "Willow", "Arc", "Loft", "Grain", "Harbour", "Juniper"]
CATEGORIES = ["Modern", "Minimalist", "Scandinavian", "Industrial", "Japandi", "Contemporary",
              "Classic", "Tropical", "Mid-century", "Luxury", "HDB 3-room", "HDB 4-room",
              "HDB 5-room", "Condominium", "Landed", "Commercial", "Kitchen", "Bathroom"]
LOCATIONS = ["Tampines", "Punggol", "Sengkang", "Jurong West", "Woodlands", "Bishan", "Toa Payoh",
             "Clementi", "Bedok", "Ang Mo Kio", "Queenstown", "Bukit Timah", "Novena", "Pasir Ris",
             "Yishun", "Hougang", "Serangoon", "Marine Parade", "Bukit Batok", "Choa Chu Kang"]
ROOMS = ["Living Room", "Kitchen", "Master Bedroom", "Whole Home", "Bathroom", "Study", "Family Home"]
ADJECTIVES = ["Warm", "Airy", "Bright", "Cosy", "Elegant", "Bold", "Calm", "Earthy", "Sleek", "Timeless"]


def rand_dt(days_back):
    return (datetime.now() - timedelta(days=RNG.randint(0, days_back),
                                       minutes=RNG.randint(0, 1439))).isoformat(timespec="seconds")


def person():
    return f"{RNG.choice(FIRST)} {RNG.choice(LAST)}"


def seed_accounts(conn, pw_hash):
    rows = [("admin@ideal.test", pw_hash, "System Admin", "user_admin", "active", rand_dt(400))]
    rows += [(f"pm{i}@ideal.test", pw_hash, f"Platform Manager {i}", "platform_manager", "active", rand_dt(400))
             for i in range(1, 6)]
    for i in range(1, 101):
        studio = f"{RNG.choice(STUDIO_WORDS)} {RNG.choice(STUDIOS)}"
        status = "pending" if i > 90 else "active"
        rows.append((f"designer{i:03d}@ideal.test", pw_hash, studio, "interior_designer", status, rand_dt(365)))
    for i in range(1, 101):
        status = "suspended" if i % 25 == 0 else "active"
        rows.append((f"customer{i:03d}@ideal.test", pw_hash, person(), "customer", status, rand_dt(365)))
    conn.executemany(
        "INSERT INTO user_account (email, password_hash, name, role, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )


def seed_categories(conn):
    conn.executemany(
        "INSERT INTO category (name, is_active, created_at) VALUES (?, ?, ?)",
        [(name, 0 if name == "Commercial" else 1, rand_dt(500)) for name in CATEGORIES],
    )


def seed_projects(conn):
    designer_ids = [r[0] for r in conn.execute(
        "SELECT user_id FROM user_account WHERE role = 'interior_designer' AND status = 'active'")]
    category_ids = [r[0] for r in conn.execute("SELECT category_id FROM category WHERE is_active = 1")]
    today = date.today()
    for designer_id in designer_ids:
        for _ in range(RNG.randint(1, 4)):
            room = RNG.choice(ROOMS)
            location = RNG.choice(LOCATIONS)
            title = f"{RNG.choice(ADJECTIVES)} {room} in {location}"
            description = (f"A {RNG.choice(ADJECTIVES).lower()} {room.lower()} renovation for a "
                           f"{RNG.choice(['young couple', 'family of four', 'retiree', 'working professional'])}. "
                           f"Budget around ${RNG.randrange(15, 150) * 1000:,}.")
            completion = today + timedelta(days=RNG.randint(-900, 120))
            created = rand_dt(400)
            status = "removed" if RNG.random() < 0.05 else "active"
            cur = conn.execute(
                "INSERT INTO project (designer_id, title, description, location, completion_date,"
                " status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (designer_id, title, description, location, completion.isoformat(), status, created, created),
            )
            for category_id in RNG.sample(category_ids, RNG.randint(1, 3)):
                conn.execute("INSERT INTO project_category (project_id, category_id) VALUES (?, ?)",
                             (cur.lastrowid, category_id))


def seed_companies(conn):
    designers = conn.execute(
        "SELECT user_id FROM user_account WHERE role = 'interior_designer'").fetchall()
    rows = [
        (d["user_id"], f"UEN{d['user_id']:06d}A",
         f"{RNG.randint(1, 200)} {RNG.choice(LOCATIONS)} Road",
         f"6{RNG.randint(1000000, 9999999)}",
         RNG.choice(["Residential interior design", "Commercial fit-out specialists",
                     "Renovation and space planning"]))
        for d in designers
    ]
    conn.executemany(
        "INSERT INTO company (designer_id, registration_no, address, phone, description)"
        " VALUES (?, ?, ?, ?, ?)", rows)


def main():
    app = create_app()
    with app.app_context():
        init_db()
        conn = get_db()
        pw_hash = generate_password_hash(SEED_PASSWORD)
        seed_accounts(conn, pw_hash)
        seed_companies(conn)
        seed_categories(conn)
        seed_projects(conn)
        conn.commit()

        for table in ("user_account", "category", "project", "project_category"):
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table:20} {count}")
        print(f"\nAll accounts use password: {SEED_PASSWORD}")


if __name__ == "__main__":
    main()
