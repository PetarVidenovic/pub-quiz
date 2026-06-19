# web_main.py - Bez Pygame, samo WebSocket server

import json
import logging
import asyncio
import websockets
import random
from datetime import datetime

# ========== KONFIGURACIJA ==========
logging.basicConfig(level=logging.INFO)

# ========== GLOBALNO STANJE ==========
teams = []
current_question = 0
questions = []
quiz_active = False
clients = set()

# ========== WEBSOCKET HENDLER ==========
async def handler(websocket):
    """Glavni WebSocket hendler"""
    clients.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            await handle_message(websocket, data)
    finally:
        clients.remove(websocket)

async def handle_message(websocket, data):
    """Obrada poruka od klijenata"""
    msg_type = data.get('type')
    
    if msg_type == 'client_login':
        team_name = data.get('team_name', '')
        teams.append({
            'name': team_name,
            'score': 0,
            'websocket': websocket
        })
        await broadcast({
            'type': 'teams_update',
            'teams': [{'name': t['name'], 'score': t['score']} for t in teams]
        })
    
    elif msg_type == 'buzz':
        team_name = data.get('team_name', '')
        await broadcast({
            'type': 'buzz',
            'team_name': team_name
        })
    
    elif msg_type == 'answer':
        team_name = data.get('team_name', '')
        answer = data.get('answer_index', -1)
        # Logika za odgovor...
        await broadcast({
            'type': 'answer_submitted',
            'team_name': team_name,
            'is_correct': True  # Zameni sa stvarnom logikom
        })

async def broadcast(message):
    """Šalje poruku svim povezanim klijentima"""
    if clients:
        await asyncio.wait([
            client.send(json.dumps(message))
            for client in clients
        ])

# ========== POKRETANJE SERVERA ==========
async def main():
    port = int(os.environ.get('PORT', 10000))
    async with websockets.serve(handler, "0.0.0.0", port):
        logging.info(f"Server pokrenut na portu {port}")
        await asyncio.Future()  # Večno radi

if __name__ == "__main__":
    import os
    asyncio.run(main())
