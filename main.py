from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from db import conn
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#for posting
class observationCreate(BaseModel):
    user_id : int
    species_id : int
    research_content : str
    latitude: float
    longitude: float

#for commenting
class commentCreate(BaseModel):
    obs_id : int
    user_id : int
    comments: str
    parent_id : Optional[int] = None # Allows null for top-level comments

class SpeciesCreate(BaseModel):
    genus_name: str
    species_name: str
    user_id: int

def fetch_observations(species_id=None, user_id = None, limit=10):
    curr = conn.cursor() # executes queries
    query = """
    select u.user_id, s.genus_name, s.species_name, o.research_content, o.latitude, o.longitude, o.observed_at
    from observation o
    join users u on u.user_id = o.user_id
    join species s on s.species_id = o.species_id
    where 1=1
    """

    param = []

    if species_id is not None:
        query += " and o.species_id = %s" # o.species because we usef from observation
        param.append(species_id)
    if user_id is not None:
        query += " and o.user_id = %s"
        param.append(user_id)
    query += " LIMIT %s"
    param.append(limit)

    try:
        curr.execute(query,param)
        rows = curr.fetchall()
        return rows
    except Exception as e:
        conn.rollback()
        print("DB ERROR", e)
        return []
    finally:
        curr.close()




@app.get("/observations")

def get_observations (species_id: int = None, user_id: int = None):
    
    rows = fetch_observations(species_id=species_id, user_id=user_id)

    #convert to json file

    data = []

    for row in rows:
        obs = {
           "user_id" : row[0],
           "species" : {
               "genus" : row[1],
               "species" : row[2]
           },
           "research_content" : row[3],
           "location" : {
               "latitude" : row[4],
               "longitude" : row[5]
           },
           "observed_at" : str(row[6]) 
        }

        data.append(obs)

    return {
        "status" : "success",
        "count" : len(data),
        "data" : data
    }

@app.post("/observations")
def create_observation(obs: observationCreate):
    curr = conn.cursor()

    query = """
    INSERT INTO observation 
    (user_id, species_id, research_content, latitude, longitude, observed_at)
    VALUES (%s, %s, %s, %s, %s, NOW())
    RETURNING observation_id;
    """

    values = (
        obs.user_id,
        obs.species_id,
        obs.research_content,
        obs.latitude,
        obs.longitude,
    )

    curr.execute(query, values)
    new_id = curr.fetchone()[0]

    conn.commit()
    curr.close()

    return {
        "status" : "success",
        "message" : "observation created",
        "observation_id" : new_id
    }


@app.post("/comments")

def create_comment(c : commentCreate):
    curr = conn.cursor()

    query = """
    insert into forum
    (obs_id, user_id, comments, parent_id)
    values(%s, %s, %s, %s)
    returning post_id
    """

    
    values = (
        c.obs_id,
        c.user_id,
        c.comments,
        c.parent_id
    )

    try:
        curr.execute(query, values)
        new_id = curr.fetchone()[0]

        conn.commit()
        curr.close()

        return {
            "status" : "success",
            "post_id" : new_id
    }

    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    
    finally:
        curr.close()
#copied
def build_comment_tree(comments):

    comment_map = {}

    # create node map
    for c in comments:
        comment_map[c["post_id"]] = {
            "post_id": c["post_id"],
            "user_id": c["user_id"],
            "username": c["username"],
            "comments": c["comments"],
            "parent_id": c["parent_id"],
            "replies": []
        }

    root = []

    # attach children to parents
    for c in comment_map.values():

        if c["parent_id"] is None:
            root.append(c)
        else:
            parent = comment_map.get(c["parent_id"])
            if parent:
                parent["replies"].append(c)

    return root


#get commets
@app.get("/comments")
def get_comments(obs_id: int):

    curr = conn.cursor()

    query = """
    SELECT 
        f.post_id,
        f.user_id,
        u.username,
        f.comments,
        f.parent_id
    FROM forum f
    JOIN users u ON u.user_id = f.user_id
    WHERE f.obs_id = %s
    ORDER BY f.post_id;
    """

    curr.execute(query, (obs_id,))
    rows = curr.fetchall()
    curr.close()

    comments = []

    for row in rows:
        comments.append({
            "post_id": row[0],
            "user_id": row[1],
            "username": row[2],
            "comments": row[3],
            "parent_id": row[4]
        })

    nested = build_comment_tree(comments)

    return {
        "status": "success",
        "obs_id": obs_id,
        "count": len(comments),
        "data": nested
    }

#users
@app.get("/users")
def get_users():
    curr = conn.cursor()

    query = """
    SELECT user_id, username, expertise_level, role
    FROM users;
    """

    curr.execute(query)
    rows = curr.fetchall()
    curr.close()

    data = []

    for row in rows:
        data.append({
            "user_id": row[0],
            "username": row[1],
            "expertise_level": row[2],
            "role": row[3]
        })

    return {
        "status": "success",
        "data": data
    }

#species
@app.get("/species")
def get_species():

    cur = conn.cursor()

    query = """
    SELECT
        s.species_id,
        s.genus_name,
        s.species_name,
        scn.common_name
    FROM species s
    LEFT JOIN species_common_names scn
        ON s.species_id = scn.species_id
    ORDER BY s.species_id;
    """

    cur.execute(query)
    rows = cur.fetchall()
    cur.close()

    species_map = {}

    for row in rows:

        sid = row[0]

        if sid not in species_map:
            species_map[sid] = {
                "species_id": sid,
                "genus": row[1],
                "species": row[2],
                "common_names": []
            }

        # add common name if exists
        if row[3]:
            species_map[sid]["common_names"].append(row[3])

    return {
        "status": "success",
        "data": list(species_map.values())
    }

@app.post("/species")
def create_species(s: SpeciesCreate):

    cur = conn.cursor()

    
    cur.execute("""
        SELECT role
        FROM users
        WHERE user_id = %s
    """, (s.user_id,))

    user = cur.fetchone()

    if not user:
        cur.close()
        return {
            "status": "error",
            "message": "User not found"
        }

    role = user[0]

    if role != "researcher":
        cur.close()
        return {
            "status": "error",
            "message": "Only researchers can add species"
        }

    
    query = """
    insert into species (genus_name, species_name, created_by)
    values (%s, %s, %s)
    RETURNING species_id;
    """

    values = (s.genus_name, s.species_name, s.user_id)

    try:
        cur.execute(query, values)
        new_id = cur.fetchone()[0]
        conn.commit()

        return {
            "status": "success",
            "species_id": new_id
        }

    except Exception as e:
        conn.rollback()
        return {
            "status": "error",
            "message": str(e)
        }

    finally:
        cur.close()