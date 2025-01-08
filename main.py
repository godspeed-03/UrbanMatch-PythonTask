from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from typing import List
import models, schemas
import uuid

app = FastAPI()

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@app.get("/")
async def root():
    return {"message": "Hello World"}        

@app.post("/users/", response_model=schemas.UserCreate)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if not user.name or not user.age or not user.gender or not user.email or not user.city or not user.interests:
        raise HTTPException(status_code=400, detail="All fields are required")
    
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already in use")
    
    db_user = models.User(
        name=user.name,
        age=user.age,
        gender=user.gender,
        email=user.email,
        city=user.city,
        interests=user.interests,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()

    if not users:
        raise HTTPException(status_code=404, detail="No users found")

    return users

@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    for key, value in user.dict(exclude_unset=True).items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.delete("/users/{user_id}", response_model=schemas.User)
def delete_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return user


@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: uuid.UUID, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.name is not None:
        db_user.name = user.name
    if user.age is not None:
        db_user.age = user.age
    if user.gender is not None:
        db_user.gender = user.gender
    if user.email is not None:
        db_user.email = user.email
    if user.city is not None:
        db_user.city = user.city
    if user.interests is not None:
        db_user.interests = user.interests

    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/users/matches", response_model=List[schemas.User])
def find_matches(match_criteria: schemas.MatchRequest, db: Session = Depends(get_db)):
    query = db.query(models.User)

    if match_criteria.gender:
        query = query.filter(models.User.gender.ilike(match_criteria.gender))
    if match_criteria.city:
        query = query.filter(models.User.city.ilike(match_criteria.city))
    if match_criteria.interests:
        query = query.filter(models.User.interests.any(
            [interest.lower() for interest in match_criteria.interests]))  # Example for matching interests in a case-insensitive manner

    matched_users = query.all()

    return matched_users
