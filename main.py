from fastapi import FastAPI, HTTPException ,Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base



SQLALCHEMY_DATABASE_URL = "sqlite:///./notes.db"    #데이터베이스 설정
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)                                                   #데이터 베이스 연결 엔진 설정
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
app = FastAPI()
Base = declarative_base()   #모델 기본 틀 정의

class NoteDB(Base):         #Base를 상속받아 데이터베이스 모델 정의
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)

Base.metadata.create_all(bind=engine)   #테이블 생성

class NoteCreate(BaseModel):# 요청으로 받을 데이터 형식
    title: str
    content: str

class Note(BaseModel):      # 응답으로 줄 데이터 형식
    id: int
    title: str
    content: str

    class Config:           #SQLAlchemy 객체를 그대로 반환해도 FastAPI가 알아서 JSON으로 변환하게 하는 코드
        from_attributes = True  

def get_db():
    db = SessionLocal()      # 1. 세션 생성
    try:
        yield db             # 2. 세션을 엔드포인트에 넘겨줌
    finally:
        db.close()           # 3. 작업이 끝나면 세션을 닫음

class Question(BaseModel):   #질문 요청 모델
    question: str

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI! 데이터베이스 버전입니다."}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/notes", response_model=Note)    # 노트 생성, 응답: Note 모델
def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    db_note = NoteDB(title=note.title, content=note.content)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

@app.get("/notes", response_model=List[Note])   # 전체 노트 조회
def get_notes(db:Session = Depends(get_db)):
    return db.query(NoteDB).all()

@app.get("/notes/{note_id}", response_model=Note)   # 특정 노트 조회
def get_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(NoteDB).filter(NoteDB.id == note_id).first()
    if note is None:
        raise HTTPException(status_code=404, detail="노트를 찾을 수 없습니다")
    return note

@app.put("/notes/{note_id}", response_model=Note)   #노트 수정
def update_note(note_id: int, updated_note: NoteCreate, db: Session = Depends(get_db)):
    note = db.query(NoteDB).filter(NoteDB.id == note_id).first()
    if note is None:
            raise HTTPException(status_code=404, detail="노트를 찾을 수 없습니다")
    note.title = updated_note.title
    note.content = updated_note.content
    db.commit()
    db.refresh(note)
    return note

@app.delete("/notes/{note_id}")                     #노트 삭제
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(NoteDB).filter(NoteDB.id == note_id).first()
    if note is None:
        raise HTTPException(status_code=404, detail="노트를 찾을 수 없습니다")
    db.delete(note)
    db.commit()
    return {"message": "노트가 삭제되었습니다"}

@app.post("/ask")    #ai 응답
def ask_question(q: Question, db: Session = Depends(get_db)):
    notes = db.query(NoteDB).all()  #저장된 노트를 전부 불러온다
    context = "\n".join([f"제목: {n.title}\n내용: {n.content}"for n in notes])  #노트의 내용을 하나의 문자열로 합치기
    fake_answer = f"질문: {q.question} \n\n관련 노트 요약: {context[:500]}..."
    return {
        "question": q.question,
        "answer": fake_answer,
        "note_count": len(notes)
    }