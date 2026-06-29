"""Anonymous preference-profile storage: questionnaire answers persisted under a
server-generated UUID. Mirrors the sync SessionLocal pattern used by recommend.py."""
import uuid

from fastapi import APIRouter, Body, HTTPException

from database.models import SessionLocal, Preference_Profile

api_router = APIRouter()


@api_router.post("/api/v1/profile", status_code=201)
def create_profile(body: dict = Body(...)):
    answers = (body or {}).get("answers", {})
    with SessionLocal() as session:
        prof = Preference_Profile(id=str(uuid.uuid4()), answers=answers)
        session.add(prof)
        session.commit()
        return {"id": prof.id, "answers": prof.answers}


@api_router.get("/api/v1/profile/{profile_id}")
def get_profile(profile_id: str):
    with SessionLocal() as session:
        prof = session.get(Preference_Profile, profile_id)
        if prof is None:
            raise HTTPException(status_code=404, detail="profile not found")
        return {"id": prof.id, "answers": prof.answers}


@api_router.put("/api/v1/profile/{profile_id}")
def update_profile(profile_id: str, body: dict = Body(...)):
    answers = (body or {}).get("answers", {})
    with SessionLocal() as session:
        prof = session.get(Preference_Profile, profile_id)
        if prof is None:
            raise HTTPException(status_code=404, detail="profile not found")
        prof.answers = answers          # reassignment (not in-place) so JSON change is tracked
        session.commit()
        return {"id": prof.id, "answers": prof.answers}
