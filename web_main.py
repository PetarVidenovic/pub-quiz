# web_main.py - KONAČNA RADI VERZIJA SA HTTP PODRŠKOM!

import json
import logging
import asyncio
import websockets
import os
from http import HTTPStatus

# ========== KONFIGURACIJA ==========
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# ========== GLOBALNO STANJE ==========
teams = []
clients = set()
quiz_active = False
questions = []

# ========== HTTP HENDLER ==========
async def http_handler(path, request_headers):
    """
    Handluje HTTP zahteve (HEAD i GET).
    Ovo je ključno za Render!
    """
    LOGGER.info(f"HTTP zahtev: {path}")
    
    # Odgovori na sve HTTP zahteve sa "OK"
    # Ovo zadovoljava Render-ov health check
    return websockets.http11.Response(
        status_code=HTTPStatus.OK,
        reason_phrase="OK",
        headers=[("Content-Type", "text/plain")],
        body=b"OK"
    )

# ========== WEBSOCKET HENDLER ==========
async def websocket_handler(websocket):
    """Glavni WebSocket hendler"""
    await websocket.accept()
    clients.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get('type')
            LOGGER.info(f"Poruka: {msg_type} od {data.get('team_name', '')}")
            
            if msg_type == 'client_login':
                team_name = data.get('team_name', '')
                player_name = data.get('player_name', '')
                
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
                await websocket.send(json.dumps({
                    'type': 'login_success',
                    'team_name': team_name,
                    'message': 'Uspešno prijavljeni!'
                }))
                
                await broadcast({
                    'type': 'teams_update',
                    'teams': [{'name': t['name'], 'score': t['score']} for t in teams]
                })
            
            elif msg_type == 'buzz':
                team_name = data.get('team_name', '')
                LOGGER.info(f"🔔 BUZZ od tima: {team_name}")
                await broadcast({
                    'type': 'buzz',
                    'team_name': team_name
                })
            
            elif msg_type == 'answer':
                team_name = data.get('team_name', '')
                answer_index = data.get('answer_index', -1)
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
                await websocket.send(json.dumps(state))
    
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.remove(websocket)
        LOGGER.info(f"Klijent se odjavio. Aktivni: {len(clients)}")

async def broadcast(message):
    """Šalje poruku svim povezanim klijentima"""
    if clients:
        await asyncio.wait([
            asyncio.create_task(client.send(json.dumps(message)))
            for client in clients.copy()
        ])

# ========== POKRETANJE SERVERA ==========
async def main():
    """Pokreće WebSocket server sa HTTP podrškom"""
    port = int(os.environ.get('PORT', 10000))
    LOGGER.info(f"🚀 Pokrećem server na portu {port}")
    
    # Pokreni server sa HTTP handler-om
    async with websockets.serve(
        websocket_handler,
        "0.0.0.0",
        port,
        process_request=http_handler  # OVO JE KLJUČNO!
    ):
        LOGGER.info(f"✅ Server uspešno pokrenut na portu {port}")
        LOGGER.info(f"🌐 WebSocket: ws://0.0.0.0:{port}")
        LOGGER.info(f"🔗 HTTP: http://0.0.0.0:{port} (za health check)")
        await asyncio.Future()  # Radi zauvek

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Server zaustavljen")
    except Exception as e:
        LOGGER.error(f"Greška: {e}")
