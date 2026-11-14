from fastapi import FastAPI, HTTPException ,Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import requests
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./notes.db"    #데이터베이스 설정
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)                                                   #데이터 베이스 연결 엔진 설정
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
app = FastAPI()
Base = declarative_base()   #모델 기본 틀 정의

app.mount("/static", StaticFiles(directory="static"), name="static")

class NoteDB(Base):         #Base를 상속받아 데이터베이스 모델 정의
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)

class QARecord(Base):
    __tablename__ = "qa_records"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String)
    answer = Column(String)
    created_at = Column(String)  # 간단하게 문자열로 저장

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

@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/ask-page", response_class=HTMLResponse)
def ask_page():
    with open("templates/ask.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/notes-page", response_class=HTMLResponse)
def notes_page():
    with open("templates/notes.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/history", response_class=HTMLResponse)
def history_page():
    with open("templates/history.html", "r", encoding="utf-8") as f:
        return f.read()

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

    if len(context) > 2000:
        context = context[:2000] + "..."    #컨텍스트가 너무 길면 자르기

    prompt = f"""당신은 사용자의 개인 노트를 기반으로 정확하게 답변하는 도우미입니다.
아래 규칙을 반드시 지켜주세요:
- 오직 제공된 노트 내용만을 바탕으로 답변하세요.
- 노트에 없는 내용은 추측하지 마세요.
- 관련 내용이 없으면 "노트에서 관련 정보를 찾을 수 없습니다"라고 답하세요.
- 답변은 간결하고 명확하게 한국어로 작성하세요.

노트 내용:
{context}

질문: {q.question}

답변:"""

    # Ollama API 호출
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5:latest",  # 다운로드한 모델 이름으로 바꾸세요
            "prompt": prompt,
            "stream": False
        }
    )

    if response.status_code == 200:
        answer = response.json().get("response", "응답을 생성하지 못했습니다.")
    else:
        answer = "Ollama 연결에 실패했습니다. Ollama가 실행 중인지 확인하세요."

    # 기록 저장
    record = QARecord(
        question=q.question,
        answer=answer,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.add(record)
    db.commit()

    return {
        "question": q.question,
        "answer": answer,
        "note_count": len(notes)
    }

@app.get("/qa-records")
def get_qa_records(db: Session = Depends(get_db)):
    records = db.query(QARecord).order_by(QARecord.id.desc()).all()
    return [
        {
            "id": r.id,
            "question": r.question,
            "answer": r.answer,
            "created_at": r.created_at
        }
        for r in records
    ]