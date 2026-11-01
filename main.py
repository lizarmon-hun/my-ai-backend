from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

notes_db: List[dict] = []   # 메모리에 노트를 저장할 리스트
note_id_counter = 1         

class NoteCreate(BaseModel):# 요청으로 받을 데이터 형식
    title: str
    content: str

class Note(BaseModel):      # 응답으로 줄 데이터 형식
    id: int
    title: str
    content: str

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI! 서버가 정상적으로 실행됐어요."}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/notes", response_model=Note)    # 노트 생성, 응답: Note 모델
def create_note(note: NoteCreate):
    global note_id_counter
    new_note = {
        "id": note_id_counter,
        "title": note.title,
        "content": note.content
    }
    notes_db.append(new_note)
    note_id_counter += 1
    return new_note