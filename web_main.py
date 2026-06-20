# web_main.py - FastAPI verzija (RADI SIGURNO!)

import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
import uvicorn
import os
from typing import List, Dict

# ========== KONFIGURACIJA ==========
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# ========== FASTAPI APP ==========
app = FastAPI()

# ========== GLOBALNO STANJE ==========
teams: List[Dict] = []
active_connections: List[WebSocket] = []
quiz_active = False
questions = []

# ========== HTTP ENDPOINTI ==========
@app.get("/")
@app.get("/health")
async def health_check():
    """Health check za Render"""
    return PlainTextResponse("OK")

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
                
                await broadcast({
                    'type': 'teams_update',
                    'teams': [{'name': t['name'], 'score': t['score']} for t in teams]
                })
            
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
                LOGGER.info(f"Odgovor od {team_name}: {answer_index}")
                await broadcast({
                    'type': 'answer_submitted',
                    'team_name': team_name,
                    'answer_index': answer_index,
                    'is_correct': True
                })
            
            elif msg_type == 'get_state':
                state = {
                    'type': 'state_update',
                    'teams': [{'name': t['name'], 'score': t['score']} for t in teams],
                    'quiz_active': quiz_active,
                    'total_questions': len(questions)
                }
                await websocket.send_text(json.dumps(state))
    
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        LOGGER.info(f"Klijent se odjavio. Aktivni: {len(active_connections)}")

async def broadcast(message: dict):
    """Šalje poruku svim povezanim klijentima"""
    if active_connections:
        for connection in active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

# ========== POKRETANJE SERVERA ==========
if __name__ == "__main__":
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
