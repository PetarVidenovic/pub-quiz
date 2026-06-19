# web_main.py - Konačno ispravna verzija!

import json
import logging
import asyncio
import websockets
import os
from datetime import datetime

# ========== KONFIGURACIJA ==========
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# ========== GLOBALNO STANJE ==========
teams = []
clients = set()
quiz_active = False
current_question = 0
questions = []

# ========== HTTP HENDLER ZA HEALTH CHECK ==========
async def http_handler(path, request_headers):
    """
    Handluje HTTP zahteve (health check).
    Prima 2 argumenta: path i request_headers
    """
    LOGGER.info(f"HTTP zahtev: {path}")
    
    # Health check endpoint
    if path == "/health" or path == "/":
        return websockets.http11.Response(
            status_code=200,
            reason_phrase="OK",  # OVO JE BITNO!
            headers=[("Content-Type", "text/plain")],
            body=b"OK"
        )
    
    # Sve ostalo - 404
    return websockets.http11.Response(
        status_code=404,
        reason_phrase="Not Found",  # OVO JE BITNO!
        headers=[("Content-Type", "text/plain")],
        body=b"Not Found"
    )

# ========== WEBSOCKET HENDLER ==========
async def websocket_handler(websocket):
    """Glavni WebSocket hendler"""
    clients.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            await handle_message(websocket, data)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clients.remove(websocket)
        LOGGER.info(f"Klijent se odjavio. Aktivni: {len(clients)}")

async def handle_message(websocket, data):
    """Obrada poruka od klijenata"""
    msg_type = data.get('type')
    LOGGER.info(f"Primljena poruka: {msg_type} od {data.get('team_name', 'nepoznat')}")
    
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
        await send_to_client(websocket, {
            'type': 'login_success',
            'team_name': team_name,
            'message': 'Uspešno prijavljeni!'
        })
        await broadcast_teams()
    
    elif msg_type == 'buzz':
        team_name = data.get('team_name', '')
        LOGGER.info(f"BUZZ od tima: {team_name}")
        await broadcast({
            'type': 'buzz',
            'team_name': team_name
        })
    
    elif msg_type == 'answer':
        team_name = data.get('team_name', '')
        answer_index = data.get('answer_index', -1)
        LOGGER.info(f"Odgovor od {team_name}: {answer_index}")
        # Ovde dodaj logiku za proveru odgovora
        await broadcast({
            'type': 'answer_submitted',
            'team_name': team_name,
            'answer_index': answer_index,
            'is_correct': True
        })
    
    elif msg_type == 'get_state':
        await send_current_state(websocket)

async def send_to_client(websocket, message):
    """Šalje poruku jednom klijentu"""
    try:
        await websocket.send(json.dumps(message))
    except Exception as e:
        LOGGER.error(f"Greška pri slanju: {e}")

async def broadcast(message):
    """Šalje poruku svim povezanim klijentima"""
    if clients:
        await asyncio.wait([
            asyncio.create_task(client.send(json.dumps(message)))
            for client in clients.copy()
        ])

async def broadcast_teams():
    """Šalje ažuriranu listu timova"""
    await broadcast({
        'type': 'teams_update',
        'teams': [{'name': t['name'], 'score': t['score']} for t in teams]
    })

async def send_current_state(websocket):
    """Šalje trenutno stanje klijentu"""
    state = {
        'type': 'state_update',
        'teams': [{'name': t['name'], 'score': t['score']} for t in teams],
        'quiz_active': quiz_active,
        'total_questions': len(questions)
    }
    await send_to_client(websocket, state)

# ========== POKRETANJE SERVERA ==========
async def main():
    """Pokreće server sa HTTP i WebSocket podrškom"""
    port = int(os.environ.get('PORT', 10000))
    LOGGER.info(f"Pokrećem server na portu {port}")
    
    # Kreiramo server sa HTTP i WebSocket handler-ima
    async with websockets.serve(
        websocket_handler,
        "0.0.0.0",  # BITNO: Bind na sve interfejse
        port,
        process_request=http_handler
    ):
        LOGGER.info(f"✅ Server uspešno pokrenut na portu {port}")
        LOGGER.info(f"🔗 Health check: http://0.0.0.0:{port}/health")
        LOGGER.info(f"🌐 WebSocket: ws://0.0.0.0:{port}")
        await asyncio.Future()  # Radi zauvek

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Server zaustavljen")
    except Exception as e:
        LOGGER.error(f"Greška: {e}")
