# web_main.py - FastAPI verzija sa učitavanjem pitanja iz fajlova

import json
import logging
import os
import random
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from typing import List, Dict

# ========== KONFIGURACIJA ==========
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# ========== FASTAPI APP ==========
app = FastAPI()

# ========== STATIČKI FAJLOVI ==========
# Serviraj index.html i druge fajlove iz trenutnog foldera
app.mount("/", StaticFiles(directory=".", html=True), name="static")

# ========== GLOBALNO STANJE ==========
teams: List[Dict] = []
active_connections: List[WebSocket] = []
quiz_active = False
current_language = 'srpski'
all_questions = []
current_questions = []
current_question_index = 0
questions = []  # Za backward compatibility

# ========== FUNKCIJE ZA UCITAVANJE PITANJA ==========
def load_questions_by_language(lang):
    """Učitava pitanja na osnovu jezika"""
    if lang == 'srpski':
        pitanja_path = "pitanja.txt"
        odgovori_path = "odgovori.txt"
    else:  # engleski
        pitanja_path = "pitanja1.txt"
        odgovori_path = "odgovori1.txt"
    
    return load_questions_from_files(pitanja_path, odgovori_path)

def load_questions_from_files(pitanja_path, odgovori_path):
    """Učitava pitanja iz fajlova"""
    questions_list = []
    
    # Proveri da li fajlovi postoje
    if not os.path.exists(pitanja_path):
        LOGGER.warning(f"Fajl {pitanja_path} nije pronađen, koristim default pitanja")
        return get_default_questions()
    
    try:
        # Učitaj pitanja
        with open(pitanja_path, "r", encoding="utf-8") as f:
            content = f.read()
            question_blocks = content.strip().split("\n\n")
            
            for block in question_blocks:
                lines = [line.strip() for line in block.split("\n") if line.strip()]
                if len(lines) >= 5:
                    # Prva linija je pitanje
                    question_line = lines[0]
                    # Ukloni broj (npr. "1) " ili "1. ")
                    if ') ' in question_line:
                        question_text = question_line.split(') ', 1)[1]
                    elif '. ' in question_line:
                        question_text = question_line.split('. ', 1)[1]
                    else:
                        question_text = question_line
                    
                    # Opcije (linije 2-5)
                    options = []
                    for i in range(1, 5):
                        if i < len(lines):
                            option_line = lines[i]
                            if ') ' in option_line:
                                option_text = option_line.split(') ', 1)[1]
                            elif '. ' in option_line:
                                option_text = option_line.split('. ', 1)[1]
                            else:
                                option_text = option_line[2:].strip() if len(option_line) > 2 else option_line
                            options.append(option_text)
                        else:
                            options.append("")
                    
                    questions_list.append({
                        'question': question_text,
                        'options': options,
                        'correct': 0,  # Default, kasnije ćemo učitati tačne
                        'hint': "Hint nije dostupan."
                    })
        
        # Učitaj tačne odgovore
        if os.path.exists(odgovori_path):
            with open(odgovori_path, "r", encoding="utf-8") as f:
                content = f.read()
                answer_blocks = content.strip().split("\n\n")
                
                for block in answer_blocks:
                    lines = [line.strip() for line in block.split("\n") if line.strip()]
                    if len(lines) >= 5:
                        # Prva linija je pitanje
                        question_line = lines[0]
                        if ') ' in question_line:
                            question_text = question_line.split(') ', 1)[1]
                        elif '. ' in question_line:
                            question_text = question_line.split('. ', 1)[1]
                        else:
                            question_text = question_line
                        
                        # Traži tačan odgovor
                        for i in range(1, 5):
                            if i < len(lines):
                                option_line = lines[i]
                                if "Tacno" in option_line or "tacno" in option_line.lower():
                                    for q in questions_list:
                                        if q['question'] == question_text:
                                            q['correct'] = i - 1
                                            # Ukloni "Tačno" iz opcije
                                            if 'Tacno' in q['options'][i-1]:
                                                q['options'][i-1] = q['options'][i-1].replace('Tacno', '').strip()
                                            break
                                    break
        
        # Ako nijedno pitanje nema tačan odgovor, nasumično dodeli
        for q in questions_list:
            if q['correct'] not in [0, 1, 2, 3]:
                q['correct'] = random.randint(0, 3)
        
        LOGGER.info(f"Učitano {len(questions_list)} pitanja iz {pitanja_path}")
        return questions_list
    
    except Exception as e:
        LOGGER.error(f"Greška pri učitavanju pitanja: {e}")
        return get_default_questions()

def get_default_questions():
    """Default pitanja ako fajlovi ne postoje"""
    return [
        {'question': 'Koji je glavni grad Srbije?', 'options': ['Niš', 'Novi Sad', 'Beograd', 'Priština'], 'correct': 2},
        {'question': 'Koja je najduža reka u Evropi?', 'options': ['Dunav', 'Volga', 'Rajna', 'Temza'], 'correct': 1},
        {'question': 'Koji je hemijski simbol za vodu?', 'options': ['H2O', 'CO2', 'NaCl', 'HCl'], 'correct': 0},
        {'question': 'Koja je najveća planeta u Sunčevom sistemu?', 'options': ['Saturn', 'Jupiter', 'Neptun', 'Uran'], 'correct': 1},
        {'question': 'Koji je glavni grad Francuske?', 'options': ['London', 'Berlin', 'Pariz', 'Madrid'], 'correct': 2},
    ]

# ========== FUNKCIJE ZA KVIZ ==========
async def send_question_to_all():
    """Šalje trenutno pitanje svim klijentima"""
    global current_question_index, quiz_active, current_questions
    
    if not quiz_active or current_question_index >= len(current_questions):
        await broadcast({"type": "quiz_end"})
        quiz_active = False
        return
    
    q = current_questions[current_question_index]
    await broadcast({
        "type": "question",
        "index": current_question_index + 1,
        "total": len(current_questions),
        "question": q['question'],
        "options": q['options'],
        "time": 15  # Vreme za odgovor u sekundama
    })

async def broadcast(message: dict):
    """Šalje poruku svim povezanim klijentima"""
    if active_connections:
        for connection in active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

async def broadcast_teams():
    """Šalje ažuriranu listu timova svima"""
    await broadcast({
        'type': 'teams_update',
        'teams': [{'name': t['name'], 'score': t['score']} for t in teams]
    })

# ========== HTTP ENDPOINTI ==========
@app.get("/")
@app.get("/health")
async def health_check():
    """Health check za Render"""
    return PlainTextResponse("OK")

@app.post("/set_language")
async def set_language(lang: str):
    """Menja jezik kviza"""
    global current_language, all_questions, current_questions, quiz_active
    current_language = lang
    all_questions = load_questions_by_language(lang)
    current_questions = all_questions.copy()
    quiz_active = False
    LOGGER.info(f"Jezik promenjen na: {lang}, učitano {len(all_questions)} pitanja")
    return {"status": "ok", "language": lang, "total_questions": len(all_questions)}

@app.post("/start_quiz")
async def start_quiz(num_questions: int = 10):
    """Pokreće kviz sa odabranim brojem pitanja"""
    global current_questions, current_question_index, quiz_active, all_questions
    
    if not all_questions:
        all_questions = load_questions_by_language(current_language)
    
    if len(all_questions) < num_questions:
        return {"status": "error", "message": f"Nema dovoljno pitanja! (ima: {len(all_questions)}, treba: {num_questions})"}
    
    # Nasumično odaberi pitanja
    indices = random.sample(range(len(all_questions)), num_questions)
    current_questions = [all_questions[idx] for idx in indices]
    current_question_index = 0
    quiz_active = True
    
    LOGGER.info(f"Kviz pokrenut sa {len(current_questions)} pitanja")
    
    # Resetuj poene timova
    for team in teams:
        team['score'] = 0
    
    # Pošalji prvo pitanje
    await send_question_to_all()
    await broadcast_teams()
    
    return {"status": "ok", "total_questions": len(current_questions)}

@app.get("/quiz_status")
async def quiz_status():
    """Vraća trenutni status kviza"""
    return {
        "active": quiz_active,
        "current_question": current_question_index + 1 if quiz_active else 0,
        "total_questions": len(current_questions),
        "language": current_language,
        "teams": [{'name': t['name'], 'score': t['score']} for t in teams]
    }

# ========== WEBSOCKET ENDPOINT ==========
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get('type')
            LOGGER.info(f"Poruka: {msg_type} od {message.get('team_name', '')}")
            
            if msg_type == 'client_login':
                team_name = message.get('team_name', '')
                player_name = message.get('player_name', '')
                
                existing = next((t for t in teams if t['name'] == team_name), None)
                if existing:
                    existing['websocket'] = websocket
                    existing['player_name'] = player_name
                else:
                    teams.append({
                        'name': team_name,
                        'player_name': player_name,
                        'score': 0,
                        'websocket': websocket
                    })
                
                LOGGER.info(f"Tim registrovan: {team_name}")
                await websocket.send_text(json.dumps({
                    'type': 'login_success',
                    'team_name': team_name,
                    'message': 'Uspešno prijavljeni!'
                }))
                
                await broadcast_teams()
            
            elif msg_type == 'buzz':
                team_name = message.get('team_name', '')
                LOGGER.info(f"🔔 BUZZ od tima: {team_name}")
                await broadcast({
                    'type': 'buzz',
                    'team_name': team_name
                })
            
            elif msg_type == 'answer':
                team_name = message.get('team_name', '')
                answer_index = message.get('answer_index', -1)
                
                if not quiz_active or current_question_index >= len(current_questions):
                    await websocket.send_text(json.dumps({
                        'type': 'error',
                        'message': 'Kviz nije aktivan ili je završen'
                    }))
                    return
                
                # Proveri tačnost
                current_q = current_questions[current_question_index]
                is_correct = (answer_index == current_q['correct'])
                
                # Ažuriraj poene
                for team in teams:
                    if team['name'] == team_name:
                        if is_correct:
                            team['score'] += 10
                        else:
                            team['score'] -= 5
                        break
                
                LOGGER.info(f"Odgovor od {team_name}: {answer_index} - {'TAČNO' if is_correct else 'NETAČNO'}")
                
                # Pošalji rezultat
                await broadcast({
                    'type': 'answer_submitted',
                    'team_name': team_name,
                    'answer_index': answer_index,
                    'is_correct': is_correct,
                    'correct_answer': current_q['correct'],
                    'score': next((t['score'] for t in teams if t['name'] == team_name), 0)
                })
                
                # Ažuriraj tabelu
                await broadcast_teams()
                
                # Idi na sledeće pitanje posle kratke pauze
                await asyncio.sleep(2)
                current_question_index += 1
                await send_question_to_all()
            
            elif msg_type == 'get_state':
                state = {
                    'type': 'state_update',
                    'teams': [{'name': t['name'], 'score': t['score']} for t in teams],
                    'quiz_active': quiz_active,
                    'current_question': current_question_index + 1 if quiz_active else 0,
                    'total_questions': len(current_questions)
                }
                await websocket.send_text(json.dumps(state))
    
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
        LOGGER.info(f"Klijent se odjavio. Aktivni: {len(active_connections)}")

# ========== POKRETANJE SERVERA ==========
if __name__ == "__main__":
    # Učitaj pitanja pri startu
    all_questions = load_questions_by_language(current_language)
    current_questions = all_questions.copy()
    LOGGER.info(f"Ukupno učitano pitanja: {len(all_questions)}")
    
    port = int(os.environ.get('PORT', 10000))
    LOGGER.info(f"🚀 Pokrećem FastAPI server na portu {port}")
    LOGGER.info(f"🔗 Health check: http://0.0.0.0:{port}/health")
    LOGGER.info(f"🌐 WebSocket: ws://0.0.0.0:{port}/ws")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
