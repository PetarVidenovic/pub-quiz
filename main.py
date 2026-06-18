import pygame
import sys
import random
import time
import json
import os
import socket
import threading
from datetime import datetime
import csv
import shutil
import logging
import argparse
import re
from io import BytesIO

# ========== KONFIGURACIJA LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kviz.log'),
        logging.StreamHandler()
    ]
)

# ========== POKUSAJ IMPORT BIBLIOTEKA ==========
try:
    import qrcode
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False
    logging.warning("QR kod biblioteka nije dostupna")

# ========== ARGUMENTI KOMANDNE LINIJE ==========
def parse_args():
    parser = argparse.ArgumentParser(description='Pub Kviz Master - Profesionalni sistem za vođenje kvizova')
    parser.add_argument('--lang', default='srpski', choices=['srpski', 'engleski', 'francuski', 'ruski', 'nemacki'], help='Jezik interfejsa')
    parser.add_argument('--port', type=int, default=65432, help='Port za WebSocket server')
    parser.add_argument('--fullscreen', action='store_true', help='Pokreni u punom ekranu')
    parser.add_argument('--load', help='Učitaj sačuvano takmičenje')
    parser.add_argument('--demo', action='store_true', help='Pokreni demo verziju sa ograničenjima')
    return parser.parse_args()

ARGS = parse_args()

# ========== PODRSKA ZA VISE JEZIKA ==========
LANGUAGES = {
    'srpski': {
        'title': "PUB KVIZ TAKMIČENJE",
        'setup_subtitle': "Podešavanje novog takmičenja",
        'quiz_name': "Naziv takmičenja:",
        'time_per_q': "Vreme po pitanju (sec):",
        'num_questions': "Broj pitanja:",
        'online': "Omogući online konekciju:",
        'next': "DALJE → PRIJAVA TIMOVA",
        'history': "ISTORIJA",
        'settings': "PODEŠAVANJA",
        'quick_quiz': "BRZI KVIZ",
        'teams_registered': "PRIJAVLJENI TIMOVI:",
        'new_team': "NOVI TIM:",
        'team_name': "Ime tima:",
        'members': "Članovi tima (maks. 6):",
        'add_team': "+ DODAJ TIM",
        'start_quiz': "POČNI KVIZ",
        'back': "← NAZAD",
        'quick_register': "BRZA PRIJAVA",
        'active_team': "AKTIVAN TIM:",
        'time_left': "VREME:",
        'teams_participating': "UČESTVUJE TIMOVA:",
        'results': "REZULTATI TAKMIČENJA",
        'rank': "RANG",
        'team': "IME TIMA",
        'points': "POENI",
        'new_competition': "NOVA",
        'save': "SAČUVAJ",
        'export': "IZVEZI CSV",
        'enter_question': "UNESI PITANJE",
        'report': "IZVEŠTAJ",
        'history_title': "ISTORIJA",
        'saved': "SAČUVANO:",
        'repeat_quiz': "PONOVI KVIZ",
        'delete': "OBRIŠI",
        'language': "JEZIK",
        'correct_answers': "TAČNI ODGOVORI",
        'fastest': "NAJBRŽI",
        'avg_time': "PROSEK",
        'score': "POENI",
        'music_on': "MUZIKA UKLJUČENA",
        'music_off': "MUZIKA ISKLJUČENA",
        'volume': "JAČINA ZVUKA",
        'render_url': "RENDER URL",
        'back_settings': "NAZAD",
        'points_correct': "POENI ZA TAČAN ODGOVOR:",
        'points_incorrect': "KAZNA ZA NETACAN:",
        'exit': "IZLAZ",
        'admin_password': "ADMIN LOZINKA:",
        'save_settings': "SAČUVAJ PODEŠAVANJA",
        'music_toggle': "UKLJUČI/ISKLJUČI MUZIKU",
        'player_name': "TVOJE IME:",
        'team_name_input': "IME TIMA:",
        'join_game': "PRIDRUŽI SE",
        'waiting': "ČEKANJE NA POČETAK...",
        'your_score': "TVOJ SKOR:",
        'game_over': "KRAJ IGRE!",
        'final_results': "KONAČNI REZULTATI",
        'correct': "TAČNO!",
        'incorrect': "NETAČNO!",
        'next_question': "SLEDEĆE PITANJE",
        'buzz': "BUZZ!"
    },
    'engleski': {
        'title': "PUB QUIZ COMPETITION",
        'setup_subtitle': "New competition setup",
        'quiz_name': "Competition name:",
        'time_per_q': "Time per question (sec):",
        'num_questions': "Number of questions:",
        'online': "Enable online connection:",
        'next': "NEXT → TEAM REGISTRATION",
        'history': "HISTORY",
        'settings': "SETTINGS",
        'quick_quiz': "QUICK QUIZ",
        'teams_registered': "REGISTERED TEAMS:",
        'new_team': "NEW TEAM:",
        'team_name': "Team name:",
        'members': "Team members (max 6):",
        'add_team': "+ ADD TEAM",
        'start_quiz': "START QUIZ",
        'back': "← BACK",
        'quick_register': "QUICK REGISTER",
        'active_team': "ACTIVE TEAM:",
        'time_left': "TIME:",
        'teams_participating': "TEAMS:",
        'results': "COMPETITION RESULTS",
        'rank': "RANK",
        'team': "TEAM NAME",
        'points': "POINTS",
        'new_competition': "NEW",
        'save': "SAVE",
        'export': "EXPORT CSV",
        'enter_question': "ADD QUESTION",
        'report': "REPORT",
        'history_title': "HISTORY",
        'saved': "SAVED:",
        'repeat_quiz': "REPEAT QUIZ",
        'delete': "DELETE",
        'language': "LANGUAGE",
        'correct_answers': "CORRECT",
        'fastest': "FASTEST",
        'avg_time': "AVG TIME",
        'score': "POINTS",
        'music_on': "MUSIC ON",
        'music_off': "MUSIC OFF",
        'volume': "VOLUME",
        'render_url': "RENDER URL",
        'back_settings': "BACK",
        'points_correct': "POINTS FOR CORRECT:",
        'points_incorrect': "PENALTY FOR WRONG:",
        'exit': "EXIT",
        'admin_password': "ADMIN PASSWORD:",
        'save_settings': "SAVE SETTINGS",
        'music_toggle': "TOGGLE MUSIC",
        'player_name': "YOUR NAME:",
        'team_name_input': "TEAM NAME:",
        'join_game': "JOIN GAME",
        'waiting': "WAITING TO START...",
        'your_score': "YOUR SCORE:",
        'game_over': "GAME OVER!",
        'final_results': "FINAL RESULTS",
        'correct': "CORRECT!",
        'incorrect': "WRONG!",
        'next_question': "NEXT QUESTION",
        'buzz': "BUZZ!"
    },
    'francuski': {
        'title': "CONCOURS DE QUIZ PUB",
        'setup_subtitle': "Configuration du nouveau concours",
        'quiz_name': "Nom du concours:",
        'time_per_q': "Temps par question (sec):",
        'num_questions': "Nombre de questions:",
        'online': "Activer la connexion en ligne:",
        'next': "SUIVANT → INSCRIPTION DES ÉQUIPES",
        'history': "HISTORIQUE",
        'settings': "PARAMÈTRES",
        'quick_quiz': "QUIZ RAPIDE",
        'teams_registered': "ÉQUIPES INSCRITES:",
        'new_team': "NOUVELLE ÉQUIPE:",
        'team_name': "Nom de l'équipe:",
        'members': "Membres (max 6):",
        'add_team': "+ AJOUTER ÉQUIPE",
        'start_quiz': "COMMENCER QUIZ",
        'back': "← RETOUR",
        'quick_register': "INSCRIPTION RAPIDE",
        'active_team': "ÉQUIPE ACTIVE:",
        'time_left': "TEMPS:",
        'teams_participating': "ÉQUIPES:",
        'results': "RÉSULTATS DU CONCOURS",
        'rank': "RANG",
        'team': "NOM DE L'ÉQUIPE",
        'points': "POINTS",
        'new_competition': "NOUVEAU",
        'save': "SAUVEGARDER",
        'export': "EXPORTER CSV",
        'enter_question': "AJOUTER QUESTION",
        'report': "RAPPORT",
        'history_title': "HISTORIQUE",
        'saved': "SAUVEGARDÉ:",
        'repeat_quiz': "RÉPÉTER QUIZ",
        'delete': "SUPPRIMER",
        'language': "LANGUE",
        'correct_answers': "BONNES RÉPONSES",
        'fastest': "PLUS RAPIDE",
        'avg_time': "MOYENNE",
        'score': "POINTS",
        'music_on': "MUSIQUE ACTIVE",
        'music_off': "MUSIQUE INACTIVE",
        'volume': "VOLUME",
        'render_url': "URL RENDER",
        'back_settings': "RETOUR",
        'points_correct': "POINTS POUR BONNE RÉPONSE:",
        'points_incorrect': "PÉNALITÉ POUR MAUVAISE:",
        'exit': "SORTIR",
        'admin_password': "MOT DE PASSE ADMIN:",
        'save_settings': "ENREGISTRER PARAMÈTRES",
        'music_toggle': "ACTIVER/DÉSACTIVER MUSIQUE",
        'player_name': "VOTRE NOM:",
        'team_name_input': "NOM DE L'ÉQUIPE:",
        'join_game': "REJOINDRE",
        'waiting': "EN ATTENTE...",
        'your_score': "VOTRE SCORE:",
        'game_over': "FIN DU JEU!",
        'final_results': "RÉSULTATS FINAUX",
        'correct': "CORRECT!",
        'incorrect': "INCORRECT!",
        'next_question': "QUESTION SUIVANTE",
        'buzz': "BUZZ!"
    },
    'ruski': {
        'title': "ПУБ-ВИКТОРИНА",
        'setup_subtitle': "Настройка нового соревнования",
        'quiz_name': "Название:",
        'time_per_q': "Время на вопрос (сек):",
        'num_questions': "Количество вопросов:",
        'online': "Включить онлайн подключение:",
        'next': "ДАЛЕЕ → РЕГИСТРАЦИЯ КОМАНД",
        'history': "ИСТОРИЯ",
        'settings': "НАСТРОЙКИ",
        'quick_quiz': "БЫСТРАЯ ВИКТОРИНА",
        'teams_registered': "ЗАРЕГИСТРИРОВАННЫЕ КОМАНДЫ:",
        'new_team': "НОВАЯ КОМАНДА:",
        'team_name': "Название команды:",
        'members': "Члены команды (макс 6):",
        'add_team': "+ ДОБАВИТЬ КОМАНДУ",
        'start_quiz': "НАЧАТЬ ВИКТОРИНУ",
        'back': "← НАЗАД",
        'quick_register': "БЫСТРАЯ РЕГИСТРАЦИЯ",
        'active_team': "АКТИВНАЯ КОМАНДА:",
        'time_left': "ВРЕМЯ:",
        'teams_participating': "КОМАНД:",
        'results': "РЕЗУЛЬТАТЫ СОРЕВНОВАНИЯ",
        'rank': "МЕСТО",
        'team': "КОМАНДА",
        'points': "ОЧКИ",
        'new_competition': "НОВЫЙ",
        'save': "СОХРАНИТЬ",
        'export': "ЭКСПОРТ CSV",
        'enter_question': "ДОБАВИТЬ ВОПРОС",
        'report': "ОТЧЕТ",
        'history_title': "ИСТОРИЯ",
        'saved': "СОХРАНЕНО:",
        'repeat_quiz': "ПОВТОРИТЬ",
        'delete': "УДАЛИТЬ",
        'language': "ЯЗЫК",
        'correct_answers': "ВЕРНЫЕ ОТВЕТЫ",
        'fastest': "БЫСТРЕЙШИЙ",
        'avg_time': "СРЕДНЕЕ",
        'score': "ОЧКИ",
        'music_on': "МУЗЫКА ВКЛ",
        'music_off': "МУЗЫКА ВЫКЛ",
        'volume': "ГРОМКОСТЬ",
        'render_url': "URL RENDER",
        'back_settings': "НАЗАД",
        'points_correct': "ОЧКИ ЗА ВЕРНЫЙ ОТВЕТ:",
        'points_incorrect': "ШТРАФ ЗА НЕВЕРНЫЙ:",
        'exit': "ВЫХОД",
        'admin_password': "ПАРОЛЬ АДМИНА:",
        'save_settings': "СОХРАНИТЬ НАСТРОЙКИ",
        'music_toggle': "ВКЛ/ВЫКЛ МУЗЫКУ",
        'player_name': "ВАШЕ ИМЯ:",
        'team_name_input': "НАЗВАНИЕ КОМАНДЫ:",
        'join_game': "ПРИСОЕДИНИТЬСЯ",
        'waiting': "ОЖИДАНИЕ...",
        'your_score': "ВАШ СЧЕТ:",
        'game_over': "ИГРА ОКОНЧЕНА!",
        'final_results': "ИТОГОВЫЕ РЕЗУЛЬТАТЫ",
        'correct': "ВЕРНО!",
        'incorrect': "НЕВЕРНО!",
        'next_question': "СЛЕДУЮЩИЙ ВОПРОС",
        'buzz': "BUZZ!"
    },
    'nemacki': {
        'title': "PUB QUIZ WETTBEWERB",
        'setup_subtitle': "Neuen Wettbewerb einrichten",
        'quiz_name': "Wettbewerbsname:",
        'time_per_q': "Zeit pro Frage (Sek):",
        'num_questions': "Anzahl der Fragen:",
        'online': "Online-Verbindung aktivieren:",
        'next': "WEITER → TEAMREGISTRIERUNG",
        'history': "VERLAUF",
        'settings': "EINSTELLUNGEN",
        'quick_quiz': "SCHNELLQUIZ",
        'teams_registered': "REGISTRIERTE TEAMS:",
        'new_team': "NEUES TEAM:",
        'team_name': "Teamname:",
        'members': "Teammitglieder (max 6):",
        'add_team': "+ TEAM HINZUFÜGEN",
        'start_quiz': "QUIZ STARTEN",
        'back': "← ZURÜCK",
        'quick_register': "SCHNELLREGISTRIERUNG",
        'active_team': "AKTIVES TEAM:",
        'time_left': "ZEIT:",
        'teams_participating': "TEAMS:",
        'results': "WETTBEWERBSERGEBNISSE",
        'rank': "RANG",
        'team': "TEAMNAME",
        'points': "PUNKTE",
        'new_competition': "NEU",
        'save': "SPEICHERN",
        'export': "CSV EXPORTIEREN",
        'enter_question': "FRAGE HINZUFÜGEN",
        'report': "BERICHT",
        'history_title': "VERLAUF",
        'saved': "GESPEICHERT:",
        'repeat_quiz': "QUIZ WIEDERHOLEN",
        'delete': "LÖSCHEN",
        'language': "SPRACHE",
        'correct_answers': "RICHTIGE",
        'fastest': "SCHNELLSTE",
        'avg_time': "DURCHSCHNITT",
        'score': "PUNKTE",
        'music_on': "MUSIK AN",
        'music_off': "MUSIK AUS",
        'volume': "LAUTSTÄRKE",
        'render_url': "RENDER URL",
        'back_settings': "ZURÜCK",
        'points_correct': "PUNKTE FÜR RICHTIG:",
        'points_incorrect': "STRAFE FÜR FALSCH:",
        'exit': "AUSGANG",
        'admin_password': "ADMIN PASSWORT:",
        'save_settings': "EINSTELLUNGEN SPEICHERN",
        'music_toggle': "MUSIK EIN/AUS",
        'player_name': "IHR NAME:",
        'team_name_input': "TEAMNAME:",
        'join_game': "BEITRETEN",
        'waiting': "WARTEN...",
        'your_score': "IHRE PUNKTE:",
        'game_over': "SPIEL VORBEI!",
        'final_results': "ENDERGEBNISSE",
        'correct': "RICHTIG!",
        'incorrect': "FALSCH!",
        'next_question': "NÄCHSTE FRAGE",
        'buzz': "BUZZ!"
    }
}

current_lang = ARGS.lang if ARGS.lang in LANGUAGES else 'srpski'
lang_texts = LANGUAGES[current_lang]

def set_language(lang):
    global current_lang, lang_texts
    if lang in LANGUAGES:
        current_lang = lang
        lang_texts = LANGUAGES[current_lang]
        logging.info(f"Jezik promenjen na: {lang}")

def get_text(key):
    return lang_texts.get(key, key)

# ========== INICIJALIZACIJA PYGAME ==========
pygame.init()
pygame.font.init()
pygame.mixer.init()

# ========== EKRAN I FONTOVI ==========
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)

if ARGS.fullscreen:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)

pygame.display.set_caption("Pub Kviz Master - Profesionalni sistem za vođenje kvizova")
clock = pygame.time.Clock()

# ========== OPTIMIZOVANI FONTOVI ZA BOLJU ČITLJIVOST ==========
try:
    FONT_XL = pygame.font.Font(None, 72)
    FONT_LARGE = pygame.font.Font(None, 52)
    FONT_MEDIUM = pygame.font.Font(None, 40)
    FONT_SMALL = pygame.font.Font(None, 32)
    FONT_XS = pygame.font.Font(None, 26)
    FONT_XXS = pygame.font.Font(None, 22)
except:
    FONT_XL = pygame.font.SysFont('Arial', 72, bold=True)
    FONT_LARGE = pygame.font.SysFont('Arial', 52)
    FONT_MEDIUM = pygame.font.SysFont('Arial', 40)
    FONT_SMALL = pygame.font.SysFont('Arial', 32)
    FONT_XS = pygame.font.SysFont('Arial', 26)
    FONT_XXS = pygame.font.SysFont('Arial', 22)

# ========== BOJE - PROFESIONALNA PALETA ==========
COLORS = {
    'bg_primary': (18, 18, 30),
    'bg_secondary': (28, 28, 45),
    'bg_panel': (38, 38, 58),
    'bg_panel_light': (48, 48, 70),
    'bg_hover': (58, 58, 85),
    'text_primary': (245, 245, 255),
    'text_secondary': (200, 200, 220),
    'text_muted': (150, 150, 180),
    'gold': (218, 165, 32),
    'gold_light': (255, 215, 0),
    'blue': (70, 130, 180),
    'blue_light': (100, 170, 220),
    'green': (60, 200, 100),
    'green_light': (80, 230, 120),
    'red': (220, 80, 80),
    'red_light': (255, 100, 100),
    'purple': (150, 80, 180),
    'orange': (255, 165, 0),
    'silver': (192, 192, 192),
    'bronze': (205, 127, 50),
    'button_primary': (60, 120, 180),
    'button_primary_hover': (80, 150, 210),
    'button_success': (50, 180, 90),
    'button_success_hover': (70, 210, 110),
    'button_danger': (200, 60, 60),
    'button_danger_hover': (230, 80, 80),
    'button_warning': (200, 150, 40),
    'button_warning_hover': (230, 180, 50),
    'button_disabled': (80, 80, 100),
    'border': (100, 100, 140),
    'border_light': (140, 140, 180),
    'border_highlight': (218, 165, 32),
}

# ========== FUNKCIJE ZA PUTANJE ==========
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_data_path(relative_path):
    current_dir_path = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath("."), relative_path)
    if os.path.exists(current_dir_path):
        return current_dir_path
    return resource_path(relative_path)

# ========== MUZIKA ==========
music_playing = False
music_volume = 0.3

def load_music():
    global music_playing
    try:
        music_path = get_data_path("muzika.mp3")
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(music_volume)
        return True
    except:
        logging.warning("Muzika nije pronađena")
        return False

def toggle_music():
    global music_playing
    if music_playing:
        pygame.mixer.music.pause()
        music_playing = False
    else:
        pygame.mixer.music.unpause()
        music_playing = True

def set_music_volume(vol):
    global music_volume
    music_volume = max(0.0, min(1.0, vol))
    pygame.mixer.music.set_volume(music_volume)

# ========== ZVUČNI EFEKTI ==========
sound_effects = {}

def load_sound_effects():
    global sound_effects
    effects = {
        'correct': 'correct.wav',
        'wrong': 'wrong.wav',
        'buzz': 'buzz.wav',
        'timer': 'timer.wav',
        'applause': 'applause.wav'
    }
    for name, file in effects.items():
        try:
            sound_effects[name] = pygame.mixer.Sound(get_data_path(file))
        except:
            sound_effects[name] = None
            logging.warning(f"Zvučni efekat {file} nije pronađen")

def play_sound(name):
    if name in sound_effects and sound_effects[name]:
        try:
            sound_effects[name].play()
        except:
            pass

# ========== VALIDACIJA UNOSA ==========
class InputValidator:
    @staticmethod
    def sanitize_text(text, max_len=100):
        text = re.sub(r'[<>\"\'%;()&+]', '', text)
        return text[:max_len]
    
    @staticmethod
    def validate_team_name(name):
        return len(name.strip()) >= 2 and len(name.strip()) <= 30
    
    @staticmethod
    def validate_player_name(name):
        return len(name.strip()) >= 2 and len(name.strip()) <= 50

# ========== UPRAVLJANJE LOZINKOM ==========
def load_admin_password():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("admin_password", "admin123")
    except:
        default_pw = "admin123"
        config = {"admin_password": default_pw}
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except:
            pass
        return default_pw

def save_admin_password(password):
    try:
        config = {}
        if os.path.exists("config.json"):
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
        config["admin_password"] = password
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        return True
    except:
        return False

# ========== FUNKCIJE ZA UCITAVANJE PITANJA ==========
def load_questions_by_language(lang):
    if lang == 'srpski':
        pitanja_path = get_data_path("pitanja1.txt")
        odgovori_path = get_data_path("odgovori1.txt")
    else:
        pitanja_path = get_data_path("pitanja.txt")
        odgovori_path = get_data_path("odgovori.txt")
    return load_questions_from_files(pitanja_path, odgovori_path)

def load_questions_from_files(pitanja_path, odgovori_path):
    questions = []
    if not os.path.exists(pitanja_path):
        return get_default_questions()
    try:
        with open(pitanja_path, "r", encoding="utf-8") as f:
            content = f.read()
            question_blocks = content.strip().split("\n\n")
            for block in question_blocks:
                lines = [line.strip() for line in block.split("\n") if line.strip()]
                if len(lines) >= 5:
                    question_line = lines[0]
                    if ') ' in question_line:
                        question_text = question_line.split(') ', 1)[1]
                    elif '. ' in question_line:
                        question_text = question_line.split('. ', 1)[1]
                    else:
                        question_text = question_line
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
                    questions.append({'question': question_text, 'options': options, 'correct': 0, 'hint': "Hint nije dostupan."})
    except Exception as e:
        logging.error(f"Greška pri učitavanju pitanja: {e}")
        return get_default_questions()
    
    if os.path.exists(odgovori_path):
        try:
            with open(odgovori_path, "r", encoding="utf-8") as f:
                content = f.read()
                answer_blocks = content.strip().split("\n\n")
                for block in answer_blocks:
                    lines = [line.strip() for line in block.split("\n") if line.strip()]
                    if len(lines) >= 5:
                        question_line = lines[0]
                        if ') ' in question_line:
                            question_text = question_line.split(') ', 1)[1]
                        elif '. ' in question_line:
                            question_text = question_line.split('. ', 1)[1]
                        else:
                            question_text = question_line
                        for i in range(1, 5):
                            if i < len(lines):
                                option_line = lines[i]
                                if "Tacno" in option_line or "tacno" in option_line.lower():
                                    for q in questions:
                                        if q['question'] == question_text:
                                            q['correct'] = i - 1
                                            if 'Tacno' in q['options'][i-1]:
                                                q['options'][i-1] = q['options'][i-1].replace('Tacno', '').strip()
                                            break
                                    break
        except Exception as e:
            logging.error(f"Greška pri učitavanju odgovora: {e}")
    
    for q in questions:
        if q['correct'] not in [0, 1, 2, 3]:
            q['correct'] = random.randint(0, 3)
    return questions

def get_default_questions():
    return [
        {'question': 'Koji je glavni grad Srbije?', 'options': ['Niš', 'Novi Sad', 'Beograd', 'Priština'], 'correct': 2, 'hint': 'Najveći grad u Srbiji.'},
        {'question': 'Koja je najduža reka u Evropi?', 'options': ['Dunav', 'Volga', 'Rajna', 'Temza'], 'correct': 1, 'hint': 'Protice kroz Rusiju.'},
        {'question': 'Koji je hemijski simbol za vodu?', 'options': ['H2O', 'CO2', 'NaCl', 'HCl'], 'correct': 0, 'hint': 'Dva atoma vodonika, jedan kiseonika.'},
        {'question': 'Koja je najveća planeta u Sunčevom sistemu?', 'options': ['Saturn', 'Jupiter', 'Neptun', 'Uran'], 'correct': 1, 'hint': 'Najveća planeta.'},
        {'question': 'Koji je glavni grad Francuske?', 'options': ['London', 'Berlin', 'Pariz', 'Madrid'], 'correct': 2, 'hint': 'Grad ljubavi.'},
    ]

def save_custom_questions(custom_questions):
    try:
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = "."
        custom_file = os.path.join(base_dir, "custom_questions.json")
        with open(custom_file, "w", encoding="utf-8") as f:
            json.dump(custom_questions, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"Greška pri čuvanju custom pitanja: {e}")
        return False

# ========== SPLASH SCREEN ==========
def show_splash_screen():
    splash_duration = 2.5
    start_time = time.time()
    
    for i in range(30):
        color_val = 18 + i
        pygame.draw.rect(screen, (color_val, color_val, color_val + 12), (0, i * 27, SCREEN_WIDTH, 27))
    
    draw_text("🏆 PUB KVIZ MASTER 🏆", FONT_XL, COLORS['gold_light'], SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60, centered=True)
    draw_text("Profesionalni sistem za vođenje kvizova", FONT_MEDIUM, COLORS['text_secondary'], SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 10, centered=True)
    draw_text(f"Verzija 2.0 | © 2025", FONT_SMALL, COLORS['text_muted'], SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70, centered=True)
    
    bar_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 + 120, 400, 8)
    pygame.draw.rect(screen, COLORS['bg_panel'], bar_rect, border_radius=4)
    
    while time.time() - start_time < splash_duration:
        progress = (time.time() - start_time) / splash_duration
        current_width = int(400 * min(1.0, progress))
        progress_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 + 120, current_width, 8)
        pygame.draw.rect(screen, COLORS['gold_light'], progress_rect, border_radius=4)
        pygame.display.flip()
        clock.tick(60)
    
    for alpha in range(255, 0, -15):
        fade_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        fade_surf.fill((0, 0, 0))
        fade_surf.set_alpha(255 - alpha)
        screen.blit(fade_surf, (0, 0))
        pygame.display.flip()
        pygame.time.delay(10)

# ========== BACKUP SISTEM ==========
def create_backup():
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = f"backups/backup_{timestamp}"
        os.makedirs(backup_dir, exist_ok=True)
        
        files_to_backup = [
            'competitions.json',
            'custom_questions.json',
            'config.json'
        ]
        
        for file in files_to_backup:
            if os.path.exists(file):
                shutil.copy2(file, f"{backup_dir}/{file}")
        
        shutil.make_archive(backup_dir, 'zip', backup_dir)
        shutil.rmtree(backup_dir)
        logging.info(f"Backup kreiran: {backup_dir}.zip")
        return True
    except Exception as e:
        logging.error(f"Greška pri kreiranju backup-a: {e}")
        return False

# ========== AUTOMATSKO SAČUAVANJE ==========
auto_save_active = False

def auto_save_quiz():
    global auto_save_active
    auto_save_active = True
    while auto_save_active:
        time.sleep(30)
        if game_state and game_state.quiz_active:
            save_quiz_state()

def save_quiz_state():
    try:
        if not game_state or not game_state.quiz_active:
            return
        
        state_file = f"autosave_{game_state.quiz_name}_{datetime.now().strftime('%Y%m%d')}.json"
        data = {
            'quiz_name': game_state.quiz_name,
            'teams': game_state.teams,
            'current_question': game_state.current_question_index,
            'questions': game_state.current_questions,
            'timestamp': time.time(),
            'time_per_question': game_state.time_per_question,
            'num_questions': game_state.num_questions
        }
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f"Auto-save izvršen: {state_file}")
    except Exception as e:
        logging.error(f"Greška pri auto-save-u: {e}")

def load_quiz_state(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        game_state.quiz_name = data.get('quiz_name', 'Obnovljeni kviz')
        game_state.teams = data.get('teams', [])
        game_state.current_question_index = data.get('current_question', 0)
        game_state.current_questions = data.get('questions', [])
        game_state.time_per_question = data.get('time_per_question', 15)
        game_state.num_questions = data.get('num_questions', 10)
        game_state.quiz_active = True
        game_state.question_start_time = time.time()
        
        logging.info(f"Stanje kviza učitano iz: {filename}")
        return True
    except Exception as e:
        logging.error(f"Greška pri učitavanju stanja: {e}")
        return False

# ========== KLASA ZA UPRAVLJANJE STANJEM ==========
class GameState:
    def __init__(self):
        self.current = "setup"
        self.teams = []
        self.current_questions = []
        self.custom_questions = []
        self.current_question_index = 0
        self.quiz_name = ""
        self.time_per_question = 15
        self.num_questions = 10
        self.quiz_active = False
        self.selected_answer = None
        self.answer_submitted = False
        self.show_correct_answer = False
        self.question_start_time = 0
        self.quiz_start_time = 0
        self.active_team_index = -1
        self.last_buzz_time = 0
        self.buzz_cooldown = 1
        self.disabled_options = []
        self.multiplier_active = False
        self.multiplier_rounds_left = 0
        
        self.points_correct = 10
        self.points_incorrect = 5
        
        self.lifelines = {
            '50_50': {'used': False, 'name': "50/50", 'available': True},
            'hint': {'used': False, 'name': "Hint", 'available': True},
            'audience': {'used': False, 'name': "Publika", 'available': True},
            'skip': {'used': False, 'name': "Preskoči", 'available': True}
        }
        
        self.network_enabled = False
        self.network_clients = []
        self.server_socket = None
        self.client_responses = {}
        self.render_url = ""
        
        self.competitions_history = []
        self.audience_percentages = [0, 0, 0, 0]
        
        self.popup_text = ""
        self.popup_until = 0.0
        
        self.correction_mode = False
        self.correction_password = load_admin_password()
        self.correction_input = ""
        self.selected_team_for_correction = -1
        self.waiting_for_password = False
        
        self.question_input_mode = False
        self.new_question = {
            'question': "",
            'options': ["", "", "", ""],
            'correct': -1,
            'hint': "Hint nije dostupan."
        }
        
        self.scroll_offset_results = 0
        self.scroll_offset_history = 0
        self.scroll_offset_competitions = 0
        
        self.repeat_quiz_data = None
        self.dragging_scroll_bar = False
        self.dragging_scroll_bar_type = ""
        self.drag_start_y = 0
        self.scroll_start_offset = 0
        self.custom_quiz_mode = False
        
        self.render_clients = []
        self.player_scores = {}

    def reset_for_new_question(self):
        self.selected_answer = None
        self.answer_submitted = False
        self.show_correct_answer = False
        self.disabled_options = []
        self.client_responses = {}
        self.question_start_time = time.time()
        self.popup_text = ""
        self.popup_until = 0.0

    def reset_for_new_quiz(self):
        self.current_question_index = 0
        self.quiz_active = False
        self.selected_answer = None
        self.answer_submitted = False
        self.show_correct_answer = False
        self.active_team_index = -1
        self.disabled_options = []
        self.client_responses = {}
        self.scroll_offset_results = 0
        self.custom_quiz_mode = False
        self.multiplier_active = False
        self.multiplier_rounds_left = 0
        
        for key in self.lifelines:
            self.lifelines[key]['used'] = False
            self.lifelines[key]['available'] = True
        
        for team in self.teams:
            team['score'] = 0
            team['answers'] = [None] * self.num_questions
            team['response_times'] = [None] * self.num_questions
            team['correct_count'] = 0
            team['fastest_response'] = None
            team['response_times_list'] = []

    def team_buzz(self, team_index):
        current_time = time.time()
        if current_time - self.last_buzz_time < self.buzz_cooldown:
            return False
        if self.active_team_index == -1:
            self.active_team_index = team_index
            self.last_buzz_time = current_time
            play_sound('buzz')
            return True
        return False

    def submit_answer(self, team_index, answer_index, response_time):
        if team_index != self.active_team_index:
            return False
        
        current_q = self.current_questions[self.current_question_index]
        is_correct = (answer_index == current_q['correct'])
        
        if is_correct:
            points = self.points_correct
            
            if response_time < 1.0:
                points = points // 2
                self.popup_text = f"⚠️ Sumnjivo brzo! +{points} poena"
                self.popup_until = time.time() + 1.5
            
            if self.multiplier_active:
                points *= 3
                self.popup_text = f"🔥 MULTIPLIER 3x! +{points} POENA! 🔥"
                self.popup_until = time.time() + 2.0
            
            self.teams[team_index]['score'] += points
            self.teams[team_index]['answers'][self.current_question_index] = 'correct'
            self.teams[team_index]['response_times'][self.current_question_index] = response_time
            self.teams[team_index]['correct_count'] = self.teams[team_index].get('correct_count', 0) + 1
            self.teams[team_index]['response_times_list'].append(response_time)
            
            if self.teams[team_index].get('fastest_response') is None or response_time < self.teams[team_index]['fastest_response']:
                self.teams[team_index]['fastest_response'] = response_time
            
            if not self.multiplier_active and response_time >= 1.0:
                self.popup_text = f"✅ +{points} POENA!"
                self.popup_until = time.time() + 1.5
            
            play_sound('correct')
        else:
            points_penalty = self.points_incorrect
            self.teams[team_index]['score'] -= points_penalty
            self.teams[team_index]['answers'][self.current_question_index] = 'incorrect'
            self.teams[team_index]['response_times'][self.current_question_index] = response_time
            self.teams[team_index]['response_times_list'].append(response_time)
            self.popup_text = f"❌ -{points_penalty} POENA!"
            self.popup_until = time.time() + 1.5
            play_sound('wrong')
        
        self.answer_submitted = True
        self.show_correct_answer = True
        return True

    def activate_multiplier_round(self, num_rounds=1):
        self.multiplier_active = True
        self.multiplier_rounds_left = num_rounds
        self.popup_text = f"⭐ MULTIPLIER RUNDA AKTIVNA! {num_rounds}x poena! ⭐"
        self.popup_until = time.time() + 3.0

    def use_hint_popup(self):
        if not self.current_questions:
            return
        q = self.current_questions[self.current_question_index]
        correct_idx = q['correct']
        correct_text = q['options'][correct_idx]
        first_two = correct_text[:2] if len(correct_text) >= 2 else correct_text
        self.popup_text = f"Hint: {first_two}.."
        self.popup_until = time.time() + 2.0
        self.lifelines['hint']['used'] = True
        self.lifelines['hint']['available'] = False

    def use_audience_popup(self):
        percentages = simulate_audience()
        p_line = f"A:{percentages[0]}% B:{percentages[1]}% C:{percentages[2]}% D:{percentages[3]}%"
        self.popup_text = p_line
        self.popup_until = time.time() + 3.0
        self.lifelines['audience']['used'] = True
        self.lifelines['audience']['available'] = False
    
    def correct_team_score(self, team_index, new_score):
        if 0 <= team_index < len(self.teams):
            try:
                self.teams[team_index]['score'] = int(new_score)
                return True
            except:
                return False
        return False
    
    def add_new_question(self):
        if (self.new_question['question'].strip() and 
            all(opt.strip() for opt in self.new_question['options']) and
            self.new_question['correct'] >= 0):
            
            new_q = {
                'question': self.new_question['question'],
                'options': self.new_question['options'].copy(),
                'correct': self.new_question['correct'],
                'hint': self.new_question['hint']
            }
            
            all_questions.append(new_q)
            self.custom_questions.append(new_q)
            save_custom_questions(self.custom_questions)
            
            self.new_question = {
                'question': "",
                'options': ["", "", "", ""],
                'correct': -1,
                'hint': "Hint nije dostupan."
            }
            self.question_input_mode = False
            return True
        return False
    
    def delete_competition(self, index):
        if 0 <= index < len(self.competitions_history):
            del self.competitions_history[index]
            save_competitions_to_file(self.competitions_history)
            return True
        return False

game_state = GameState()

# ========== MREZNA KOMUNIKACIJA ==========
def start_server():
    try:
        game_state.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        game_state.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        game_state.server_socket.bind(('0.0.0.0', ARGS.port))
        game_state.server_socket.listen(5)
        game_state.server_socket.settimeout(1)
        game_state.network_enabled = True
        
        accept_thread = threading.Thread(target=accept_clients, daemon=True)
        accept_thread.start()
        receive_thread = threading.Thread(target=receive_messages, daemon=True)
        receive_thread.start()
        heartbeat_thread = threading.Thread(target=client_heartbeat, daemon=True)
        heartbeat_thread.start()
        logging.info(f"Server pokrenut na portu {ARGS.port}")
        return True
    except Exception as e:
        logging.error(f"Greška pri pokretanju servera: {e}")
        game_state.network_enabled = False
        if game_state.server_socket:
            try:
                game_state.server_socket.close()
            except:
                pass
            game_state.server_socket = None
        return False

def stop_server():
    try:
        game_state.network_enabled = False
        for client in game_state.network_clients[:]:
            try:
                client.shutdown(socket.SHUT_RDWR)
                client.close()
            except:
                pass
        game_state.network_clients.clear()
        if game_state.server_socket:
            try:
                game_state.server_socket.shutdown(socket.SHUT_RDWR)
                game_state.server_socket.close()
            except:
                pass
            game_state.server_socket = None
        logging.info("Server zaustavljen")
    except:
        pass

def accept_clients():
    while game_state.network_enabled:
        if not game_state.server_socket:
            break
        try:
            client, addr = game_state.server_socket.accept()
            client.settimeout(0.1)
            game_state.network_clients.append(client)
            send_to_client(client, {
                'type': 'welcome', 
                'message': 'Dobrodošli u kviz!', 
                'teams': [t['name'] for t in game_state.teams], 
                'quiz_name': game_state.quiz_name,
                'render_url': game_state.render_url
            })
            logging.info(f"Novi klijent povezan: {addr}")
        except socket.timeout:
            continue
        except:
            break

def receive_messages():
    while game_state.network_enabled:
        for client in game_state.network_clients[:]:
            try:
                data = client.recv(4096)
                if data:
                    try:
                        message = json.loads(data.decode('utf-8'))
                        handle_client_message(client, message)
                    except:
                        continue
            except:
                try:
                    game_state.network_clients.remove(client)
                except:
                    pass
        time.sleep(0.1)

def client_heartbeat():
    while game_state.network_enabled:
        for client in game_state.network_clients[:]:
            try:
                client.send(b'{"type":"ping"}')
            except:
                try:
                    game_state.network_clients.remove(client)
                except:
                    pass
        time.sleep(5)

def handle_client_message(client, message):
    msg_type = message.get('type', '')
    
    if msg_type == 'team_register':
        team_name = message.get('team_name', '')
        members = message.get('members', [])
        player_name = message.get('player_name', '')
        
        if not InputValidator.validate_team_name(team_name):
            send_to_client(client, {'type': 'error', 'message': 'Ime tima mora imati 2-30 karaktera'})
            return
        
        if not any(t['name'] == team_name for t in game_state.teams):
            game_state.teams.append({
                'name': team_name, 
                'members': members, 
                'player_name': player_name,
                'score': 0,
                'answers': [None] * game_state.num_questions,
                'response_times': [None] * game_state.num_questions,
                'client': client, 
                'correct_count': 0, 
                'fastest_response': None, 
                'response_times_list': []
            })
            logging.info(f"Tim registrovan: {team_name}")
        else:
            for t in game_state.teams:
                if t['name'] == team_name:
                    t['client'] = client
                    t['player_name'] = player_name
                    break
        
        broadcast({'type': 'teams_update', 'teams': [{'name': t['name'], 'score': t['score']} for t in game_state.teams]})
        send_to_client(client, {'type': 'registered', 'team_name': team_name, 'team_id': len(game_state.teams) - 1})
    
    elif msg_type == 'client_login':
        team_name = message.get('team_name', '')
        player_name = message.get('player_name', '')
        
        if not InputValidator.validate_team_name(team_name):
            send_to_client(client, {'type': 'error', 'message': 'Ime tima mora imati 2-30 karaktera'})
            return
        
        if not any(t['name'] == team_name for t in game_state.teams):
            game_state.teams.append({
                'name': team_name, 
                'members': [], 
                'player_name': player_name,
                'score': 0,
                'answers': [None] * game_state.num_questions,
                'response_times': [None] * game_state.num_questions,
                'client': client, 
                'correct_count': 0, 
                'fastest_response': None, 
                'response_times_list': []
            })
            logging.info(f"Novi tim preko Render-a: {team_name}")
        else:
            for t in game_state.teams:
                if t['name'] == team_name:
                    t['client'] = client
                    t['player_name'] = player_name
                    break
        
        if game_state.quiz_active:
            send_current_question(client)
        
        broadcast({'type': 'participants_update', 'participants': sum(1 for t in game_state.teams if t.get('client'))})
        send_to_client(client, {'type': 'login_success', 'team_name': team_name})
    
    elif msg_type == 'buzz':
        team_name = message.get('team_name', '')
        for i, team in enumerate(game_state.teams):
            if team['name'] == team_name:
                if game_state.team_buzz(i):
                    broadcast({'type': 'buzz', 'team_name': team_name, 'team_index': i})
                    play_sound('buzz')
                break
    
    elif msg_type == 'answer':
        team_name = message.get('team_name', '')
        answer_index = message.get('answer_index', -1)
        response_time = message.get('response_time', 0)
        for i, team in enumerate(game_state.teams):
            if team['name'] == team_name:
                if game_state.submit_answer(i, answer_index, response_time):
                    is_correct = (answer_index == game_state.current_questions[game_state.current_question_index]['correct'])
                    broadcast({
                        'type': 'answer_submitted',
                        'team_name': team_name,
                        'answer_index': answer_index,
                        'is_correct': is_correct,
                        'score': game_state.teams[i]['score']
                    })
                    if is_correct:
                        play_sound('correct')
                    else:
                        play_sound('wrong')
                break
    
    elif msg_type == 'get_state':
        send_current_state(client)

def send_current_question(client):
    if not game_state.quiz_active or game_state.current_question_index >= len(game_state.current_questions):
        return
    
    q = game_state.current_questions[game_state.current_question_index]
    elapsed_time = time.time() - game_state.question_start_time
    time_left = max(0, game_state.time_per_question - elapsed_time)
    
    data = {
        'type': 'question',
        'index': game_state.current_question_index,
        'total': len(game_state.current_questions),
        'question': q['question'],
        'options': q['options'],
        'correct': q['correct'],
        'time': game_state.time_per_question,
        'disabled_options': game_state.disabled_options,
        'time_left': time_left,
        'quiz_name': game_state.quiz_name,
        'teams': [{'name': t['name'], 'score': t['score']} for t in game_state.teams]
    }
    send_to_client(client, data)

def send_current_state(client):
    state = {
        'type': 'state_update',
        'quiz_active': game_state.quiz_active,
        'current_question': game_state.current_question_index if game_state.quiz_active else -1,
        'total_questions': len(game_state.current_questions),
        'teams': [{'name': t['name'], 'score': t['score']} for t in game_state.teams],
        'quiz_name': game_state.quiz_name
    }
    
    if game_state.quiz_active and game_state.current_question_index < len(game_state.current_questions):
        q = game_state.current_questions[game_state.current_question_index]
        elapsed_time = time.time() - game_state.question_start_time
        state['question'] = {
            'text': q['question'],
            'options': q['options'],
            'time_left': max(0, game_state.time_per_question - elapsed_time),
            'total_time': game_state.time_per_question,
            'disabled_options': game_state.disabled_options
        }
    
    send_to_client(client, state)

def send_to_client(client, data):
    try:
        client.send(json.dumps(data).encode('utf-8'))
    except:
        pass

def broadcast(data):
    for client in game_state.network_clients[:]:
        send_to_client(client, data)

def broadcast_question():
    if not game_state.network_enabled or not game_state.quiz_active:
        return
    q = game_state.current_questions[game_state.current_question_index]
    elapsed_time = time.time() - game_state.question_start_time
    time_left = max(0, game_state.time_per_question - elapsed_time)
    
    data = {
        'type': 'question', 
        'index': game_state.current_question_index, 
        'total': len(game_state.current_questions),
        'question': q['question'], 
        'options': q['options'], 
        'correct': q['correct'],
        'time': game_state.time_per_question, 
        'disabled_options': game_state.disabled_options,
        'time_left': time_left,
        'quiz_name': game_state.quiz_name,
        'teams': [{'name': t['name'], 'score': t['score']} for t in game_state.teams]
    }
    broadcast(data)

def broadcast_results():
    sorted_teams = sorted(game_state.teams, key=lambda x: x['score'], reverse=True)
    results = []
    for i, team in enumerate(sorted_teams, 1):
        results.append({
            'rank': i,
            'name': team['name'],
            'score': team['score'],
            'correct_count': team.get('correct_count', 0)
        })
    
    data = {
        'type': 'results',
        'results': results,
        'quiz_name': game_state.quiz_name
    }
    broadcast(data)

# ========== LIFELINE SISTEM ==========
def handle_50_50_lifeline():
    current_q = game_state.current_questions[game_state.current_question_index]
    correct = current_q['correct']
    wrong_options = [i for i in range(4) if i != correct]
    remove_options = random.sample(wrong_options, 2)
    game_state.disabled_options = remove_options
    game_state.lifelines['50_50']['used'] = True
    game_state.lifelines['50_50']['available'] = False
    
    if game_state.network_enabled:
        broadcast({'type': 'lifeline_used', 'lifeline': '50_50', 'disabled_options': remove_options})

def handle_skip_lifeline():
    game_state.reset_for_new_question()
    game_state.current_question_index += 1
    game_state.lifelines['skip']['used'] = True
    game_state.lifelines['skip']['available'] = False
    if game_state.current_question_index < len(game_state.current_questions):
        if game_state.network_enabled:
            broadcast_question()
    else:
        game_state.current = "results"
        broadcast_results()
    if game_state.multiplier_active:
        game_state.multiplier_rounds_left -= 1
        if game_state.multiplier_rounds_left <= 0:
            game_state.multiplier_active = False

def simulate_audience():
    current_q = game_state.current_questions[game_state.current_question_index]
    correct = current_q['correct']
    correct_percentage = random.randint(50, 80)
    remaining = 100 - correct_percentage
    other_options = [i for i in range(4) if i != correct]
    percentages = [0, 0, 0, 0]
    percentages[correct] = correct_percentage
    for i in other_options:
        if remaining > 0:
            p = random.randint(0, remaining)
            percentages[i] = p
            remaining -= p
    if remaining > 0:
        percentages[correct] += remaining
    game_state.audience_percentages = percentages
    game_state.lifelines['audience']['used'] = True
    game_state.lifelines['audience']['available'] = False
    return percentages

# ========== EXPORT IZVESTAJA U CSV ==========
def export_results_to_csv():
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"izvestaj_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([get_text('rank'), get_text('team'), get_text('points'), get_text('correct_answers'), get_text('fastest') + " (s)", get_text('avg_time') + " (s)"])
            
            sorted_teams = sorted(game_state.teams, key=lambda x: x['score'], reverse=True)
            for i, team in enumerate(sorted_teams, 1):
                correct_count = team.get('correct_count', 0)
                fastest = team.get('fastest_response', '-')
                if fastest is not None and fastest != '-':
                    fastest = f"{fastest:.2f}"
                else:
                    fastest = '-'
                response_times = [t for t in team.get('response_times_list', []) if t is not None]
                avg_time = sum(response_times) / len(response_times) if response_times else '-'
                if avg_time != '-':
                    avg_time = f"{avg_time:.2f}"
                
                writer.writerow([i, team['name'], team['score'], correct_count, fastest, avg_time])
        
        game_state.popup_text = f"Izveštaj sačuvan u {filename}"
        game_state.popup_until = time.time() + 3.0
        logging.info(f"Izveštaj sačuvan: {filename}")
        return True
    except Exception as e:
        logging.error(f"Greška pri exportu: {e}")
        return False

# ========== GUI FUNKCIJE ==========
def draw_button(text, rect, color=COLORS['button_primary'], hover_color=COLORS['button_primary_hover'], font=FONT_MEDIUM, modern=True):
    mouse_pos = pygame.mouse.get_pos()
    is_hover = rect.collidepoint(mouse_pos)
    current_color = hover_color if is_hover else color
    
    shadow_rect = rect.copy()
    shadow_rect.x += 3
    shadow_rect.y += 3
    pygame.draw.rect(screen, (0, 0, 0, 50), shadow_rect, border_radius=15)
    
    if modern:
        pygame.draw.rect(screen, current_color, rect, border_radius=15)
        if is_hover:
            pygame.draw.rect(screen, COLORS['gold_light'], rect, 3, border_radius=15)
        else:
            pygame.draw.rect(screen, COLORS['border_light'], rect, 2, border_radius=15)
    else:
        pygame.draw.rect(screen, current_color, rect, border_radius=12)
        if is_hover:
            pygame.draw.rect(screen, COLORS['gold_light'], rect, 3, border_radius=12)
        else:
            pygame.draw.rect(screen, COLORS['border_light'], rect, 2, border_radius=12)
    
    text_surf = font.render(text, True, COLORS['text_primary'])
    text_rect = text_surf.get_rect(center=rect.center)
    
    shadow_surf = font.render(text, True, (0, 0, 0, 30))
    shadow_rect_text = text_rect.copy()
    shadow_rect_text.x += 1
    shadow_rect_text.y += 1
    screen.blit(shadow_surf, shadow_rect_text)
    
    screen.blit(text_surf, text_rect)
    return is_hover

def draw_text(text, font, color, x, y, centered=False, shadow=True):
    text_surf = font.render(text, True, color)
    
    if shadow:
        shadow_surf = font.render(text, True, (0, 0, 0, 30))
        shadow_rect = text_surf.get_rect()
        if centered:
            shadow_rect.center = (x + 1, y + 1)
        else:
            shadow_rect.topleft = (x + 1, y + 1)
        screen.blit(shadow_surf, shadow_rect)
    
    if centered:
        text_rect = text_surf.get_rect(center=(x, y))
        screen.blit(text_surf, text_rect)
    else:
        screen.blit(text_surf, (x, y))

def draw_panel(rect, color=COLORS['bg_panel'], border_radius=15, gradient=False):
    if gradient:
        for i in range(rect.height):
            progress = i / rect.height
            r = int(color[0] + (COLORS['bg_panel_light'][0] - color[0]) * progress)
            g = int(color[1] + (COLORS['bg_panel_light'][1] - color[1]) * progress)
            b = int(color[2] + (COLORS['bg_panel_light'][2] - color[2]) * progress)
            line_rect = pygame.Rect(rect.x, rect.y + i, rect.width, 1)
            pygame.draw.rect(screen, (r, g, b), line_rect)
    else:
        pygame.draw.rect(screen, color, rect, border_radius=border_radius)
    
    pygame.draw.rect(screen, COLORS['border'], rect, 2, border_radius=border_radius)

def draw_input_field(rect, text, active=False, placeholder="", font=FONT_SMALL):
    color = COLORS['gold_light'] if active else COLORS['border']
    pygame.draw.rect(screen, COLORS['bg_panel_light'], rect, border_radius=10)
    pygame.draw.rect(screen, color, rect, 3 if active else 2, border_radius=10)
    
    display_text = text if text else placeholder
    text_color = COLORS['text_primary'] if text else COLORS['text_muted']
    text_surf = font.render(display_text, True, text_color)
    text_rect = text_surf.get_rect(midleft=(rect.x + 15, rect.centery))
    screen.blit(text_surf, text_rect)
    
    if active and int(time.time() * 2) % 2 == 0:
        cursor_x = rect.x + 15 + text_surf.get_width() + 2
        pygame.draw.line(screen, COLORS['gold_light'], (cursor_x, rect.y + 8), (cursor_x, rect.y + rect.height - 8), 2)

def draw_scroll_bar(scroll_area, content_height, scroll_offset, max_offset, bar_type=""):
    if content_height <= scroll_area.height:
        return scroll_offset, False
    
    visible_ratio = scroll_area.height / content_height
    handle_height = max(30, scroll_area.height * visible_ratio)
    scroll_range = max_offset
    if scroll_range > 0:
        handle_y = scroll_area.y + (scroll_offset / max_offset) * (scroll_area.height - handle_height)
    else:
        handle_y = scroll_area.y
    
    bar_rect = pygame.Rect(scroll_area.right - 12, scroll_area.y, 12, scroll_area.height)
    pygame.draw.rect(screen, COLORS['bg_panel'], bar_rect, border_radius=6)
    pygame.draw.rect(screen, COLORS['border'], bar_rect, 1, border_radius=6)
    
    handle_rect = pygame.Rect(scroll_area.right - 12, handle_y, 12, handle_height)
    pygame.draw.rect(screen, COLORS['button_primary'], handle_rect, border_radius=6)
    
    scroll_clicked = False
    new_offset = scroll_offset
    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()[0]
    
    if mouse_pressed:
        if bar_rect.collidepoint(mouse_pos) and not game_state.dragging_scroll_bar:
            if handle_rect.collidepoint(mouse_pos):
                game_state.dragging_scroll_bar = True
                game_state.dragging_scroll_bar_type = bar_type
                game_state.drag_start_y = mouse_pos[1]
                game_state.scroll_start_offset = scroll_offset
            else:
                relative_y = mouse_pos[1] - scroll_area.y
                new_offset = int((relative_y / scroll_area.height) * max_offset)
                new_offset = max(0, min(max_offset, new_offset))
                scroll_clicked = True
    
    if game_state.dragging_scroll_bar and game_state.dragging_scroll_bar_type == bar_type:
        if mouse_pressed:
            mouse_y = mouse_pos[1]
            delta_y = mouse_y - game_state.drag_start_y
            scroll_delta = (delta_y / scroll_area.height) * max_offset
            new_offset = int(max(0, min(max_offset, game_state.scroll_start_offset + scroll_delta)))
            scroll_clicked = True
        else:
            game_state.dragging_scroll_bar = False
            game_state.dragging_scroll_bar_type = ""
    
    return new_offset, scroll_clicked

# ========== QR KOD FUNKCIJA ==========
def generate_qr_code(data):
    if not QR_AVAILABLE:
        return None
    try:
        qr = qrcode.QRCode(box_size=5, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        qr_surface = pygame.image.load(img_bytes)
        return pygame.transform.scale(qr_surface, (180, 180))
    except:
        return None

# ========== RENDER CLIENT FILES ==========
def create_render_files():
    app_json = {
        "name": "Pub Kviz Master",
        "description": "Profesionalni sistem za vođenje pub kvizova",
        "repository": "https://github.com/yourusername/pub-kviz-master",
        "keywords": ["pub quiz", "kviz", "takmicenje", "game"],
        "env": {
            "PORT": {
                "description": "Port na kome radi server",
                "value": "65432"
            }
        },
        "buildpacks": [
            {"url": "heroku/python"}
        ]
    }
    
    app_js = """
// ========== PUB KVIZ MASTER - RENDER KLIJENT ==========
class PubKvizClient {
    constructor() {
        this.socket = null;
        this.teamName = null;
        this.playerName = null;
        this.currentQuestion = null;
        this.timerInterval = null;
        this.canBuzz = false;
        this.canAnswer = false;
        this.quizActive = false;
        this.teams = [];
        this.score = 0;
        this.correctCount = 0;
        this.questionStartTime = 0;
        this.disabledOptions = [];
        this.connected = false;
        
        this.joinPanel = document.getElementById('joinPanel');
        this.quizPanel = document.getElementById('quizPanel');
        this.resultsPanel = document.getElementById('resultsPanel');
        this.teamNameInput = document.getElementById('teamNameInput');
        this.playerNameInput = document.getElementById('playerNameInput');
        this.statusDiv = document.getElementById('status');
        this.quizTitle = document.getElementById('quizTitle');
        this.questionArea = document.getElementById('questionArea');
        this.leaderboardArea = document.getElementById('leaderboardArea');
        this.resultsArea = document.getElementById('resultsArea');
        
        this.init();
    }
    
    init() {
        document.getElementById('joinBtn').addEventListener('click', () => this.joinGame());
        document.getElementById('buzzBtn').addEventListener('click', () => this.buzz());
        
        document.getElementById('teamNameInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.joinGame();
        });
        document.getElementById('playerNameInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.joinGame();
        });
        
        this.autoConnect();
    }
    
    autoConnect() {
        const savedTeam = localStorage.getItem('pubKvizTeam');
        const savedPlayer = localStorage.getItem('pubKvizPlayer');
        if (savedTeam && savedPlayer) {
            this.teamNameInput.value = savedTeam;
            this.playerNameInput.value = savedPlayer;
            setTimeout(() => this.joinGame(), 1000);
        }
    }
    
    getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname;
        const port = window.location.port || '65432';
        return `${protocol}//${host}:${port}`;
    }
    
    joinGame() {
        const teamName = this.teamNameInput.value.trim();
        const playerName = this.playerNameInput.value.trim();
        
        if (!teamName || teamName.length < 2) {
            this.showStatus('Ime tima mora imati najmanje 2 karaktera', 'error');
            return;
        }
        
        if (!playerName || playerName.length < 2) {
            this.showStatus('Vaše ime mora imati najmanje 2 karaktera', 'error');
            return;
        }
        
        this.teamName = teamName;
        this.playerName = playerName;
        
        localStorage.setItem('pubKvizTeam', teamName);
        localStorage.setItem('pubKvizPlayer', playerName);
        
        this.showStatus('Povezivanje sa serverom...', 'info');
        
        if (this.socket) {
            this.socket.close();
        }
        
        try {
            const wsUrl = this.getWebSocketUrl();
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = () => {
                this.connected = true;
                this.showStatus('✅ Povezani na server', 'success');
                this.socket.send(JSON.stringify({
                    type: 'client_login',
                    team_name: this.teamName,
                    player_name: this.playerName
                }));
            };
            
            this.socket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                } catch (e) {
                    console.error('Greška pri parsiranju poruke:', e);
                }
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket greška:', error);
                this.showStatus('❌ Greška pri povezivanju', 'error');
            };
            
            this.socket.onclose = () => {
                this.connected = false;
                this.showStatus('🔌 Konekcija prekinuta', 'error');
            };
        } catch (e) {
            this.showStatus('❌ Greška: ' + e.message, 'error');
        }
    }
    
    handleMessage(message) {
        console.log('Primljena poruka:', message.type);
        
        switch(message.type) {
            case 'login_success':
                this.showStatus('✅ Uspešno prijavljeni!', 'success');
                this.joinPanel.style.display = 'none';
                this.quizPanel.style.display = 'block';
                this.quizTitle.textContent = '🎯 ' + (message.quiz_name || 'Pub Kviz');
                document.getElementById('yourTeamName').textContent = this.teamName;
                break;
                
            case 'welcome':
                this.showStatus('📡 Povezani na server', 'success');
                break;
                
            case 'question':
                this.showQuestion(message);
                break;
                
            case 'teams_update':
            case 'participants_update':
                this.updateTeams(message.teams || []);
                break;
                
            case 'state_update':
                this.updateState(message);
                break;
                
            case 'buzz':
                this.onBuzz(message.team_name);
                break;
                
            case 'answer_submitted':
                this.onAnswerSubmitted(message);
                break;
                
            case 'lifeline_used':
                if (message.lifeline === '50_50' && message.disabled_options) {
                    this.disabledOptions = message.disabled_options;
                }
                break;
                
            case 'results':
                this.showResults(message.results);
                break;
                
            case 'error':
                this.showStatus('❌ ' + message.message, 'error');
                break;
                
            case 'ping':
                this.socket.send(JSON.stringify({type: 'pong'}));
                break;
                
            default:
                console.log('Nepoznata poruka:', message);
        }
    }
    
    showQuestion(data) {
        this.currentQuestion = data;
        this.canBuzz = true;
        this.canAnswer = false;
        this.disabledOptions = data.disabled_options || [];
        this.questionStartTime = Date.now();
        
        const qArea = this.questionArea;
        const timeLeft = Math.ceil(data.time_left || data.time || 15);
        
        let html = `
            <div class="question-container">
                <div class="question-header">
                    <span class="question-number">Pitanje ${data.index + 1}/${data.total}</span>
                    <span class="timer" id="questionTimer">${timeLeft}s</span>
                </div>
                <div class="question-text">${this.escapeHtml(data.question)}</div>
                <div class="options-grid" id="optionsGrid">
        `;
        
        data.options.forEach((option, idx) => {
            const disabled = this.disabledOptions.includes(idx);
            const letter = String.fromCharCode(65 + idx);
            html += `
                <div class="option ${disabled ? 'disabled' : ''}" 
                     data-index="${idx}" 
                     onclick="client.answer(${idx})">
                    <span class="option-letter">${letter}</span>
                    <span class="option-text">${this.escapeHtml(option)}</span>
                </div>
            `;
        });
        
        html += `
                </div>
                <button id="buzzBtn" class="buzz-button" onclick="client.buzz()">
                    🔔 BUZZ!
                </button>
                <div id="buzzStatus" class="buzz-status"></div>
            </div>
        `;
        
        qArea.innerHTML = html;
        
        if (this.timerInterval) clearInterval(this.timerInterval);
        let remaining = timeLeft;
        this.timerInterval = setInterval(() => {
            remaining--;
            const timerEl = document.getElementById('questionTimer');
            if (timerEl) {
                timerEl.textContent = remaining + 's';
                if (remaining <= 5) timerEl.style.color = '#ff4444';
                else timerEl.style.color = '#ffd700';
            }
            if (remaining <= 0) {
                clearInterval(this.timerInterval);
                this.endQuestion();
            }
        }, 1000);
        
        this.resultsPanel.style.display = 'none';
        this.quizPanel.style.display = 'block';
        
        if (data.teams) {
            this.updateTeams(data.teams);
        }
    }
    
    answer(answerIndex) {
        if (!this.canAnswer) {
            this.showBuzzStatus('⏳ Sačekajte da buzz-ujete prvo!', 'info');
            return;
        }
        
        if (this.disabledOptions.includes(answerIndex)) {
            this.showBuzzStatus('❌ Ova opcija je isključena!', 'error');
            return;
        }
        
        const responseTime = (Date.now() - this.questionStartTime) / 1000;
        this.canAnswer = false;
        
        this.socket.send(JSON.stringify({
            type: 'answer',
            team_name: this.teamName,
            answer_index: answerIndex,
            response_time: responseTime
        }));
        
        document.querySelectorAll('.option').forEach(el => {
            el.style.opacity = '0.5';
            el.style.cursor = 'default';
        });
    }
    
    buzz() {
        if (!this.canBuzz) {
            this.showBuzzStatus('⏳ Sačekajte malo pre nego što ponovo buzz-ujete', 'info');
            return;
        }
        
        this.canBuzz = false;
        document.getElementById('buzzBtn').disabled = true;
        this.showBuzzStatus('⏳ Čekamo odgovor...', 'info');
        
        this.socket.send(JSON.stringify({
            type: 'buzz',
            team_name: this.teamName
        }));
    }
    
    onBuzz(teamName) {
        if (teamName === this.teamName) {
            this.canAnswer = true;
            this.showBuzzStatus('✅ Vi ste buzz-ovali! Odaberite odgovor.', 'success');
            document.getElementById('buzzBtn').style.display = 'none';
            document.querySelectorAll('.option:not(.disabled)').forEach(el => {
                el.style.opacity = '1';
                el.style.cursor = 'pointer';
            });
        } else {
            this.showBuzzStatus('🔔 ' + teamName + ' je buzz-ovao!', 'info');
            this.canBuzz = false;
        }
    }
    
    onAnswerSubmitted(data) {
        if (data.team_name === this.teamName) {
            if (data.is_correct) {
                this.showBuzzStatus('✅ TAČNO! +' + (data.points || 10) + ' poena!', 'success');
                this.score += data.points || 10;
                this.correctCount++;
                document.querySelectorAll('.option').forEach(el => {
                    if (el.dataset.index == data.answer_index) {
                        el.style.backgroundColor = '#00cc44';
                    }
                });
            } else {
                this.showBuzzStatus('❌ NETAČNO! -' + (data.points || 5) + ' poena!', 'error');
                this.score -= data.points || 5;
                document.querySelectorAll('.option').forEach(el => {
                    if (el.dataset.index == data.answer_index) {
                        el.style.backgroundColor = '#cc4444';
                    }
                });
            }
            document.getElementById('yourScore').textContent = this.score;
        }
        
        if (data.is_correct !== undefined && this.currentQuestion) {
            const correctIdx = this.currentQuestion.correct;
            document.querySelectorAll('.option').forEach(el => {
                if (el.dataset.index == correctIdx && data.team_name !== this.teamName) {
                    el.style.backgroundColor = '#00cc44';
                }
            });
        }
    }
    
    endQuestion() {
        if (this.timerInterval) clearInterval(this.timerInterval);
        this.canBuzz = false;
        this.canAnswer = false;
        
        const qArea = this.questionArea;
        qArea.innerHTML = `
            <div class="waiting-container">
                <div class="waiting-icon">⏳</div>
                <div class="waiting-text">Čekamo sledeće pitanje...</div>
            </div>
        `;
        
        setTimeout(() => {
            this.canBuzz = true;
        }, 2000);
    }
    
    updateTeams(teams) {
        this.teams = teams || [];
        const lbArea = document.getElementById('leaderboardList');
        if (!lbArea) return;
        
        let html = '';
        const sorted = [...this.teams].sort((a, b) => (b.score || 0) - (a.score || 0));
        
        sorted.slice(0, 8).forEach((team, idx) => {
            const isMe = team.name === this.teamName;
            const medal = idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : (idx + 1) + '.';
            html += `
                <div class="leaderboard-item ${isMe ? 'me' : ''}">
                    <span class="rank">${medal}</span>
                    <span class="team-name">${this.escapeHtml(team.name)}</span>
                    <span class="team-score">${team.score || 0}</span>
                </div>
            `;
        });
        
        if (sorted.length === 0) {
            html = '<div class="no-teams">Nema prijavljenih timova</div>';
        }
        
        lbArea.innerHTML = html;
        
        const myTeam = this.teams.find(t => t.name === this.teamName);
        if (myTeam) {
            this.score = myTeam.score || 0;
            const scoreEl = document.getElementById('yourScore');
            if (scoreEl) scoreEl.textContent = this.score;
        }
    }
    
    updateState(state) {
        if (state.quiz_active && state.current_question >= 0) {
            this.quizActive = true;
            if (state.question) {
                const data = {
                    index: state.current_question,
                    total: state.total_questions,
                    question: state.question.text,
                    options: state.question.options,
                    time: state.question.total_time,
                    time_left: state.question.time_left,
                    disabled_options: state.question.disabled_options || [],
                    teams: state.teams
                };
                this.showQuestion(data);
            }
        } else {
            this.quizActive = false;
            this.quizPanel.style.display = 'block';
            this.questionArea.innerHTML = `
                <div class="waiting-container">
                    <div class="waiting-icon">🎯</div>
                    <div class="waiting-text">Čekamo početak kviza...</div>
                </div>
            `;
        }
        
        if (state.teams) {
            this.updateTeams(state.teams);
        }
    }
    
    showResults(results) {
        this.quizPanel.style.display = 'none';
        this.resultsPanel.style.display = 'block';
        
        let html = `
            <h2>🏆 KONAČNI REZULTATI 🏆</h2>
            <div class="results-list">
        `;
        
        results.forEach((team, idx) => {
            const medal = idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : (idx + 1) + '.';
            const isMe = team.name === this.teamName;
            html += `
                <div class="result-item ${isMe ? 'me' : ''}">
                    <span class="result-rank">${medal}</span>
                    <span class="result-name">${this.escapeHtml(team.name)}</span>
                    <span class="result-score">${team.score} poena</span>
                    <span class="result-correct">✅ ${team.correct_count || 0}</span>
                </div>
            `;
        });
        
        html += '</div>';
        
        const myResult = results.find(r => r.name === this.teamName);
        if (myResult) {
            html += `
                <div class="my-result">
                    <h3>📍 VAŠ REZULTAT</h3>
                    <div class="my-result-details">
                        <span>Tim: ${this.escapeHtml(myResult.name)}</span>
                        <span>Poeni: ${myResult.score}</span>
                        <span>Tačni odgovori: ${myResult.correct_count || 0}</span>
                    </div>
                </div>
            `;
        }
        
        this.resultsArea.innerHTML = html;
        this.addConfetti();
    }
    
    addConfetti() {
        const colors = ['#ffd700', '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ff6b6b'];
        const container = this.resultsPanel;
        
        for (let i = 0; i < 50; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * 100 + '%';
            confetti.style.top = '-10px';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.width = Math.random() * 8 + 4 + 'px';
            confetti.style.height = Math.random() * 8 + 4 + 'px';
            confetti.style.position = 'absolute';
            confetti.style.animation = 'confettiFall ' + (Math.random() * 3 + 2) + 's linear infinite';
            confetti.style.animationDelay = Math.random() * 2 + 's';
            confetti.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';
            container.appendChild(confetti);
        }
    }
    
    showBuzzStatus(message, type) {
        const el = document.getElementById('buzzStatus');
        if (el) {
            el.textContent = message;
            el.className = 'buzz-status ' + type;
            el.style.display = 'block';
        }
    }
    
    showStatus(message, type) {
        if (this.statusDiv) {
            this.statusDiv.textContent = message;
            this.statusDiv.className = 'status ' + type;
        }
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

let client = null;
document.addEventListener('DOMContentLoaded', () => {
    client = new PubKvizClient();
});
"""
    
    try:
        with open('app.js', 'w', encoding='utf-8') as f:
            f.write(app_js)
        logging.info("app.js kreiran")
    except Exception as e:
        logging.error(f"Greška pri kreiranju app.js: {e}")
    
    try:
        with open('app.json', 'w', encoding='utf-8') as f:
            json.dump(app_json, f, indent=2)
        logging.info("app.json kreiran")
    except Exception as e:
        logging.error(f"Greška pri kreiranju app.json: {e}")

# ========== SETUP EKRAN ==========
def setup_screen():
    global current_lang, all_questions, music_playing
    
    input_active = None
    quiz_name_input = game_state.quiz_name
    time_input = str(game_state.time_per_question)
    questions_input = str(game_state.num_questions)
    show_lang_menu = False
    
    if ARGS.demo:
        create_backup()
    
    while game_state.current == "setup":
        # === SVI RECT-OVI SE KREIRAJU SVAKI PUT ===
        input_rects = {
            "name": pygame.Rect(SCREEN_WIDTH//2 - 220, 240, 440, 55),
            "time": pygame.Rect(SCREEN_WIDTH//2 - 220, 340, 440, 55),
            "questions": pygame.Rect(SCREEN_WIDTH//2 - 220, 440, 440, 55)
        }
        network_rect = pygame.Rect(SCREEN_WIDTH//2 - 220, 540, 30, 30)
        lang_button_rect = pygame.Rect(SCREEN_WIDTH - 240, 20, 200, 45)
        next_rect = pygame.Rect(SCREEN_WIDTH//2 - 160, SCREEN_HEIGHT - 120, 320, 55)
        history_rect = pygame.Rect(SCREEN_WIDTH - 220, SCREEN_HEIGHT - 80, 190, 50)
        quick_rect = pygame.Rect(50, SCREEN_HEIGHT - 120, 180, 50)
        settings_rect = pygame.Rect(SCREEN_WIDTH//2 - 160, SCREEN_HEIGHT - 190, 320, 50)
        panel_rect = pygame.Rect(SCREEN_WIDTH//2 - 280, 140, 560, 480)
        
        # Pozadina
        for i in range(SCREEN_HEIGHT):
            progress = i / SCREEN_HEIGHT
            r = int(18 + (28 - 18) * progress)
            g = int(18 + (28 - 18) * progress)
            b = int(30 + (45 - 30) * progress)
            pygame.draw.line(screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))
        
        header_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 90)
        pygame.draw.rect(screen, COLORS['bg_panel'], header_rect)
        pygame.draw.line(screen, COLORS['border'], (0, 90), (SCREEN_WIDTH, 90), 2)
        
        draw_text(get_text('title'), FONT_XL, COLORS['gold_light'], SCREEN_WIDTH//2, 45, centered=True)
        draw_text(get_text('setup_subtitle'), FONT_MEDIUM, COLORS['text_secondary'], SCREEN_WIDTH//2, 110, centered=True)
        
        lang_color = COLORS['button_primary_hover'] if lang_button_rect.collidepoint(pygame.mouse.get_pos()) else COLORS['button_primary']
        pygame.draw.rect(screen, lang_color, lang_button_rect, border_radius=12)
        pygame.draw.rect(screen, COLORS['gold_light'], lang_button_rect, 2, border_radius=12)
        draw_text(f"🌐 {current_lang.upper()}", FONT_MEDIUM, COLORS['text_primary'], lang_button_rect.centerx, lang_button_rect.centery, centered=True)
        
        if show_lang_menu:
            menu_height = len(LANGUAGES) * 50
            menu_rect = pygame.Rect(lang_button_rect.x, lang_button_rect.bottom + 5, lang_button_rect.width, menu_height)
            pygame.draw.rect(screen, COLORS['bg_panel'], menu_rect, border_radius=12)
            pygame.draw.rect(screen, COLORS['border'], menu_rect, 2, border_radius=12)
            for i, lang in enumerate(LANGUAGES.keys()):
                item_rect = pygame.Rect(menu_rect.x + 5, menu_rect.y + i * 50 + 5, menu_rect.width - 10, 40)
                if item_rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(screen, COLORS['bg_hover'], item_rect, border_radius=8)
                draw_text(lang.upper(), FONT_MEDIUM, COLORS['text_primary'], item_rect.centerx, item_rect.centery, centered=True)
        
        draw_panel(panel_rect, gradient=True)
        
        labels = [get_text('quiz_name'), get_text('time_per_q'), get_text('num_questions')]
        values = [quiz_name_input, time_input, questions_input]
        keys = ["name", "time", "questions"]
        
        for i, (label, value, key) in enumerate(zip(labels, values, keys)):
            y = 200 + i * 100
            draw_text(label, FONT_MEDIUM, COLORS['text_secondary'], SCREEN_WIDTH//2 - 240, y - 5)
            rect = input_rects[key]
            draw_input_field(rect, value, input_active == key, f"Unesite {label.lower()}")
        
        draw_text(get_text('online'), FONT_MEDIUM, COLORS['text_secondary'], SCREEN_WIDTH//2 - 240, 548)
        pygame.draw.rect(screen, COLORS['bg_panel_light'], network_rect, border_radius=8)
        if game_state.network_enabled:
            pygame.draw.rect(screen, COLORS['green'], network_rect, border_radius=8)
            pygame.draw.rect(screen, COLORS['gold_light'], network_rect, 2, border_radius=8)
            pygame.draw.line(screen, COLORS['text_primary'], (network_rect.x + 6, network_rect.y + 15), (network_rect.x + 13, network_rect.y + 22), 3)
            pygame.draw.line(screen, COLORS['text_primary'], (network_rect.x + 13, network_rect.y + 22), (network_rect.x + 24, network_rect.y + 6), 3)
        else:
            pygame.draw.rect(screen, COLORS['button_disabled'], network_rect, border_radius=8)
            pygame.draw.rect(screen, COLORS['border'], network_rect, 2, border_radius=8)
        
        if game_state.network_enabled:
            draw_text("🔗 Server aktivan", FONT_XS, COLORS['green'], network_rect.x + 50, network_rect.y + 18)
        else:
            draw_text("🔌 Server neaktivan", FONT_XS, COLORS['text_muted'], network_rect.x + 50, network_rect.y + 18)
        
        if draw_button(get_text('settings'), settings_rect, COLORS['button_primary'], COLORS['button_primary_hover']):
            settings_screen()
        
        if draw_button(get_text('quick_quiz'), quick_rect, COLORS['button_success'], COLORS['button_success_hover'], FONT_MEDIUM):
            game_state.quiz_name = "Brzi kviz"
            game_state.time_per_question = 15
            game_state.num_questions = 10
            all_questions = load_questions_by_language(current_lang)
            game_state.teams = []
            for i in range(5):
                game_state.teams.append({
                    'name': f'Tim{i+1}', 
                    'members': [], 
                    'player_name': f'Igrač{i+1}',
                    'score': 0,
                    'answers': [None] * 10, 
                    'response_times': [None] * 10,
                    'client': None, 
                    'correct_count': 0, 
                    'fastest_response': None, 
                    'response_times_list': []
                })
            game_state.reset_for_new_quiz()
            if len(all_questions) >= 10:
                indices = random.sample(range(len(all_questions)), 10)
            else:
                indices = list(range(len(all_questions)))
            game_state.current_questions = [all_questions[idx] for idx in indices]
            game_state.num_questions = len(game_state.current_questions)
            game_state.quiz_active = True
            game_state.question_start_time = time.time()
            game_state.quiz_start_time = time.time()
            if game_state.active_team_index == -1 and len(game_state.teams) > 0:
                game_state.active_team_index = 0
            game_state.current = "quiz"
            if game_state.network_enabled:
                broadcast_question()
                broadcast({'type': 'quiz_start', 'quiz_name': game_state.quiz_name})
        
        if draw_button(get_text('next'), next_rect, COLORS['button_success'], COLORS['button_success_hover'], FONT_MEDIUM):
            if quiz_name_input and time_input.isdigit() and questions_input.isdigit():
                game_state.quiz_name = InputValidator.sanitize_text(quiz_name_input)
                game_state.time_per_question = max(1, int(time_input))
                game_state.num_questions = max(1, int(questions_input))
                all_questions = load_questions_by_language(current_lang)
                if len(all_questions) < game_state.num_questions:
                    game_state.popup_text = f"Nema dovoljno pitanja! (ima: {len(all_questions)}, treba: {game_state.num_questions})"
                    game_state.popup_until = time.time() + 3.0
                else:
                    if game_state.network_enabled:
                        if start_server():
                            game_state.current = "team_registration"
                            broadcast({'type': 'registration_open', 'quiz_name': game_state.quiz_name})
                        else:
                            game_state.popup_text = "Greška pri pokretanju servera!"
                            game_state.popup_until = time.time() + 3.0
                    else:
                        game_state.current = "team_registration"
            else:
                game_state.popup_text = "Popunite sva polja ispravno!"
                game_state.popup_until = time.time() + 2.0
        
        if draw_button(get_text('history'), history_rect, COLORS['purple'], (180, 100, 210), FONT_MEDIUM):
            load_history()
            game_state.current = "history"
        
        draw_text("🔹 Popunite sva polja za nastavak", FONT_XS, COLORS['text_muted'], SCREEN_WIDTH//2, SCREEN_HEIGHT - 60, centered=True)
        
        if getattr(game_state, 'popup_until', 0) > time.time():
            popup_surf = FONT_MEDIUM.render(game_state.popup_text, True, COLORS['text_primary'])
            popup_rect = popup_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
            pygame.draw.rect(screen, COLORS['bg_panel'], popup_rect.inflate(40, 30), border_radius=15)
            pygame.draw.rect(screen, COLORS['gold_light'], popup_rect.inflate(40, 30), 3, border_radius=15)
            screen.blit(popup_surf, popup_rect)
        
        if ARGS.demo:
            demo_surf = FONT_SMALL.render("🔹 DEMO VERZIJA - Ograničeno na 5 pitanja", True, COLORS['orange'])
            demo_rect = demo_surf.get_rect(center=(SCREEN_WIDTH//2, 25))
            screen.blit(demo_surf, demo_rect)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_server()
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.VIDEORESIZE:
                pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                continue
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if lang_button_rect.collidepoint((mx, my)):
                    show_lang_menu = not show_lang_menu
                elif show_lang_menu:
                    menu_rect = pygame.Rect(lang_button_rect.x, lang_button_rect.bottom + 5, lang_button_rect.width, len(LANGUAGES) * 50)
                    for i, lang in enumerate(LANGUAGES.keys()):
                        item_rect = pygame.Rect(menu_rect.x + 5, menu_rect.y + i * 50 + 5, menu_rect.width - 10, 40)
                        if item_rect.collidepoint((mx, my)):
                            set_language(lang)
                            all_questions = load_questions_by_language(current_lang)
                            show_lang_menu = False
                            break
                    else:
                        show_lang_menu = False
                elif network_rect.collidepoint((mx, my)):
                    game_state.network_enabled = not game_state.network_enabled
                    if not game_state.network_enabled:
                        stop_server()
                else:
                    for key, rect in input_rects.items():
                        if rect.collidepoint((mx, my)):
                            input_active = key
                            break
                    else:
                        input_active = None
            
            if event.type == pygame.KEYDOWN and input_active:
                if input_active == "name":
                    if event.key == pygame.K_BACKSPACE:
                        quiz_name_input = quiz_name_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        input_active = None
                    else:
                        if len(quiz_name_input) < 30 and event.unicode.isprintable():
                            quiz_name_input += event.unicode
                elif input_active == "time":
                    if event.key == pygame.K_BACKSPACE:
                        time_input = time_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        input_active = None
                    elif event.unicode.isdigit():
                        if len(time_input) < 3:
                            time_input += event.unicode
                elif input_active == "questions":
                    if event.key == pygame.K_BACKSPACE:
                        questions_input = questions_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        input_active = None
                    elif event.unicode.isdigit():
                        if len(questions_input) < 3:
                            questions_input += event.unicode
        
        pygame.display.flip()
        clock.tick(60)

# ========== TEAM REGISTRATION SCREEN ==========
def team_registration_screen():
    global all_questions, music_playing
    
    if music_playing:
        pygame.mixer.music.unpause()
    
    current_team = {"name": "", "members": ["", "", "", "", "", ""], "player_name": ""}
    editing_member = None
    scroll_offset_teams = 0
    max_visible_teams = 7
    
    while game_state.current == "team_registration":
        # === SVI RECT-OVI SE KREIRAJU SVAKI PUT ===
        k_button_rect = pygame.Rect(SCREEN_WIDTH - 80, 20, 60, 60)
        left_panel = pygame.Rect(40, 100, 450, SCREEN_HEIGHT - 180)
        right_panel = pygame.Rect(510, 100, SCREEN_WIDTH - 550, SCREEN_HEIGHT - 180)
        team_name_rect = pygame.Rect(right_panel.x + 180, right_panel.y + 72, right_panel.width - 210, 45)
        player_name_rect = pygame.Rect(right_panel.x + 180, right_panel.y + 132, right_panel.width - 210, 45)
        
        member_rects = []
        for row in range(3):
            for col in range(2):
                i = row * 2 + col
                x = right_panel.x + 30 + col * (right_panel.width//2 - 40)
                y = right_panel.y + 230 + row * 50
                rect = pygame.Rect(x + 30, y, right_panel.width//2 - 70, 40)
                member_rects.append(rect)
        
        button_y = right_panel.bottom - 70
        add_rect = pygame.Rect(right_panel.x + 20, button_y, 200, 50)
        start_rect = pygame.Rect(right_panel.x + 240, button_y, 200, 50)
        back_rect = pygame.Rect(right_panel.x + 460, button_y, 180, 50)
        quick_register_rect = pygame.Rect(right_panel.x + 20, button_y - 65, 200, 45)
        
        # Pozadina
        for i in range(SCREEN_HEIGHT):
            progress = i / SCREEN_HEIGHT
            r = int(18 + (28 - 18) * progress)
            g = int(18 + (28 - 18) * progress)
            b = int(30 + (45 - 30) * progress)
            pygame.draw.line(screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))
        
        header_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 80)
        pygame.draw.rect(screen, COLORS['bg_panel'], header_rect)
        pygame.draw.line(screen, COLORS['border'], (0, 80), (SCREEN_WIDTH, 80), 2)
        
        draw_text(f"{get_text('title')}: {game_state.quiz_name}", FONT_LARGE, COLORS['gold_light'], SCREEN_WIDTH//2, 40, centered=True)
        
        k_color = COLORS['button_danger'] if not k_button_rect.collidepoint(pygame.mouse.get_pos()) else COLORS['button_danger_hover']
        pygame.draw.rect(screen, k_color, k_button_rect, border_radius=12)
        pygame.draw.rect(screen, COLORS['gold_light'], k_button_rect, 3, border_radius=12)
        draw_text("K", FONT_XL, COLORS['text_primary'], k_button_rect.centerx, k_button_rect.centery, centered=True)
        
        if k_button_rect.collidepoint(pygame.mouse.get_pos()):
            tooltip_rect = pygame.Rect(k_button_rect.x - 220, k_button_rect.y + 70, 280, 40)
            pygame.draw.rect(screen, COLORS['bg_panel'], tooltip_rect, border_radius=8)
            pygame.draw.rect(screen, COLORS['gold_light'], tooltip_rect, 2, border_radius=8)
            draw_text("Pokreni kviz sa custom pitanjima", FONT_XS, COLORS['text_primary'], tooltip_rect.centerx, tooltip_rect.centery, centered=True)
        
        draw_panel(left_panel, gradient=True)
        draw_text(get_text('teams_registered'), FONT_LARGE, COLORS['gold_light'], left_panel.x + 20, left_panel.y + 20)
        draw_text(f"{len(game_state.teams)} timova", FONT_SMALL, COLORS['text_muted'], left_panel.x + left_panel.width - 80, left_panel.y + 28)
        
        if game_state.teams:
            start_idx = scroll_offset_teams
            end_idx = min(start_idx + max_visible_teams, len(game_state.teams))
            
            for i in range(start_idx, end_idx):
                team = game_state.teams[i]
                y = left_panel.y + 70 + (i - start_idx) * 55
                team_rect = pygame.Rect(left_panel.x + 15, y, left_panel.width - 30, 45)
                
                if game_state.active_team_index != -1 and i == game_state.active_team_index:
                    pygame.draw.rect(screen, COLORS['bg_hover'], team_rect, border_radius=8)
                    pygame.draw.rect(screen, COLORS['gold_light'], team_rect, 2, border_radius=8)
                else:
                    pygame.draw.rect(screen, COLORS['bg_panel_light'], team_rect, border_radius=8)
                    pygame.draw.rect(screen, COLORS['border'], team_rect, 1, border_radius=8)
                
                draw_text(f"{i+1}. {team['name']}", FONT_SMALL, COLORS['text_primary'], team_rect.x + 15, team_rect.centery)
                member_count = len([m for m in team['members'] if m.strip()])
                player_name = team.get('player_name', '')
                status_text = f"👤 {player_name[:10]}" if player_name else f"👥 {member_count}"
                draw_text(status_text, FONT_XS, COLORS['text_muted'], team_rect.right - 80, team_rect.centery)
                
                if team.get('client'):
                    pygame.draw.circle(screen, COLORS['green'], (team_rect.right - 15, team_rect.centery), 6)
            
            if len(game_state.teams) > max_visible_teams:
                max_scroll = len(game_state.teams) - max_visible_teams
                scroll_area = pygame.Rect(left_panel)
                new_offset, _ = draw_scroll_bar(scroll_area, len(game_state.teams) * 55 + 70, scroll_offset_teams, max_scroll, "team_list")
                scroll_offset_teams = new_offset
        else:
            draw_text("Nema prijavljenih timova", FONT_MEDIUM, COLORS['text_muted'], left_panel.centerx, left_panel.centery, centered=True)
        
        draw_panel(right_panel, gradient=True)
        draw_text(get_text('new_team'), FONT_LARGE, COLORS['gold_light'], right_panel.x + 20, right_panel.y + 20)
        
        draw_text(get_text('team_name'), FONT_MEDIUM, COLORS['text_secondary'], right_panel.x + 30, right_panel.y + 80)
        draw_input_field(team_name_rect, current_team['name'], editing_member == "team_name", "Unesite ime tima")
        
        draw_text(get_text('player_name'), FONT_MEDIUM, COLORS['text_secondary'], right_panel.x + 30, right_panel.y + 140)
        draw_input_field(player_name_rect, current_team['player_name'], editing_member == "player_name", "Unesite vaše ime")
        
        draw_text(get_text('members'), FONT_MEDIUM, COLORS['text_secondary'], right_panel.x + 30, right_panel.y + 200)
        
        for row in range(3):
            for col in range(2):
                i = row * 2 + col
                x = right_panel.x + 30 + col * (right_panel.width//2 - 40)
                y = right_panel.y + 230 + row * 50
                draw_text(f"{i+1}.", FONT_XS, COLORS['text_muted'], x, y + 15)
                draw_input_field(member_rects[i], current_team['members'][i], editing_member == i, f"Član {i+1}")
        
        if draw_button(get_text('add_team'), add_rect, COLORS['button_primary'], COLORS['button_primary_hover']):
            if current_team['name'].strip() and current_team['player_name'].strip():
                if not InputValidator.validate_team_name(current_team['name']):
                    game_state.popup_text = "Ime tima mora imati 2-30 karaktera!"
                    game_state.popup_until = time.time() + 2.0
                elif not InputValidator.validate_player_name(current_team['player_name']):
                    game_state.popup_text = "Ime igrača mora imati 2-50 karaktera!"
                    game_state.popup_until = time.time() + 2.0
                else:
                    game_state.teams.append({
                        'name': current_team['name'].strip(),
                        'members': current_team['members'].copy(),
                        'player_name': current_team['player_name'].strip(),
                        'score': 0,
                        'answers': [None] * game_state.num_questions,
                        'response_times': [None] * game_state.num_questions,
                        'client': None,
                        'correct_count': 0,
                        'fastest_response': None,
                        'response_times_list': []
                    })
                    current_team = {"name": "", "members": ["", "", "", "", "", ""], "player_name": ""}
                    if game_state.network_enabled:
                        broadcast({'type': 'teams_update', 'teams': [{'name': t['name'], 'score': t['score']} for t in game_state.teams]})
                    logging.info(f"Tim dodat: {current_team['name']}")
            else:
                game_state.popup_text = "Unesite ime tima i vaše ime!"
                game_state.popup_until = time.time() + 2.0
        
        if draw_button(get_text('start_quiz'), start_rect, COLORS['button_success'], COLORS['button_success_hover']):
            if len(game_state.teams) >= 1:
                if len(all_questions) >= game_state.num_questions:
                    game_state.reset_for_new_quiz()
                    indices = random.sample(range(len(all_questions)), game_state.num_questions)
                    game_state.current_questions = [all_questions[idx] for idx in indices]
                    game_state.quiz_active = True
                    game_state.question_start_time = time.time()
                    game_state.quiz_start_time = time.time()
                    if game_state.active_team_index == -1 and len(game_state.teams) > 0:
                        game_state.active_team_index = 0
                    game_state.current = "quiz"
                    if game_state.network_enabled:
                        broadcast_question()
                        broadcast({'type': 'quiz_start', 'quiz_name': game_state.quiz_name})
                    logging.info(f"Kviz započet: {game_state.quiz_name}")
                else:
                    game_state.popup_text = f"Nema dovoljno pitanja! (ima: {len(all_questions)}, treba: {game_state.num_questions})"
                    game_state.popup_until = time.time() + 3.0
            else:
                game_state.popup_text = "Morate imati barem jedan tim!"
                game_state.popup_until = time.time() + 2.0
        
        if draw_button(get_text('back'), back_rect, COLORS['button_primary'], COLORS['button_primary_hover']):
            stop_server()
            game_state.current = "setup"
        
        if draw_button(get_text('quick_register'), quick_register_rect, COLORS['button_success'], COLORS['button_success_hover'], FONT_SMALL):
            anon_name = f"Tim{len(game_state.teams) + 1}"
            game_state.teams.append({
                'name': anon_name,
                'members': [],
                'player_name': f"Igrač{len(game_state.teams) + 1}",
                'score': 0,
                'answers': [None] * game_state.num_questions,
                'response_times': [None] * game_state.num_questions,
                'client': None,
                'correct_count': 0,
                'fastest_response': None,
                'response_times_list': []
            })
            if game_state.network_enabled:
                broadcast({'type': 'teams_update', 'teams': [{'name': t['name'], 'score': t['score']} for t in game_state.teams]})
        
        status_text = f"Prijavljeno timova: {len(game_state.teams)} | Broj pitanja: {game_state.num_questions} | Online: {'✅ DA' if game_state.network_enabled else '❌ NE'}"
        draw_text(status_text, FONT_XS, COLORS['text_secondary'], SCREEN_WIDTH//2, SCREEN_HEIGHT - 25, centered=True)
        
        if getattr(game_state, 'popup_until', 0) > time.time():
            popup_surf = FONT_MEDIUM.render(game_state.popup_text, True, COLORS['text_primary'])
            popup_rect = popup_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            pygame.draw.rect(screen, COLORS['bg_panel'], popup_rect.inflate(40, 30), border_radius=15)
            pygame.draw.rect(screen, COLORS['gold_light'], popup_rect.inflate(40, 30), 3, border_radius=15)
            screen.blit(popup_surf, popup_rect)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_server()
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.VIDEORESIZE:
                pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                continue
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if k_button_rect.collidepoint((mx, my)):
                    if len(game_state.custom_questions) >= 10:
                        game_state.custom_quiz_mode = True
                        game_state.num_questions = 10
                        if len(game_state.custom_questions) > 10:
                            indices = random.sample(range(len(game_state.custom_questions)), 10)
                            game_state.current_questions = [game_state.custom_questions[idx] for idx in indices]
                        else:
                            game_state.current_questions = game_state.custom_questions.copy()
                        game_state.reset_for_new_quiz()
                        game_state.quiz_active = True
                        game_state.question_start_time = time.time()
                        game_state.quiz_start_time = time.time()
                        if game_state.active_team_index == -1 and len(game_state.teams) > 0:
                            game_state.active_team_index = 0
                        game_state.current = "quiz"
                        if game_state.network_enabled:
                            broadcast_question()
                            broadcast({'type': 'quiz_start', 'quiz_name': f"CUSTOM: {game_state.quiz_name}"})
                    else:
                        game_state.popup_text = f"Nema dovoljno custom pitanja! (ima: {len(game_state.custom_questions)}, treba: 10)"
                        game_state.popup_until = time.time() + 3.0
                elif team_name_rect.collidepoint((mx, my)):
                    editing_member = "team_name"
                elif player_name_rect.collidepoint((mx, my)):
                    editing_member = "player_name"
                else:
                    for i, rect in enumerate(member_rects):
                        if rect.collidepoint((mx, my)):
                            editing_member = i
                            break
                    else:
                        editing_member = None
            
            if event.type == pygame.KEYDOWN and editing_member is not None:
                if editing_member == "team_name":
                    if event.key == pygame.K_BACKSPACE:
                        current_team['name'] = current_team['name'][:-1]
                    elif event.key == pygame.K_RETURN:
                        editing_member = "player_name"
                    elif event.unicode.isprintable() and len(current_team['name']) < 30:
                        current_team['name'] += event.unicode
                elif editing_member == "player_name":
                    if event.key == pygame.K_BACKSPACE:
                        current_team['player_name'] = current_team['player_name'][:-1]
                    elif event.key == pygame.K_RETURN:
                        editing_member = None
                    elif event.unicode.isprintable() and len(current_team['player_name']) < 50:
                        current_team['player_name'] += event.unicode
                else:
                    if event.key == pygame.K_BACKSPACE:
                        current_team['members'][editing_member] = current_team['members'][editing_member][:-1]
                    elif event.key == pygame.K_RETURN:
                        if editing_member < 5:
                            editing_member += 1
                        else:
                            editing_member = None
                    elif event.unicode.isprintable() and len(current_team['members'][editing_member]) < 30:
                        current_team['members'][editing_member] += event.unicode
            
            if event.type == pygame.MOUSEWHEEL:
                if left_panel.collidepoint(pygame.mouse.get_pos()):
                    scroll_offset_teams -= event.y
                    max_scroll = max(0, len(game_state.teams) - max_visible_teams)
                    scroll_offset_teams = max(0, min(scroll_offset_teams, max_scroll))
        
        pygame.display.flip()
        clock.tick(60)

# ========== SETTINGS SCREEN ==========
def settings_screen():
    global music_playing, music_volume
    
    running = True
    input_active = None
    
    points_correct_str = str(game_state.points_correct)
    points_incorrect_str = str(game_state.points_incorrect)
    admin_password_str = game_state.correction_password
    render_url_input = game_state.render_url
    
    while running:
        # === SVI RECT-OVI SE KREIRAJU SVAKI PUT ===
        panel_rect = pygame.Rect(SCREEN_WIDTH//2 - 300, 90, 600, 620)
        music_toggle_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, 200, 400, 50)
        volume_slider_rect = pygame.Rect(SCREEN_WIDTH//2 - 150, 270, 300, 20)
        render_url_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, 330, 400, 45)
        points_correct_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, 400, 400, 45)
        points_incorrect_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, 470, 400, 45)
        admin_password_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, 540, 400, 45)
        save_settings_rect = pygame.Rect(SCREEN_WIDTH//2 - 160, 610, 320, 50)
        back_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, 680, 200, 45)
        exit_rect = pygame.Rect(panel_rect.right - 120, panel_rect.y + 10, 100, 40)
        
        # Pozadina
        for i in range(SCREEN_HEIGHT):
            progress = i / SCREEN_HEIGHT
            r = int(18 + (28 - 18) * progress)
            g = int(18 + (28 - 18) * progress)
            b = int(30 + (45 - 30) * progress)
            pygame.draw.line(screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))
        
        header_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 70)
        pygame.draw.rect(screen, COLORS['bg_panel'], header_rect)
        pygame.draw.line(screen, COLORS['border'], (0, 70), (SCREEN_WIDTH, 70), 2)
        
        draw_text(get_text('settings'), FONT_XL, COLORS['gold_light'], SCREEN_WIDTH//2, 35, centered=True)
        draw_panel(panel_rect, gradient=True)
        
        music_text = get_text('music_on') if music_playing else get_text('music_off')
        music_color = COLORS['green'] if music_playing else COLORS['button_danger']
        if draw_button(f"🎵 {music_text}", music_toggle_rect, music_color, COLORS['button_primary_hover'] if music_playing else COLORS['button_danger_hover']):
            toggle_music()
        
        draw_text(f"{get_text('volume')}: {int(music_volume * 100)}%", FONT_MEDIUM, COLORS['text_secondary'], SCREEN_WIDTH//2, 255, centered=True)
        pygame.draw.rect(screen, COLORS['bg_panel_light'], volume_slider_rect, border_radius=10)
        pygame.draw.rect(screen, COLORS['button_primary'], (volume_slider_rect.x, volume_slider_rect.y, int(music_volume * volume_slider_rect.width), volume_slider_rect.height), border_radius=10)
        handle_rect = pygame.Rect(volume_slider_rect.x + int(music_volume * volume_slider_rect.width) - 10, volume_slider_rect.y - 8, 20, 36)
        pygame.draw.rect(screen, COLORS['gold_light'], handle_rect, border_radius=10)
        
        draw_text(get_text('render_url'), FONT_SMALL, COLORS['text_secondary'], SCREEN_WIDTH//2 - 180, 335)
        draw_input_field(render_url_rect, render_url_input, input_active == "render_url", "https://your-app.onrender.com")
        
        draw_text(get_text('points_correct'), FONT_SMALL, COLORS['text_secondary'], SCREEN_WIDTH//2 - 180, 405)
        draw_input_field(points_correct_rect, points_correct_str, input_active == "points_correct", "10")
        
        draw_text(get_text('points_incorrect'), FONT_SMALL, COLORS['text_secondary'], SCREEN_WIDTH//2 - 180, 475)
        draw_input_field(points_incorrect_rect, points_incorrect_str, input_active == "points_incorrect", "5")
        
        draw_text(get_text('admin_password'), FONT_SMALL, COLORS['text_secondary'], SCREEN_WIDTH//2 - 180, 545)
        display_password = "*" * len(admin_password_str) if admin_password_str else "Unesite lozinku"
        draw_input_field(admin_password_rect, display_password, input_active == "admin_password", "admin123")
        
        if draw_button(get_text('save_settings'), save_settings_rect, COLORS['button_success'], COLORS['button_success_hover']):
            try:
                if points_correct_str.isdigit():
                    game_state.points_correct = int(points_correct_str)
                if points_incorrect_str.isdigit():
                    game_state.points_incorrect = int(points_incorrect_str)
                if admin_password_str.strip():
                    game_state.correction_password = admin_password_str
                    save_admin_password(admin_password_str)
                game_state.render_url = render_url_input
                game_state.popup_text = "Podešavanja su sačuvana!"
                game_state.popup_until = time.time() + 2.0
                logging.info("Podešavanja sačuvana")
            except Exception as e:
                logging.error(f"Greška pri čuvanju podešavanja: {e}")
                game_state.popup_text = "Greška pri čuvanju!"
                game_state.popup_until = time.time() + 2.0
        
        if draw_button(get_text('exit'), exit_rect, COLORS['button_danger'], COLORS['button_danger_hover'], FONT_SMALL):
            stop_server()
            pygame.quit()
            sys.exit()
        
        if draw_button(get_text('back_settings'), back_rect, COLORS['button_primary'], COLORS['button_primary_hover']):
            running = False
        
        if getattr(game_state, 'popup_until', 0) > time.time():
            popup_surf = FONT_MEDIUM.render(game_state.popup_text, True, COLORS['text_primary'])
            popup_rect = popup_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            pygame.draw.rect(screen, COLORS['bg_panel'], popup_rect.inflate(40, 30), border_radius=15)
            pygame.draw.rect(screen, COLORS['gold_light'], popup_rect.inflate(40, 30), 3, border_radius=15)
            screen.blit(popup_surf, popup_rect)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_server()
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.VIDEORESIZE:
                pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                continue
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if volume_slider_rect.collidepoint((mx, my)):
                    volume = (mx - volume_slider_rect.x) / volume_slider_rect.width
                    volume = max(0.0, min(1.0, volume))
                    set_music_volume(volume)
                elif render_url_rect.collidepoint((mx, my)):
                    input_active = "render_url"
                elif points_correct_rect.collidepoint((mx, my)):
                    input_active = "points_correct"
                elif points_incorrect_rect.collidepoint((mx, my)):
                    input_active = "points_incorrect"
                elif admin_password_rect.collidepoint((mx, my)):
                    input_active = "admin_password"
                else:
                    input_active = None
            
            if event.type == pygame.KEYDOWN:
                if input_active == "render_url":
                    if event.key == pygame.K_BACKSPACE:
                        render_url_input = render_url_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        input_active = None
                    elif event.unicode.isprintable():
                        render_url_input += event.unicode
                elif input_active == "points_correct":
                    if event.key == pygame.K_BACKSPACE:
                        points_correct_str = points_correct_str[:-1]
                    elif event.key == pygame.K_RETURN:
                        if points_correct_str.isdigit():
                            game_state.points_correct = int(points_correct_str)
                        input_active = None
                    elif event.unicode.isdigit():
                        points_correct_str += event.unicode
                elif input_active == "points_incorrect":
                    if event.key == pygame.K_BACKSPACE:
                        points_incorrect_str = points_incorrect_str[:-1]
                    elif event.key == pygame.K_RETURN:
                        if points_incorrect_str.isdigit():
                            game_state.points_incorrect = int(points_incorrect_str)
                        input_active = None
                    elif event.unicode.isdigit():
                        points_incorrect_str += event.unicode
                elif input_active == "admin_password":
                    if event.key == pygame.K_BACKSPACE:
                        admin_password_str = admin_password_str[:-1]
                    elif event.key == pygame.K_RETURN:
                        if admin_password_str.strip():
                            game_state.correction_password = admin_password_str
                            save_admin_password(admin_password_str)
                        input_active = None
                    elif event.unicode.isprintable():
                        admin_password_str += event.unicode
                elif event.key == pygame.K_ESCAPE:
                    running = False
        
        pygame.display.flip()
        clock.tick(60)

# ========== QUIZ SCREEN ==========
def quiz_screen():
    global music_playing
    
    if music_playing:
        pygame.mixer.music.unpause()
    
    game_state.quiz_active = True
    quiz_title = f"{get_text('title')}: {game_state.quiz_name}"
    if game_state.custom_quiz_mode:
        quiz_title = f"CUSTOM KVIZ: {game_state.quiz_name}"
    
    while game_state.current == "quiz" and game_state.current_question_index < len(game_state.current_questions):
        current_q = game_state.current_questions[game_state.current_question_index]
        elapsed_time = time.time() - game_state.question_start_time
        time_left = max(0, game_state.time_per_question - elapsed_time)
        
        if not game_state.answer_submitted and time_left <= 0:
            game_state.current_question_index += 1
            if game_state.current_question_index < len(game_state.current_questions):
                game_state.reset_for_new_question()
                if not game_state.network_enabled and len(game_state.teams) > 0:
                    game_state.active_team_index = (game_state.active_team_index + 1) % len(game_state.teams)
                if game_state.network_enabled:
                    broadcast_question()
                if game_state.multiplier_active:
                    game_state.multiplier_rounds_left -= 1
                    if game_state.multiplier_rounds_left <= 0:
                        game_state.multiplier_active = False
                        game_state.popup_text = "Multiplier runda je završena!"
                        game_state.popup_until = time.time() + 2.0
                continue
            else:
                game_state.current = "results"
                broadcast_results()
                play_sound('applause')
                break
        
        # === SVI RECT-OVI SE KREIRAJU SVAKI PUT ===
        question_rect = pygame.Rect(40, 110, SCREEN_WIDTH - 80, 140)
        table_rect = pygame.Rect(SCREEN_WIDTH - 300, 110, 270, 430)
        next_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 70, 200, 50)
        multiplier_rect = pygame.Rect(SCREEN_WIDTH - 170, 560, 150, 45)
        
        # Pozadina
        for i in range(SCREEN_HEIGHT):
            progress = i / SCREEN_HEIGHT
            r = int(18 + (28 - 18) * progress)
            g = int(18 + (28 - 18) * progress)
            b = int(30 + (45 - 30) * progress)
            pygame.draw.line(screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))
        
        header_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 85)
        pygame.draw.rect(screen, COLORS['bg_panel'], header_rect)
        pygame.draw.line(screen, COLORS['border'], (0, 85), (SCREEN_WIDTH, 85), 2)
        
        draw_text(quiz_title, FONT_MEDIUM, COLORS['gold_light'], 30, 25)
        draw_text(f"Pitanje {game_state.current_question_index + 1}/{len(game_state.current_questions)}", 
                 FONT_MEDIUM, COLORS['text_secondary'], SCREEN_WIDTH//2, 25, centered=True)
        
        timer_color = COLORS['green'] if time_left > 5 else COLORS['orange'] if time_left > 2 else COLORS['red']
        timer_text = f"{get_text('time_left')} {int(time_left)}s"
        timer_surf = FONT_LARGE.render(timer_text, True, timer_color)
        timer_rect = timer_surf.get_rect(right=SCREEN_WIDTH - 30, top=20)
        screen.blit(timer_surf, timer_rect)
        
        progress_rect = pygame.Rect(SCREEN_WIDTH - 250, 65, 220, 8)
        progress_width = int(220 * (time_left / game_state.time_per_question))
        pygame.draw.rect(screen, COLORS['bg_panel_light'], progress_rect, border_radius=4)
        pygame.draw.rect(screen, timer_color, (progress_rect.x, progress_rect.y, progress_width, progress_rect.height), border_radius=4)
        
        if game_state.multiplier_active:
            draw_text(f"⭐ MULTIPLIER 3x AKTIVAN! ⭐", FONT_SMALL, COLORS['gold_light'], SCREEN_WIDTH//2, 70, centered=True)
        
        participants_count = sum(1 for t in game_state.teams if t.get('client') or (not game_state.network_enabled and t.get('name')))
        draw_text(f"{get_text('teams_participating')} {participants_count}", FONT_XS, COLORS['text_muted'], SCREEN_WIDTH - 300, 70)
        
        if game_state.active_team_index != -1 and game_state.teams:
            active_team = game_state.teams[game_state.active_team_index]
            draw_text(f"{get_text('active_team')} {active_team['name']}", FONT_LARGE, COLORS['gold_light'], SCREEN_WIDTH//2, 70, centered=True)
        
        draw_panel(question_rect, gradient=True)
        
        question_text = current_q['question']
        words = question_text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surf = FONT_MEDIUM.render(test_line, True, COLORS['text_primary'])
            if test_surf.get_width() < question_rect.width - 40:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        for i, line in enumerate(lines[:4]):
            draw_text(line, FONT_MEDIUM, COLORS['text_primary'], question_rect.x + 20, question_rect.y + 15 + i * 32)
        
        option_rects = []
        option_height = 75
        spacing = 15
        cols = 2
        col_width = (SCREEN_WIDTH - 100) // cols
        
        for i, option in enumerate(current_q['options']):
            if i in game_state.disabled_options:
                continue
            col = i % cols
            row = i // cols
            x = 40 + col * (col_width + 20)
            y = 280 + row * (option_height + spacing)
            rect = pygame.Rect(x, y, col_width, option_height)
            option_rects.append((rect, i))
            
            if game_state.answer_submitted and game_state.show_correct_answer:
                if i == current_q['correct']:
                    color = COLORS['green']
                    border_color = COLORS['green_light']
                elif i == game_state.selected_answer and i != current_q['correct']:
                    color = COLORS['red']
                    border_color = COLORS['red_light']
                else:
                    color = COLORS['bg_panel_light']
                    border_color = COLORS['border']
            elif i == game_state.selected_answer:
                color = COLORS['bg_hover']
                border_color = COLORS['gold_light']
            else:
                color = COLORS['bg_panel_light']
                border_color = COLORS['border']
            
            pygame.draw.rect(screen, color, rect, border_radius=12)
            pygame.draw.rect(screen, border_color, rect, 3, border_radius=12)
            
            letter = chr(65 + i)
            letter_surf = FONT_MEDIUM.render(letter + ")", True, COLORS['gold_light'])
            screen.blit(letter_surf, (rect.x + 15, rect.y + 8))
            
            if option:
                words = option.split()
                opt_lines = []
                current_opt_line = []
                for word in words:
                    test_line = ' '.join(current_opt_line + [word])
                    test_surf = FONT_SMALL.render(test_line, True, COLORS['text_primary'])
                    if test_surf.get_width() < rect.width - 80:
                        current_opt_line.append(word)
                    else:
                        opt_lines.append(' '.join(current_opt_line))
                        current_opt_line = [word]
                if current_opt_line:
                    opt_lines.append(' '.join(current_opt_line))
                for j, line in enumerate(opt_lines[:3]):
                    draw_text(line, FONT_SMALL, COLORS['text_primary'], rect.x + 55, rect.y + 8 + j * 24)
        
        for i in game_state.disabled_options:
            col = i % cols
            row = i // cols
            x = 40 + col * (col_width + 20)
            y = 280 + row * (option_height + spacing)
            rect = pygame.Rect(x, y, col_width, option_height)
            pygame.draw.rect(screen, COLORS['bg_panel_light'], rect, border_radius=12)
            pygame.draw.rect(screen, COLORS['border'], rect, 2, border_radius=12)
            letter = chr(65 + i)
            draw_text(f"{letter}) ???", FONT_MEDIUM, COLORS['text_muted'], rect.centerx, rect.centery, centered=True)
        
        lifeline_y = 560
        lifeline_width = 140
        lifeline_spacing = 10
        total_lifeline_width = sum(1 for l in game_state.lifelines.values() if l['available']) * (lifeline_width + lifeline_spacing) - lifeline_spacing
        start_x = (SCREEN_WIDTH - total_lifeline_width) // 2
        
        lifeline_idx = 0
        for key, lifeline in game_state.lifelines.items():
            if not lifeline['available']:
                continue
            x = start_x + lifeline_idx * (lifeline_width + lifeline_spacing)
            rect = pygame.Rect(x, lifeline_y, lifeline_width, 45)
            color = COLORS['button_disabled'] if lifeline['used'] else COLORS['button_primary']
            hover_color = COLORS['button_primary_hover'] if not lifeline['used'] else COLORS['button_disabled']
            if draw_button(lifeline['name'], rect, color, hover_color, FONT_SMALL):
                if not lifeline['used']:
                    if key == '50_50':
                        handle_50_50_lifeline()
                        if game_state.network_enabled:
                            broadcast({'type': 'lifeline_used', 'lifeline': '50_50', 'disabled_options': game_state.disabled_options})
                    elif key == 'skip':
                        handle_skip_lifeline()
                        return
                    elif key == 'audience':
                        game_state.use_audience_popup()
                        if game_state.network_enabled:
                            broadcast({'type': 'lifeline_used', 'lifeline': 'audience'})
                    elif key == 'hint':
                        game_state.use_hint_popup()
                        if game_state.network_enabled:
                            broadcast({'type': 'lifeline_used', 'lifeline': 'hint'})
            lifeline_idx += 1
        
        if draw_button("⭐ MULTIPLIER ⭐", multiplier_rect, COLORS['gold'], COLORS['orange'], FONT_SMALL):
            game_state.activate_multiplier_round(1)
            if game_state.network_enabled:
                broadcast({'type': 'multiplier_activated'})
        
        draw_panel(table_rect, gradient=True)
        draw_text(get_text('results'), FONT_SMALL, COLORS['gold_light'], table_rect.x + 20, table_rect.y + 12)
        
        sorted_teams = sorted(game_state.teams, key=lambda x: x['score'], reverse=True)
        for i, team in enumerate(sorted_teams[:7]):
            y = table_rect.y + 45 + i * 35
            is_active = game_state.active_team_index != -1 and game_state.teams[game_state.active_team_index]['name'] == team['name']
            color = COLORS['gold_light'] if is_active else COLORS['text_secondary']
            
            medal = ""
            if i == 0:
                medal = "🥇"
            elif i == 1:
                medal = "🥈"
            elif i == 2:
                medal = "🥉"
            else:
                medal = f"{i+1}."
            
            draw_text(f"{medal} {team['name'][:12]}", FONT_XS, color, table_rect.x + 15, y)
            score_color = COLORS['green'] if team['score'] >= 0 else COLORS['red']
            draw_text(f"{team['score']}", FONT_XS, score_color, table_rect.x + 230, y)
        
        if game_state.answer_submitted:
            if draw_button(get_text('next_question'), next_rect, COLORS['button_success'], COLORS['button_success_hover']):
                game_state.current_question_index += 1
                if game_state.current_question_index < len(game_state.current_questions):
                    game_state.reset_for_new_question()
                    if not game_state.network_enabled and len(game_state.teams) > 0:
                        game_state.active_team_index = (game_state.active_team_index + 1) % len(game_state.teams)
                    if game_state.network_enabled:
                        broadcast_question()
                    if game_state.multiplier_active:
                        game_state.multiplier_rounds_left -= 1
                        if game_state.multiplier_rounds_left <= 0:
                            game_state.multiplier_active = False
                            game_state.popup_text = "Multiplier runda je završena!"
                            game_state.popup_until = time.time() + 2.0
                else:
                    game_state.current = "results"
                    broadcast_results()
                    play_sound('applause')
        
        if getattr(game_state, 'popup_until', 0) > time.time():
            popup_surf = FONT_MEDIUM.render(game_state.popup_text, True, COLORS['text_primary'])
            popup_rect = popup_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            pygame.draw.rect(screen, COLORS['bg_panel'], popup_rect.inflate(40, 30), border_radius=15)
            pygame.draw.rect(screen, COLORS['gold_light'], popup_rect.inflate(40, 30), 3, border_radius=15)
            screen.blit(popup_surf, popup_rect)
        else:
            if game_state.popup_text:
                game_state.popup_text = ""
                game_state.popup_until = 0.0
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_server()
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.VIDEORESIZE:
                pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                continue
            
            if event.type == pygame.KEYDOWN:
                if game_state.quiz_active and game_state.answer_submitted:
                    if event.key == pygame.K_SPACE:
                        game_state.current_question_index += 1
                        if game_state.current_question_index < len(game_state.current_questions):
                            game_state.reset_for_new_question()
                            if not game_state.network_enabled and len(game_state.teams) > 0:
                                game_state.active_team_index = (game_state.active_team_index + 1) % len(game_state.teams)
                            if game_state.network_enabled:
                                broadcast_question()
                        else:
                            game_state.current = "results"
                            broadcast_results()
                            play_sound('applause')
                    elif event.key == pygame.K_m:
                        game_state.activate_multiplier_round(1)
                    elif event.key == pygame.K_r:
                        game_state.reset_for_new_question()
                    elif event.key == pygame.K_ESCAPE:
                        game_state.current = "results"
                        broadcast_results()
                
                if game_state.quiz_active and not game_state.answer_submitted:
                    if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                        game_state.time_per_question = min(game_state.time_per_question + 5, 60)
                    elif event.key == pygame.K_MINUS:
                        game_state.time_per_question = max(game_state.time_per_question - 5, 5)
                    elif pygame.K_1 <= event.key <= pygame.K_9:
                        team_index = event.key - pygame.K_1
                        if team_index < len(game_state.teams):
                            game_state.team_buzz(team_index)
                            if game_state.network_enabled:
                                broadcast({'type': 'buzz', 'team_index': team_index, 'team_name': game_state.teams[team_index]['name']})
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not game_state.answer_submitted:
                pos = event.pos
                for rect, idx in option_rects:
                    if rect.collidepoint(pos):
                        if idx in game_state.disabled_options:
                            break
                        response_time = time.time() - game_state.question_start_time
                        game_state.selected_answer = idx
                        if game_state.submit_answer(game_state.active_team_index, idx, response_time):
                            if game_state.network_enabled:
                                broadcast({
                                    'type': 'answer_submitted',
                                    'team_name': game_state.teams[game_state.active_team_index]['name'],
                                    'answer_index': idx,
                                    'is_correct': (idx == current_q['correct']),
                                    'score': game_state.teams[game_state.active_team_index]['score'],
                                    'points': game_state.points_correct if idx == current_q['correct'] else game_state.points_incorrect
                                })
                        break
        
        clock.tick(60)
    
    if game_state.current_question_index >= len(game_state.current_questions):
        game_state.current = "results"
        broadcast_results()
        play_sound('applause')

# ========== RESULTS SCREEN ==========
def results_screen():
    global music_playing
    
    if music_playing:
        pygame.mixer.music.pause()
    
    save_pressed = False
    save_clicked = False
    correction_input_active = False
    password_input_active = False
    
    while game_state.current == "results":
        # === SVI RECT-OVI SE KREIRAJU SVAKI PUT ===
        table_x = 80
        table_y = 150
        table_width = SCREEN_WIDTH - 160
        table_height = SCREEN_HEIGHT - 330
        visible_rows = min(15, len(game_state.teams))
        row_height = 40
        max_scroll = max(0, len(game_state.teams) - visible_rows)
        game_state.scroll_offset_results = max(0, min(game_state.scroll_offset_results, max_scroll))
        
        new_rect = pygame.Rect(80, SCREEN_HEIGHT - 150, 180, 50)
        save_rect = pygame.Rect(280, SCREEN_HEIGHT - 150, 180, 50)
        history_rect = pygame.Rect(480, SCREEN_HEIGHT - 150, 180, 50)
        question_rect = pygame.Rect(680, SCREEN_HEIGHT - 150, 180, 50)
        report_rect = pygame.Rect(880, SCREEN_HEIGHT - 150, 180, 50)
        k_button_rect = pygame.Rect(SCREEN_WIDTH - 100, SCREEN_HEIGHT - 150, 80, 50)
        
        # Pozadina
        for i in range(SCREEN_HEIGHT):
            progress = i / SCREEN_HEIGHT
            r = int(18 + (28 - 18) * progress)
            g = int(18 + (28 - 18) * progress)
            b = int(30 + (45 - 30) * progress)
            pygame.draw.line(screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))
        
        header_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 100)
        pygame.draw.rect(screen, COLORS['bg_panel'], header_rect)
        pygame.draw.line(screen, COLORS['border'], (0, 100), (SCREEN_WIDTH, 100), 2)
        
        title_text = get_text('results')
        if game_state.custom_quiz_mode:
            title_text = f"CUSTOM KVIZ - {title_text}"
        
        draw_text(title_text, FONT_XL, COLORS['gold_light'], SCREEN_WIDTH//2, 35, centered=True)
        draw_text(f"{game_state.quiz_name} - {datetime.now().strftime('%d.%m.%Y %H:%M')}", FONT_MEDIUM, COLORS['text_secondary'], SCREEN_WIDTH//2, 80, centered=True)
        
        draw_panel(pygame.Rect(table_x, table_y, table_width, table_height), gradient=True)
        
        header_y = table_y
        pygame.draw.rect(screen, COLORS['bg_panel_light'], (table_x, header_y, table_width, 45))
        
        headers = [get_text('rank'), get_text('team'), get_text('points'), get_text('correct_answers'), get_text('fastest'), get_text('avg_time')]
        header_widths = [80, 250, 120, 140, 120, 140]
        for i, (header, width) in enumerate(zip(headers, header_widths)):
            x = table_x + sum(header_widths[:i]) + 20
            draw_text(header, FONT_SMALL, COLORS['gold_light'], x, header_y + 22)
        
        sorted_teams = sorted(game_state.teams, key=lambda x: x['score'], reverse=True)
        for idx in range(visible_rows):
            list_idx = idx + game_state.scroll_offset_results
            if list_idx >= len(sorted_teams):
                break
            team = sorted_teams[list_idx]
            y = table_y + 55 + idx * row_height
            row_color = COLORS['bg_panel_light'] if idx % 2 == 0 else COLORS['bg_panel']
            pygame.draw.rect(screen, row_color, (table_x, y, table_width, row_height))
            
            if list_idx == 0:
                draw_text("🥇", FONT_MEDIUM, COLORS['gold_light'], table_x + 30, y + 10)
            elif list_idx == 1:
                draw_text("🥈", FONT_MEDIUM, COLORS['silver'], table_x + 30, y + 10)
            elif list_idx == 2:
                draw_text("🥉", FONT_MEDIUM, COLORS['bronze'], table_x + 30, y + 10)
            else:
                draw_text(f"{list_idx + 1}.", FONT_XS, COLORS['text_secondary'], table_x + 20, y + 10)
            
            draw_text(team['name'][:20], FONT_XS, COLORS['text_primary'], table_x + 100, y + 10)
            
            if game_state.correction_mode and game_state.selected_team_for_correction == list_idx and correction_input_active:
                score_rect = pygame.Rect(table_x + 350, y - 5, 100, 30)
                pygame.draw.rect(screen, COLORS['gold_light'], score_rect, 2, border_radius=5)
                draw_text(game_state.correction_input, FONT_XS, COLORS['text_primary'], table_x + 355, y + 5)
            else:
                score_color = COLORS['green'] if team['score'] >= 0 else COLORS['red']
                draw_text(f"{team['score']}", FONT_XS, score_color, table_x + 350, y + 10)
            
            correct_count = team.get('correct_count', 0)
            draw_text(str(correct_count), FONT_XS, COLORS['text_secondary'], table_x + 490, y + 10)
            
            fastest = team.get('fastest_response', '-')
            if fastest is not None and fastest != '-':
                fastest = f"{fastest:.1f}s"
            draw_text(str(fastest), FONT_XS, COLORS['text_secondary'], table_x + 610, y + 10)
            
            response_times = [t for t in team.get('response_times_list', []) if t is not None]
            avg_time = sum(response_times) / len(response_times) if response_times else '-'
            if avg_time != '-':
                avg_time = f"{avg_time:.1f}s"
            draw_text(str(avg_time), FONT_XS, COLORS['text_secondary'], table_x + 750, y + 10)
        
        if len(sorted_teams) > visible_rows:
            scroll_area = pygame.Rect(table_x, table_y, table_width, table_height)
            new_offset, scroll_clicked = draw_scroll_bar(scroll_area, len(sorted_teams) * row_height + 55, game_state.scroll_offset_results, max_scroll, "results")
            if scroll_clicked:
                game_state.scroll_offset_results = new_offset
        
        if draw_button(get_text('new_competition'), new_rect, COLORS['button_primary'], COLORS['button_primary_hover']):
            stop_server()
            game_state.teams = []
            game_state.current_questions = []
            game_state.current = "setup"
        
        if draw_button(get_text('save'), save_rect, COLORS['button_success'], COLORS['button_success_hover']):
            save_history()
            save_pressed = True
            save_clicked = True
            game_state.popup_text = "Rezultati su sačuvani!"
            game_state.popup_until = time.time() + 2.0
        
        if draw_button(get_text('history_title'), history_rect, COLORS['button_primary'], COLORS['button_primary_hover']):
            load_history()
            game_state.current = "history"
        
        if draw_button(get_text('enter_question'), question_rect, COLORS['blue'], COLORS['button_primary_hover']):
            game_state.question_input_mode = True
            question_input_screen()
        
        if draw_button(get_text('export'), report_rect, COLORS['purple'], (180, 100, 210)):
            export_results_to_csv()
        
        if draw_button("K", k_button_rect, COLORS['button_danger'], COLORS['button_danger_hover']):
            password_input_active = True
            game_state.correction_input = ""
        
        if password_input_active:
            password_rect = pygame.Rect(SCREEN_WIDTH - 280, SCREEN_HEIGHT - 150, 160, 50)
            pygame.draw.rect(screen, COLORS['bg_panel'], password_rect, border_radius=10)
            pygame.draw.rect(screen, COLORS['gold_light'], password_rect, 2, border_radius=10)
            display = "*" * len(game_state.correction_input)
            draw_text(display if display else "Lozinka", FONT_MEDIUM, COLORS['text_primary'], password_rect.centerx, password_rect.centery, centered=True)
        
        if correction_input_active and game_state.selected_team_for_correction >= 0:
            team = sorted_teams[game_state.selected_team_for_correction]
            correction_panel = pygame.Rect(SCREEN_WIDTH//2 - 250, SCREEN_HEIGHT//2 - 120, 500, 200)
            pygame.draw.rect(screen, COLORS['bg_panel'], correction_panel, border_radius=15)
            pygame.draw.rect(screen, COLORS['gold_light'], correction_panel, 3, border_radius=15)
            
            draw_text("KOREKCIJA POENA", FONT_MEDIUM, COLORS['gold_light'], correction_panel.centerx, correction_panel.y + 30, centered=True)
            draw_text(f"Tim: {team['name']}", FONT_MEDIUM, COLORS['text_secondary'], correction_panel.centerx, correction_panel.y + 75, centered=True)
            draw_text(f"Trenutni poeni: {team['score']}", FONT_MEDIUM, COLORS['text_secondary'], correction_panel.centerx, correction_panel.y + 115, centered=True)
            
            input_rect = pygame.Rect(correction_panel.centerx - 80, correction_panel.y + 145, 160, 40)
            pygame.draw.rect(screen, COLORS['bg_panel_light'], input_rect, border_radius=8)
            pygame.draw.rect(screen, COLORS['gold_light'], input_rect, 2, border_radius=8)
            draw_text(game_state.correction_input if game_state.correction_input else "Novi poeni", FONT_MEDIUM, COLORS['text_primary'], input_rect.centerx, input_rect.centery, centered=True)
            
            ok_rect = pygame.Rect(correction_panel.centerx - 110, correction_panel.bottom - 55, 100, 40)
            cancel_rect = pygame.Rect(correction_panel.centerx + 10, correction_panel.bottom - 55, 100, 40)
            
            if draw_button("OK", ok_rect, COLORS['button_success'], COLORS['button_success_hover']):
                if game_state.correction_input.strip():
                    try:
                        new_score = int(game_state.correction_input)
                        team_index = game_state.teams.index(team)
                        game_state.teams[team_index]['score'] = new_score
                        game_state.popup_text = f"Poeni za {team['name']} promenjeni na {new_score}"
                        game_state.popup_until = time.time() + 2.0
                    except:
                        game_state.popup_text = "Unesite ispravan broj!"
                        game_state.popup_until = time.time() + 2.0
                correction_input_active = False
                game_state.selected_team_for_correction = -1
                game_state.correction_input = ""
            
            if draw_button("OTKAŽI", cancel_rect, COLORS['button_danger'], COLORS['button_danger_hover']):
                correction_input_active = False
                game_state.selected_team_for_correction = -1
                game_state.correction_input = ""
        
        if save_pressed and save_clicked:
            draw_text("✅ Rezultati su sačuvani!", FONT_MEDIUM, COLORS['green'], SCREEN_WIDTH//2, SCREEN_HEIGHT - 80, centered=True)
        if game_state.correction_mode:
            draw_text("🔴 REŽIM KOREKCIJE AKTIVAN - Kliknite na red za promenu", FONT_SMALL, COLORS['red'], SCREEN_WIDTH//2, 130, centered=True)
        
        if getattr(game_state, 'popup_until', 0) > time.time():
            popup_surf = FONT_MEDIUM.render(game_state.popup_text, True, COLORS['text_primary'])
            popup_rect = popup_surf.get_rect(center=(SCREEN_WIDTH//2, 80))
            pygame.draw.rect(screen, COLORS['bg_panel'], popup_rect.inflate(40, 25), border_radius=12)
            pygame.draw.rect(screen, COLORS['gold_light'], popup_rect.inflate(40, 25), 2, border_radius=12)
            screen.blit(popup_surf, popup_rect)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_server()
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.VIDEORESIZE:
                pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                continue
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if game_state.correction_mode and not correction_input_active:
                    for i in range(visible_rows):
                        list_idx = i + game_state.scroll_offset_results
                        if list_idx >= len(sorted_teams):
                            break
                        y = table_y + 55 + i * row_height
                        row_rect = pygame.Rect(table_x, y, table_width, row_height)
                        if row_rect.collidepoint((mx, my)):
                            game_state.selected_team_for_correction = list_idx
                            correction_input_active = True
                            game_state.correction_input = ""
                            break
                
                if password_input_active:
                    password_rect = pygame.Rect(SCREEN_WIDTH - 280, SCREEN_HEIGHT - 150, 160, 50)
                    if password_rect.collidepoint((mx, my)):
                        pass
                    else:
                        if game_state.correction_input == game_state.correction_password:
                            game_state.correction_mode = True
                            game_state.popup_text = "Režim korekcije aktiviran!"
                            game_state.popup_until = time.time() + 2.0
                        elif game_state.correction_input:
                            game_state.popup_text = "Pogrešna lozinka!"
                            game_state.popup_until = time.time() + 2.0
                        game_state.correction_input = ""
                        password_input_active = False
                
                if save_rect.collidepoint((mx, my)):
                    save_pressed = True
            
            if event.type == pygame.KEYDOWN:
                if password_input_active:
                    if event.key == pygame.K_BACKSPACE:
                        game_state.correction_input = game_state.correction_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        if game_state.correction_input == game_state.correction_password:
                            game_state.correction_mode = True
                            game_state.popup_text = "Režim korekcije aktiviran!"
                            game_state.popup_until = time.time() + 2.0
                        elif game_state.correction_input:
                            game_state.popup_text = "Pogrešna lozinka!"
                            game_state.popup_until = time.time() + 2.0
                        game_state.correction_input = ""
                        password_input_active = False
                    elif event.unicode.isprintable():
                        if len(game_state.correction_input) < 20:
                            game_state.correction_input += event.unicode
                elif correction_input_active:
                    if event.key == pygame.K_BACKSPACE:
                        game_state.correction_input = game_state.correction_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        if game_state.correction_input.strip():
                            try:
                                new_score = int(game_state.correction_input)
                                team = sorted_teams[game_state.selected_team_for_correction]
                                team_index = game_state.teams.index(team)
                                game_state.teams[team_index]['score'] = new_score
                                game_state.popup_text = f"Poeni promenjeni na {new_score}"
                                game_state.popup_until = time.time() + 2.0
                            except:
                                game_state.popup_text = "Unesite ispravan broj!"
                                game_state.popup_until = time.time() + 2.0
                        correction_input_active = False
                        game_state.selected_team_for_correction = -1
                        game_state.correction_input = ""
                    elif event.key == pygame.K_ESCAPE:
                        correction_input_active = False
                        game_state.selected_team_for_correction = -1
                        game_state.correction_input = ""
                    elif event.unicode.isdigit() or (event.unicode == '-' and not game_state.correction_input):
                        if len(game_state.correction_input) < 10:
                            game_state.correction_input += event.unicode
                elif event.key == pygame.K_ESCAPE and game_state.correction_mode:
                    game_state.correction_mode = False
                    game_state.popup_text = "Režim korekcije deaktiviran"
                    game_state.popup_until = time.time() + 2.0
            
            if event.type == pygame.MOUSEWHEEL:
                if table_x <= event.pos[0] <= table_x + table_width and table_y <= event.pos[1] <= table_y + table_height:
                    game_state.scroll_offset_results -= event.y * 3
                    max_scroll = max(0, len(game_state.teams) - visible_rows)
                    game_state.scroll_offset_results = max(0, min(game_state.scroll_offset_results, max_scroll))
        
        pygame.display.flip()
        clock.tick(60)

# ========== QUESTION INPUT SCREEN ==========
def question_input_screen():
    global music_playing
    
    if music_playing:
        pygame.mixer.music.pause()
    
    input_focus = "question"
    
    while game_state.question_input_mode:
        # === SVI RECT-OVI SE KREIRAJU SVAKI PUT ===
        question_rect = pygame.Rect(150, 190, SCREEN_WIDTH - 300, 60)
        option_rects = []
        for i in range(4):
            y = 290 + i * 55
            option_rects.append(pygame.Rect(200, y, SCREEN_WIDTH - 320, 42))
        correct_rect = pygame.Rect(150, 540, 200, 45)
        hint_rect = pygame.Rect(520, 505, SCREEN_WIDTH - 700, 45)
        save_rect = pygame.Rect(SCREEN_WIDTH - 350, SCREEN_HEIGHT - 100, 180, 50)
        back_rect = pygame.Rect(SCREEN_WIDTH - 150, SCREEN_HEIGHT - 100, 130, 50)
        panel_rect = pygame.Rect(80, 90, SCREEN_WIDTH - 160, SCREEN_HEIGHT - 210)
        
        # Pozadina
        for i in range(SCREEN_HEIGHT):
            progress = i / SCREEN_HEIGHT
            r = int(18 + (28 - 18) * progress)
            g = int(18 + (28 - 18) * progress)
            b = int(30 + (45 - 30) * progress)
            pygame.draw.line(screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))
        
        header_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 70)
        pygame.draw.rect(screen, COLORS['bg_panel'], header_rect)
        pygame.draw.line(screen, COLORS['border'], (0, 70), (SCREEN_WIDTH, 70), 2)
        
        draw_text(get_text('enter_question'), FONT_XL, COLORS['gold_light'], SCREEN_WIDTH//2, 35, centered=True)
        draw_panel(panel_rect, gradient=True)
        
        draw_text("📝 Pitanje:", FONT_MEDIUM, COLORS['text_secondary'], 120, 160)
        draw_input_field(question_rect, game_state.new_question['question'], input_focus == "question", "Unesite pitanje...")
        
        draw_text("📋 Opcije odgovora:", FONT_MEDIUM, COLORS['text_secondary'], 120, 265)
        for i in range(4):
            y = 290 + i * 55
            letter = chr(65 + i)
            draw_text(f"{letter})", FONT_MEDIUM, COLORS['gold_light'], 170, y + 10)
            draw_input_field(option_rects[i], game_state.new_question['options'][i], input_focus == f"option_{i}", f"Opcija {letter}")
        
        draw_text("✅ Tačan odgovor:", FONT_MEDIUM, COLORS['text_secondary'], 120, 510)
        draw_input_field(correct_rect, 
                        chr(65 + game_state.new_question['correct']) if game_state.new_question['correct'] >= 0 else "",
                        input_focus == "correct", 
                        "A-D")
        
        draw_text("💡 Hint:", FONT_MEDIUM, COLORS['text_secondary'], 400, 510)
        draw_input_field(hint_rect, game_state.new_question['hint'], input_focus == "hint", "Unesite hint...")
        
        if draw_button(get_text('save'), save_rect, COLORS['button_success'], COLORS['button_success_hover']):
            if game_state.add_new_question():
                game_state.popup_text = "✅ Pitanje je sačuvano!"
                game_state.popup_until = time.time() + 1.5
                logging.info(f"Novo pitanje dodato: {game_state.new_question['question'][:30]}...")
                game_state.new_question = {
                    'question': "",
                    'options': ["", "", "", ""],
                    'correct': -1,
                    'hint': "Hint nije dostupan."
                }
            else:
                game_state.popup_text = "⚠️ Popunite sva polja!"
                game_state.popup_until = time.time() + 2.0
        
        if draw_button(get_text('back'), back_rect, COLORS['button_primary'], COLORS['button_primary_hover']):
            game_state.question_input_mode = False
            break
        
        if getattr(game_state, 'popup_until', 0) > time.time():
            popup_surf = FONT_MEDIUM.render(game_state.popup_text, True, COLORS['text_primary'])
            popup_rect = popup_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            pygame.draw.rect(screen, COLORS['bg_panel'], popup_rect.inflate(40, 30), border_radius=15)
            pygame.draw.rect(screen, COLORS['gold_light'], popup_rect.inflate(40, 30), 3, border_radius=15)
            screen.blit(popup_surf, popup_rect)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_server()
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.VIDEORESIZE:
                pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                continue
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if question_rect.collidepoint((mx, my)):
                    input_focus = "question"
                elif correct_rect.collidepoint((mx, my)):
                    input_focus = "correct"
                elif hint_rect.collidepoint((mx, my)):
                    input_focus = "hint"
                else:
                    for i, rect in enumerate(option_rects):
                        if rect.collidepoint((mx, my)):
                            input_focus = f"option_{i}"
                            break
                    else:
                        input_focus = None
            
            if event.type == pygame.KEYDOWN and input_focus:
                if input_focus == "question":
                    if event.key == pygame.K_BACKSPACE:
                        game_state.new_question['question'] = game_state.new_question['question'][:-1]
                    elif event.key == pygame.K_RETURN:
                        input_focus = "option_0"
                    elif event.unicode.isprintable() and len(game_state.new_question['question']) < 200:
                        game_state.new_question['question'] += event.unicode
                
                elif input_focus.startswith("option_"):
                    idx = int(input_focus.split("_")[1])
                    if event.key == pygame.K_BACKSPACE:
                        game_state.new_question['options'][idx] = game_state.new_question['options'][idx][:-1]
                    elif event.key == pygame.K_RETURN:
                        if idx < 3:
                            input_focus = f"option_{idx + 1}"
                        else:
                            input_focus = "correct"
                    elif event.unicode.isprintable() and len(game_state.new_question['options'][idx]) < 100:
                        game_state.new_question['options'][idx] += event.unicode
                
                elif input_focus == "correct":
                    if event.key == pygame.K_BACKSPACE:
                        game_state.new_question['correct'] = -1
                    elif event.key in [pygame.K_a, pygame.K_b, pygame.K_c, pygame.K_d]:
                        game_state.new_question['correct'] = ord(event.unicode.lower()) - 97
                    elif event.key == pygame.K_RETURN:
                        input_focus = "hint"
                
                elif input_focus == "hint":
                    if event.key == pygame.K_BACKSPACE:
                        game_state.new_question['hint'] = game_state.new_question['hint'][:-1]
                    elif event.key == pygame.K_RETURN:
                        input_focus = None
                    elif event.unicode.isprintable() and len(game_state.new_question['hint']) < 100:
                        game_state.new_question['hint'] += event.unicode
        
        pygame.display.flip()
        clock.tick(60)

# ========== HISTORY SCREEN ==========
def history_screen():
    global music_playing
    
    if music_playing:
        pygame.mixer.music.unpause()
    
    selected_competition = None
    game_state.scroll_offset_history = 0
    game_state.scroll_offset_competitions = 0
    delete_confirmation = False
    competition_to_delete = -1
    
    while game_state.current == "history":
        # === SVI RECT-OVI SE KREIRAJU SVAKI PUT ===
        list_rect = pygame.Rect(50, 120, 400, SCREEN_HEIGHT - 200)
        details_rect = pygame.Rect(480, 120, SCREEN_WIDTH - 530, SCREEN_HEIGHT - 200)
        back_rect = pygame.Rect(SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT - 80, 200, 45)
        repeat_rect = pygame.Rect(SCREEN_WIDTH//2 + 100, SCREEN_HEIGHT - 80, 200, 45)
        delete_rect = pygame.Rect(SCREEN_WIDTH//2 + 320, SCREEN_HEIGHT - 80, 180, 45)
        
        # Pozadina
        for i in range(SCREEN_HEIGHT):
            progress = i / SCREEN_HEIGHT
            r = int(18 + (28 - 18) * progress)
            g = int(18 + (28 - 18) * progress)
            b = int(30 + (45 - 30) * progress)
            pygame.draw.line(screen, (r, g, b), (0, i), (SCREEN_WIDTH, i))
        
        header_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 70)
        pygame.draw.rect(screen, COLORS['bg_panel'], header_rect)
        pygame.draw.line(screen, COLORS['border'], (0, 70), (SCREEN_WIDTH, 70), 2)
        
        draw_text(get_text('history_title'), FONT_XL, COLORS['gold_light'], SCREEN_WIDTH//2, 35, centered=True)
        
        if not game_state.competitions_history:
            draw_text("📭 Nema sačuvanih takmičenja.", FONT_LARGE, COLORS['text_muted'], SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30, centered=True)
            draw_text("Kada završite kviz, rezultati će se automatski sačuvati.", FONT_MEDIUM, COLORS['text_muted'], SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30, centered=True)
        else:
            draw_panel(list_rect, gradient=True)
            draw_text(f"📋 {get_text('saved')}", FONT_MEDIUM, COLORS['gold_light'], list_rect.x + 20, list_rect.y + 15)
            draw_text(f"{len(game_state.competitions_history)} takmičenja", FONT_XS, COLORS['text_muted'], list_rect.x + list_rect.width - 100, list_rect.y + 25)
            
            item_height = 55
            max_items_visible = (list_rect.height - 50) // item_height
            max_scroll_comp = max(0, len(game_state.competitions_history) - max_items_visible)
            game_state.scroll_offset_competitions = max(0, min(game_state.scroll_offset_competitions, max_scroll_comp))
            
            for i in range(min(len(game_state.competitions_history), max_items_visible)):
                idx = i + game_state.scroll_offset_competitions
                if idx >= len(game_state.competitions_history):
                    break
                comp = game_state.competitions_history[idx]
                y = list_rect.y + 55 + i * item_height
                
                item_rect = pygame.Rect(list_rect.x + 10, y, list_rect.width - 20, item_height - 8)
                is_selected = (selected_competition == idx)
                
                if is_selected:
                    pygame.draw.rect(screen, COLORS['bg_hover'], item_rect, border_radius=8)
                    pygame.draw.rect(screen, COLORS['gold_light'], item_rect, 2, border_radius=8)
                else:
                    pygame.draw.rect(screen, COLORS['bg_panel_light'], item_rect, border_radius=8)
                    pygame.draw.rect(screen, COLORS['border'], item_rect, 1, border_radius=8)
                
                draw_text(comp['name'][:22], FONT_SMALL, COLORS['text_primary'], item_rect.x + 12, item_rect.y + 8)
                draw_text(comp.get('date', 'Nepoznat datum'), FONT_XS, COLORS['text_muted'], item_rect.x + 12, item_rect.y + 30)
                team_count = len(comp.get('teams', []))
                draw_text(f"👥 {team_count}", FONT_XS, COLORS['text_muted'], item_rect.right - 60, item_rect.y + 30)
                
                if item_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
                    selected_competition = idx
                    game_state.scroll_offset_history = 0
            
            if len(game_state.competitions_history) > max_items_visible:
                scroll_area = pygame.Rect(list_rect)
                new_offset, _ = draw_scroll_bar(scroll_area, len(game_state.competitions_history) * item_height + 55, game_state.scroll_offset_competitions, max_scroll_comp, "history_comp")
                game_state.scroll_offset_competitions = new_offset
            
            if selected_competition is not None and selected_competition < len(game_state.competitions_history):
                comp = game_state.competitions_history[selected_competition]
                draw_panel(details_rect, gradient=True)
                
                draw_text(f"🏆 {comp['name']}", FONT_LARGE, COLORS['gold_light'], details_rect.x + 20, details_rect.y + 15)
                draw_text(f"📅 {comp.get('date', 'Nepoznat datum')}", FONT_SMALL, COLORS['text_secondary'], details_rect.x + 20, details_rect.y + 60)
                
                table_y = details_rect.y + 100
                table_width = details_rect.width - 30
                
                pygame.draw.rect(screen, COLORS['bg_panel_light'], (details_rect.x + 15, table_y, table_width, 35))
                draw_text("Rang", FONT_XS, COLORS['gold_light'], details_rect.x + 30, table_y + 17)
                draw_text("Tim", FONT_XS, COLORS['gold_light'], details_rect.x + 100, table_y + 17)
                draw_text("Poeni", FONT_XS, COLORS['gold_light'], details_rect.x + 280, table_y + 17)
                draw_text("Tačni", FONT_XS, COLORS['gold_light'], details_rect.x + 370, table_y + 17)
                
                comp_teams_sorted = sorted(comp.get('teams', []), key=lambda x: x.get('score', 0), reverse=True)
                visible_teams = min(12, len(comp_teams_sorted))
                row_height = 32
                max_scroll_teams = max(0, len(comp_teams_sorted) - visible_teams)
                game_state.scroll_offset_history = max(0, min(game_state.scroll_offset_history, max_scroll_teams))
                
                for i in range(visible_teams):
                    list_idx = i + game_state.scroll_offset_history
                    if list_idx >= len(comp_teams_sorted):
                        break
                    team = comp_teams_sorted[list_idx]
                    y = table_y + 40 + i * row_height
                    
                    row_color = COLORS['bg_panel_light'] if i % 2 == 0 else COLORS['bg_panel']
                    pygame.draw.rect(screen, row_color, (details_rect.x + 15, y, table_width, row_height))
                    
                    if list_idx == 0:
                        draw_text("🥇", FONT_XS, COLORS['gold_light'], details_rect.x + 30, y + 6)
                    elif list_idx == 1:
                        draw_text("🥈", FONT_XS, COLORS['silver'], details_rect.x + 30, y + 6)
                    elif list_idx == 2:
                        draw_text("🥉", FONT_XS, COLORS['bronze'], details_rect.x + 30, y + 6)
                    else:
                        draw_text(f"{list_idx + 1}.", FONT_XS, COLORS['text_muted'], details_rect.x + 30, y + 6)
                    
                    draw_text(team.get('name', '')[:18], FONT_XS, COLORS['text_primary'], details_rect.x + 100, y + 6)
                    draw_text(str(team.get('score', 0)), FONT_XS, COLORS['green'] if team.get('score', 0) >= 0 else COLORS['red'], details_rect.x + 280, y + 6)
                    draw_text(str(team.get('correct_count', 0)), FONT_XS, COLORS['text_secondary'], details_rect.x + 370, y + 6)
                
                if len(comp_teams_sorted) > visible_teams:
                    scroll_area_teams = pygame.Rect(details_rect.x, table_y, details_rect.width, details_rect.height - 100)
                    new_offset, _ = draw_scroll_bar(scroll_area_teams, len(comp_teams_sorted) * row_height + 40, game_state.scroll_offset_history, max_scroll_teams, "history_teams")
                    game_state.scroll_offset_history = new_offset
        
        if draw_button(get_text('back'), back_rect, COLORS['button_primary'], COLORS['button_primary_hover']):
            game_state.current = "results" if game_state.teams else "setup"
        
        if selected_competition is not None and selected_competition < len(game_state.competitions_history):
            if draw_button(get_text('repeat_quiz'), repeat_rect, COLORS['button_success'], COLORS['button_success_hover']):
                comp = game_state.competitions_history[selected_competition]
                game_state.teams = []
                game_state.quiz_name = f"PONOVLJENO: {comp['name']}"
                for team_data in comp.get('teams', []):
                    game_state.teams.append({
                        'name': team_data.get('name', 'Tim'),
                        'members': team_data.get('members', []),
                        'player_name': team_data.get('player_name', ''),
                        'score': 0,
                        'answers': [None] * len(comp.get('questions', [])),
                        'response_times': [None] * len(comp.get('questions', [])),
                        'client': None,
                        'correct_count': 0,
                        'fastest_response': None,
                        'response_times_list': []
                    })
                if 'questions' in comp:
                    game_state.current_questions = comp['questions']
                    game_state.num_questions = len(comp['questions'])
                else:
                    game_state.num_questions = min(10, len(all_questions))
                    indices = random.sample(range(len(all_questions)), game_state.num_questions)
                    game_state.current_questions = [all_questions[idx] for idx in indices]
                game_state.reset_for_new_quiz()
                game_state.quiz_active = True
                game_state.question_start_time = time.time()
                game_state.quiz_start_time = time.time()
                if game_state.active_team_index == -1 and len(game_state.teams) > 0:
                    game_state.active_team_index = 0
                game_state.current = "quiz"
                if game_state.network_enabled:
                    broadcast_question()
                    broadcast({'type': 'quiz_start', 'quiz_name': game_state.quiz_name})
                logging.info(f"Ponovljen kviz: {comp['name']}")
            
            if draw_button(get_text('delete'), delete_rect, COLORS['button_danger'], COLORS['button_danger_hover']):
                delete_confirmation = True
                competition_to_delete = selected_competition
        
        if delete_confirmation and competition_to_delete is not None and competition_to_delete < len(game_state.competitions_history):
            comp = game_state.competitions_history[competition_to_delete]
            confirm_panel = pygame.Rect(SCREEN_WIDTH//2 - 250, SCREEN_HEIGHT//2 - 120, 500, 200)
            pygame.draw.rect(screen, COLORS['bg_panel'], confirm_panel, border_radius=15)
            pygame.draw.rect(screen, COLORS['gold_light'], confirm_panel, 3, border_radius=15)
            
            draw_text("⚠️ POTVRDA BRISANJA", FONT_LARGE, COLORS['red'], confirm_panel.centerx, confirm_panel.y + 35, centered=True)
            draw_text(f"Da li ste sigurni da želite da obrišete:", FONT_MEDIUM, COLORS['text_secondary'], confirm_panel.centerx, confirm_panel.y + 85, centered=True)
            draw_text(f"'{comp['name']}'?", FONT_MEDIUM, COLORS['gold_light'], confirm_panel.centerx, confirm_panel.y + 120, centered=True)
            
            yes_rect = pygame.Rect(confirm_panel.centerx - 120, confirm_panel.y + 150, 100, 40)
            no_rect = pygame.Rect(confirm_panel.centerx + 20, confirm_panel.y + 150, 100, 40)
            
            if draw_button("DA, OBRIŠI", yes_rect, COLORS['button_danger'], COLORS['button_danger_hover']):
                if game_state.delete_competition(competition_to_delete):
                    game_state.popup_text = f"Takmičenje '{comp['name']}' je obrisano!"
                    game_state.popup_until = time.time() + 2.0
                    if selected_competition >= len(game_state.competitions_history):
                        selected_competition = None
                delete_confirmation = False
                competition_to_delete = -1
            
            if draw_button("NE, OTKAŽI", no_rect, COLORS['button_primary'], COLORS['button_primary_hover']):
                delete_confirmation = False
                competition_to_delete = -1
        
        if getattr(game_state, 'popup_until', 0) > time.time():
            popup_surf = FONT_MEDIUM.render(game_state.popup_text, True, COLORS['text_primary'])
            popup_rect = popup_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
            pygame.draw.rect(screen, COLORS['bg_panel'], popup_rect.inflate(40, 30), border_radius=15)
            pygame.draw.rect(screen, COLORS['gold_light'], popup_rect.inflate(40, 30), 3, border_radius=15)
            screen.blit(popup_surf, popup_rect)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_server()
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.VIDEORESIZE:
                pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                continue
            
            if event.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                if list_rect.collidepoint((mx, my)):
                    game_state.scroll_offset_competitions -= event.y * 2
                    max_scroll_comp = max(0, len(game_state.competitions_history) - max_items_visible)
                    game_state.scroll_offset_competitions = max(0, min(game_state.scroll_offset_competitions, max_scroll_comp))
                elif selected_competition is not None and details_rect.collidepoint((mx, my)):
                    game_state.scroll_offset_history -= event.y * 2
                    max_scroll_teams = max(0, len(comp_teams_sorted) - visible_teams)
                    game_state.scroll_offset_history = max(0, min(game_state.scroll_offset_history, max_scroll_teams))
        
        pygame.display.flip()
        clock.tick(60)

# ========== ISTORIJA FUNKCIJE ==========
def load_history():
    try:
        history_path = get_data_path("competitions.json")
        if os.path.exists(history_path):
            with open(history_path, "r", encoding="utf-8") as f:
                game_state.competitions_history = json.load(f)
            logging.info(f"Učitano {len(game_state.competitions_history)} takmičenja")
    except Exception as e:
        logging.error(f"Greška pri učitavanju istorije: {e}")
        game_state.competitions_history = []

def save_competitions_to_file(competitions):
    try:
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = "."
        history_file = os.path.join(base_dir, "competitions.json")
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(competitions, f, ensure_ascii=False, indent=2)
        logging.info(f"Sačuvano {len(competitions)} takmičenja")
    except Exception as e:
        logging.error(f"Greška pri čuvanju istorije: {e}")

def save_history():
    try:
        competition_data = {
            'id': str(time.time()),
            'name': game_state.quiz_name,
            'date': datetime.now().strftime("%d.%m.%Y %H:%M"),
            'timestamp': time.time(),
            'teams': [],
            'questions': game_state.current_questions,
            'num_questions': game_state.num_questions
        }
        for team in game_state.teams:
            team_data = {
                'name': team.get('name', ''),
                'members': team.get('members', []),
                'player_name': team.get('player_name', ''),
                'score': team.get('score', 0),
                'correct_count': team.get('correct_count', 0),
                'fastest_response': team.get('fastest_response'),
                'response_times': team.get('response_times_list', [])
            }
            competition_data['teams'].append(team_data)
        
        game_state.competitions_history.append(competition_data)
        game_state.competitions_history.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        if len(game_state.competitions_history) > 100:
            game_state.competitions_history = game_state.competitions_history[:100]
        
        save_competitions_to_file(game_state.competitions_history)
        logging.info(f"Takmičenje sačuvano: {game_state.quiz_name}")
    except Exception as e:
        logging.error(f"Greška pri čuvanju: {e}")

# ========== GLAVNA PETLJA ==========
all_questions = load_questions_by_language(current_lang)
game_state.custom_questions = []

def main():
    load_history()
    
    try:
        custom_file = get_data_path("custom_questions.json")
        if os.path.exists(custom_file):
            with open(custom_file, "r", encoding="utf-8") as f:
                game_state.custom_questions = json.load(f)
            logging.info(f"Učitano {len(game_state.custom_questions)} custom pitanja")
    except Exception as e:
        logging.error(f"Greška pri učitavanju custom pitanja: {e}")
    
    load_music()
    load_sound_effects()
    show_splash_screen()
    create_render_files()
    
    if ARGS.demo:
        game_state.num_questions = 5
        game_state.popup_text = "🔹 DEMO MOD - Ograničeno na 5 pitanja"
        game_state.popup_until = time.time() + 3.0
    
    if ARGS.load:
        if load_quiz_state(ARGS.load):
            game_state.current = "quiz"
            game_state.quiz_active = True
            game_state.question_start_time = time.time()
            logging.info(f"Učitano stanje iz: {ARGS.load}")
    
    auto_save_thread = threading.Thread(target=auto_save_quiz, daemon=True)
    auto_save_thread.start()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.VIDEORESIZE:
                pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            else:
                pygame.event.post(event)
                break
        
        if game_state.current == "setup":
            setup_screen()
        elif game_state.current == "team_registration":
            team_registration_screen()
        elif game_state.current == "quiz":
            quiz_screen()
        elif game_state.current == "results":
            results_screen()
        elif game_state.current == "history":
            history_screen()
        
        clock.tick(60)

if __name__ == "__main__":
    try:
        ARGS = parse_args()
        if ARGS.lang:
            set_language(ARGS.lang)
        main()
    except KeyboardInterrupt:
        logging.info("Aplikacija prekinuta od strane korisnika")
    except Exception as e:
        logging.error(f"Neočekivana greška: {e}")
        import traceback
        traceback.print_exc()
    finally:
        stop_server()
        pygame.quit()
        sys.exit()
