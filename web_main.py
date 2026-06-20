# web_main.py - KONAČNO RADI! (HTTP na 10000, WebSocket na 10001)

import json
import logging
import asyncio
import websockets
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
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

# ========== 1. HTTP SERVER ZA HEALTH CHECK ==========
class HealthCheckHandler(BaseHTTPRequestHandler):
    """Handluje HTTP zahteve za Render health check"""
    
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_HEAD(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Isključuje nepotrebne logove

def run_http_server(port):
    """Pokreće HTTP server u posebnom thread-u"""
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    LOGGER.info(f"✅ HTTP server za health check pokrenut na portu {port}")
    server.serve_forever()

# ========== 2. WEBSOCKET HENDLER ==========
async def websocket_handler(websocket):
    """Glavni WebSocket hendler"""
    await websocket.accept()
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
        await send_current_state(websocket)

async def send_to_client(websocket, message):
    try:
        await websocket.send(json.dumps(message))
    except Exception as e:
        LOGGER.error(f"Greška pri slanju: {e}")

async def broadcast(message):
    if clients:
        await asyncio.wait([
            asyncio.create_task(client.send(json.dumps(message)))
            for client in clients.copy()
        ])

async def broadcast_teams():
    await broadcast({
        'type': 'teams_update',
        'teams': [{'name': t['name'], 'score': t['score']} for t in teams]
    })

async def send_current_state(websocket):
    state = {
        'type': 'state_update',
        'teams': [{'name': t['name'], 'score': t['score']} for t in teams],
        'quiz_active': quiz_active,
        'total_questions': len(questions)
    }
    await send_to_client(websocket, state)

# ========== 3. POKRETANJE OBA SERVERA ==========
async def main():
    """Pokreće HTTP na 10000, WebSocket na 10001"""
    # Portovi
    http_port = int(os.environ.get('PORT', 10000))
    ws_port = http_port + 1  # WebSocket na 10001
    
    LOGGER.info(f"🚀 Pokrećem HTTP server na portu {http_port}")
    LOGGER.info(f"🚀 Pokrećem WebSocket server na portu {ws_port}")
    
    # 1. Pokreni HTTP server u pozadinskom thread-u
    http_thread = threading.Thread(
        target=run_http_server,
        args=(http_port,),
        daemon=True
    )
    http_thread.start()
    
    # 2. Pokreni WebSocket server
    async with websockets.serve(
        websocket_handler,
        "0.0.0.0",
        ws_port
    ):
        LOGGER.info(f"✅ Serveri uspešno pokrenuti!")
        LOGGER.info(f"🔗 Health check: http://0.0.0.0:{http_port}/health")
        LOGGER.info(f"🌐 WebSocket: ws://0.0.0.0:{ws_port}")
        await asyncio.Future()  # Radi zauvek

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("Server zaustavljen")
    except Exception as e:
        LOGGER.error(f"Greška: {e}")
