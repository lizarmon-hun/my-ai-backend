# 내 노트 기반 AI 질의응답

개인 노트를 저장하고, 저장된 노트 내용을 바탕으로 AI에게 질문할 수 있는 웹 애플리케이션입니다.

## 주요 기능
- 노트 생성 / 조회 / 수정(인라인) / 삭제
- 저장된 노트를 컨텍스트로 활용한 AI 질의응답
- 간단한 웹 인터페이스 제공

## 기술 스택
- **Backend**: FastAPI, SQLAlchemy, SQLite
- **AI**: Ollama (로컬 LLM)
- **Frontend**: HTML, CSS, JavaScript

## 실행 방법

### 1. 저장소 클론
```bash
git clone https://github.com/lizarmon-hun/my-ai-backend.git
cd my-ai-backend
```

### 2. 가상환경 생성 및 패키지 설치
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Ollama 설치 및 모델 다운로드
1. [Ollama 공식 사이트](https://ollama.com)에서 설치
2. 모델 다운로드 (예시)
```bash
ollama pull qwen2.5:7b
```

### 4. 서버 실행
```bash
uvicorn main:app --reload
```

### 5. 접속
브라우저에서 [http://127.0.0.1:8000](http://127.0.0.1:8000) 접속

## 프로젝트 구조
```
.
├── main.py
├── templates/
│   ├── index.html
│   ├── notes.html
│   └── ask.html
├── static/
│   └── style.css
├── requirements.txt
└── README.md
```

## 참고 사항
- `notes.db` 파일은 `.gitignore`에 포함되어 있어 저장소에 올라가지 않습니다.
- AI 질문 기능을 사용하려면 Ollama가 실행 중이어야 합니다.
- 프롬프트에서 한국어로 답변하도록 지시하고 있습니다.
