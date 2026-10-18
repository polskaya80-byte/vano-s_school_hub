import streamlit as st
import json
import os
import re
import random
from datetime import datetime
import pandas as pd
import google.generativeai as genai
import pypdf
import requests

# ---------------------------------------------------------
# 1. НАЛАШТУВАННЯ СТОРІНКИ ТА СКЕТЧ-СТИЛІВ (CSS)
# ---------------------------------------------------------
st.set_page_config(
    page_title="RudaFox Learning Hub",
    page_icon="🦊",
    layout="wide"
)

# Завантаження дудлінг-шрифтів з Google Fonts та стилізація
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Comfortaa:wght@500;700&family=Neucha&display=swap');

    /* Загальний фон сайту в теплій гамі */
    .stApp {
        background-color: #fcf8f2 !important;
        color: #3e2723 !important;
        font-family: 'Comfortaa', cursive, sans-serif !important;
    }

    /* Заголовки у стилі hand-drawn скетчу */
    h1, h2, h3, h4, .stHeader {
        font-family: 'Neucha', cursive, sans-serif !important;
        color: #2e4a32 !important;
        letter-spacing: 1px;
    }

    /* Бокова панель (Скетчбук) */
    section[data-testid="stSidebar"] {
        background-color: #f4ece1 !important;
        border-right: 3px dashed #8d6e63 !important;
    }

    /* Стильні кнопки у дудлінг-стилі */
    .stButton>button {
        background-color: #4a7c59 !important;
        color: #ffffff !important;
        border: 2px solid #2e4a32 !important;
        border-radius: 18px !important;
        font-family: 'Comfortaa', cursive !important;
        font-weight: bold !important;
        box-shadow: 3px 3px 0px #2e4a32 !important;
        transition: all 0.2s ease !important;
    }

    .stButton>button:hover {
        transform: translate(-2px, -2px) !important;
        box-shadow: 5px 5px 0px #2e4a32 !important;
        background-color: #3a6346 !important;
    }

    /* Збільшений, зручний блок із тестом */
    div[data-testid="stForm"] {
        background-color: #fffdf9 !important;
        border: 3px dashed #8d6e63 !important;
        border-radius: 20px !important;
        box-shadow: 6px 6px 0px rgba(141, 110, 99, 0.2) !important;
        padding: 25px !important;
    }

    /* Стилізація варіантів у тесті */
    div[role="radiogroup"] label {
        background-color: #fcf8f2 !important;
        border: 2px solid #d7ccc8 !important;
        border-radius: 12px !important;
        padding: 10px 18px !important;
        margin-bottom: 8px !important;
        font-size: 16px !important;
        cursor: pointer !important;
        transition: all 0.2s !important;
    }

    div[role="radiogroup"] label:hover {
        border-color: #4a7c59 !important;
        background-color: #e8f5e9 !important;
    }

    /* Вкладки (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #f4ece1 !important;
        border-radius: 12px 12px 0px 0px !important;
        border: 1px solid #8d6e63 !important;
        color: #3e2723 !important;
        font-family: 'Neucha', cursive !important;
        font-size: 18px !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: #4a7c59 !important;
        color: #ffffff !important;
        border-bottom: none !important;
    }

    /* Дудл-карточки для дашборду */
    .doodle-card {
        background-color: #fffdf9;
        border: 2px dashed #8d6e63;
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 15px;
        box-shadow: 3px 3px 0px rgba(141, 110, 99, 0.15);
    }
</style>
""", unsafe_allow_html=True)

DATA_FILE = "lessons_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"lessons": [], "results": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

db = load_data()

# ---------------------------------------------------------
# 2. МОТИВАЦІЙНІ ЦИТАТИ ТА ЛАЙФХАКИ ДЛЯ КУКУХИ
# ---------------------------------------------------------
MOTIVATIONAL_QUOTES = [
    "«Світ великий і дивний, але геометрію за тебе ніхто не складе.» — Мудрість Зони S.T.A.L.K.E.R.",
    "«Важко навчатися? Зате в Minecraft потім побудуєш атомний коллайдер!»",
    "«Навіть Тоторо робить перерви на сон. Бережи кукуху, роби паузи!» — Studio Ghibli",
    "«Вчитися — це як качати перк у гринді: спочатку нудно, а потім ти оверпауер!»",
    "«Пригода на 20 хвилин, казав Рік... Але цей конспект ми закриємо за 10!» — Рік і Морті",
    "«Знання — це твій особистий артефакт, який не фонить радіацією.»",
    "«Не бійся робити помилки. Навіть у коді Minecraft спочатку були баги з кріперами!»"
]

TEEN_LIFEHACKS = [
    "🧠 **Лайфхак для кукухи:** Метод Помодоро — 25 хв вчишся, 5 хв тупиш у меми. Мозок перестає закипати!",
    "🎧 **Лайфхак для фокусу:** Ввімкни Lofi-хіп-хоп або саундтрек із Minecraft/Ghibli без слів — рівень концентрації +40%.",
    "💧 **Лайфхак для бадьорості:** Зроби 3 глибоких видихи та випий склянку води. Вода змиває ментальний дебаф на 15%.",
    "👀 **Лайфхак для очей:** Правило 20-20-20: кожні 20 хвилин дивись 20 секунд у вікно на щось зелене.",
    "🍫 **Лайфхак для мотивації:** Пообіцяй собі смаколик чи 15 хвилин катки одразу після закриття цього тесту!"
]

def get_daily_quote_and_hack(date_str):
    try:
        seed = int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())
    except Exception:
        seed = 42
    rnd = random.Random(seed)
    q = rnd.choice(MOTIVATIONAL_QUOTES)
    h = rnd.choice(TEEN_LIFEHACKS)
    return q, h

# ---------------------------------------------------------
# 3. ТЕЛЕГРАМ СПОВІЩЕННЯ
# ---------------------------------------------------------
def send_telegram_notification(subject, topic, test_mode, score_pct, score_text, completed_at, day_progress_str=""):
    bot_token = str(st.secrets.get("TELEGRAM_BOT_TOKEN", None) or st.session_state.get("user_tg_token", "")).strip()
    chat_id = str(st.secrets.get("TELEGRAM_CHAT_ID", None) or st.session_state.get("user_tg_chat_id", "")).strip()
    
    if not bot_token or not chat_id:
        return False, "Ключі Telegram не знайдені в Secrets або налаштуваннях."
    
    clean_topic = str(topic).replace("*", "").replace("_", "").replace("`", "")
    clean_subject = str(subject).replace("*", "").replace("_", "")
    
    msg = (
        f"🦊 *ЗВІТ З МІСЦЯ СТРАЖДАНЬ ТА ДОСЯГНЕНЬ*\n\n"
        f"📚 *Предмет:* {clean_subject}\n"
        f"📖 *Тема:* {clean_topic}\n"
        f"🏋️ *Режим:* {test_mode}\n"
        f"📊 *Результат тесту:* {score_pct}% ({score_text})\n"
        f"📈 *Прогрес за день:* {day_progress_str}\n"
        f"⏰ *Час здачі:* {completed_at}"
    )
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        res_data = response.json()
        if response.status_code == 200 and res_data.get("ok"):
            return True, "Успішно"
        else:
            err_desc = res_data.get("description", response.text)
            return False, f"{err_desc}"
    except Exception as e:
        return False, f"Помилка з'єднання: {e}"

# ---------------------------------------------------------
# 4. ЗЧИТУВАННЯ PDF
# ---------------------------------------------------------
def extract_text_from_pdf(uploaded_file):
    try:
        reader = pypdf.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    except Exception as e:
        st.error(f"Помилка зчитування PDF: {e}")
        return ""

# ---------------------------------------------------------
# 5. ТЕМАТИЧНІ ПРЕСЕТИ
# ---------------------------------------------------------
THEMES = {
    "🌿 Затишний Скетчбук (Коричневий-Зелений)": {
        "bg_front": "linear-gradient(135deg, #4a7c59 0%, #3a6346 100%)",
        "bg_back": "linear-gradient(135deg, #8d5b4c 0%, #6d4032 100%)",
        "border_front": "#2e4a32",
        "border_back": "#4a2c20",
        "slide_bg": "#fffdf9",
        "slide_text": "#3e2723",
        "slide_accent": "#4a7c59"
    },
    "🍃 Studio Ghibli Еко": {
        "bg_front": "linear-gradient(135deg, #2d5a27 0%, #3c763d 100%)",
        "bg_back": "linear-gradient(135deg, #8b5a2b 0%, #a0522d 100%)",
        "border_front": "#5cb85c",
        "border_back": "#cd853f",
        "slide_bg": "#f4f1ea",
        "slide_text": "#2c3e50",
        "slide_accent": "#27ae60"
    },
    "👾 Minecraft Піксель": {
        "bg_front": "linear-gradient(135deg, #388e3c 0%, #1b5e20 100%)",
        "bg_back": "linear-gradient(135deg, #795548 0%, #4e342e 100%)",
        "border_front": "#81c784",
        "border_back": "#a1887f",
        "slide_bg": "#e8f5e9",
        "slide_text": "#1b5e20",
        "slide_accent": "#2e7d32"
    },
    "☢️ Зона S.T.A.L.K.E.R.": {
        "bg_front": "linear-gradient(135deg, #2b3a2a 0%, #1a2419 100%)",
        "bg_back": "linear-gradient(135deg, #4a3b2c 0%, #291f16 100%)",
        "border_front": "#4af626",
        "border_back": "#ff9800",
        "slide_bg": "#121712",
        "slide_text": "#e0e6e0",
        "slide_accent": "#4af626"
    }
}

# ---------------------------------------------------------
# 6. РОЗУМНА ГЕНЕРАЦІЯ
# ---------------------------------------------------------
def generate_lesson_with_fallback(prompt, api_key):
    genai.configure(api_key=api_key)
    candidate_models = ['gemini-3.8-flash', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-flash']
    
    last_error = None
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            last_error = e
            continue
            
    raise last_error

# ---------------------------------------------------------
# 7. ШІ-ВІДЕОПЛЕЄР З ГОЛОСОВИМ ДИКТОРОМ (WEB SPEECH API)
# ---------------------------------------------------------
def render_ai_video_explainer_html(video_data, theme_key):
    if not video_data or not video_data.get("scenes"):
        return
    
    theme = THEMES.get(theme_key, THEMES["🌿 Затишний Скетчбук (Коричневий-Зелений)"])
    video_json = json.dumps(video_data, ensure_ascii=False)
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <link href="https://fonts.googleapis.com/css2?family=Comfortaa:wght@500;700&family=Neucha&display=swap" rel="stylesheet">
    <style>
      body {{ font-family: 'Comfortaa', cursive, sans-serif; background: transparent; margin: 0; padding: 10px; display: flex; flex-direction: column; align-items: center; }}
      .video-box {{ width: 100%; max-width: 820px; background: {theme['slide_bg']}; color: {theme['slide_text']}; border-radius: 20px; border: 3px dashed {theme['slide_accent']}; padding: 25px; box-sizing: border-box; box-shadow: 6px 6px 0px rgba(0,0,0,0.1); position: relative; }}
      .video-header {{ font-family: 'Neucha', cursive; font-size: 26px; font-weight: 700; color: {theme['slide_accent']}; border-bottom: 2px dashed {theme['slide_accent']}; padding-bottom: 8px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }}
      .scene-screen {{ background: rgba(74, 124, 89, 0.08); border: 2px solid {theme['slide_accent']}; border-radius: 16px; padding: 20px; min-height: 180px; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; margin-bottom: 15px; position: relative; }}
      .scene-time {{ position: absolute; top: 10px; left: 15px; font-family: 'Neucha', cursive; font-size: 14px; background: {theme['slide_accent']}; color: white; padding: 3px 10px; border-radius: 10px; }}
      .scene-visual {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; color: {theme['slide_accent']}; }}
      .subtitles-box {{ background: #2e4a32; color: #ffffff; padding: 12px 18px; border-radius: 12px; font-size: 15px; line-height: 1.5; min-height: 50px; display: flex; align-items: center; justify-content: center; text-align: center; border: 1px solid #1a2419; margin-bottom: 15px; }}
      .controls-bar {{ display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; }}
      .btn {{ background-color: {theme['slide_accent']}; color: white; border: 2px solid #2e4a32; padding: 9px 20px; border-radius: 20px; cursor: pointer; font-family: 'Comfortaa', cursive; font-weight: 700; font-size: 14px; box-shadow: 2px 2px 0px #2e4a32; transition: all 0.2s; }}
      .btn:hover {{ transform: translate(-1px, -1px); box-shadow: 4px 4px 0px #2e4a32; }}
      .speed-select {{ background: #f4ece1; border: 2px solid #8d6e63; border-radius: 12px; padding: 6px 12px; font-family: 'Comfortaa', cursive; font-weight: bold; }}
    </style>
    </head>
    <body>

    <div class="video-box">
      <div class="video-header">
        <span>🎥 ШІ-Відеопояснення з Диктором</span>
        <select class="speed-select" id="speed-select" onchange="changeSpeed()">
          <option value="1">Швидкість 1.0x</option>
          <option value="1.25">Швидкість 1.25x</option>
          <option value="1.5">Швидкість 1.5x</option>
        </select>
      </div>

      <div class="scene-screen">
        <div class="scene-time" id="v-time">00:00 - 00:15</div>
        <div class="scene-visual" id="v-visual">🎨 Візуальний кадр...</div>
      </div>

      <div class="subtitles-box" id="v-subtitles">💬 Натисніть «Запустити відеопояснення», щоб послухати диктора...</div>

      <div class="controls-bar">
        <button class="btn" onclick="prevScene()">⬅️ Кадр назад</button>
        <button class="btn" style="background:#2e4a32;" id="play-btn" onclick="togglePlay()">▶️ Запустити відеопояснення</button>
        <button class="btn" onclick="nextScene()">Кадр далі ➡️</button>
      </div>
    </div>

    <script>
      const videoData = {video_json};
      const scenes = videoData.scenes || [];
      let currentIdx = 0;
      let isPlaying = false;
      let synth = window.speechSynthesis;
      let currentUtterance = null;
      let speechSpeed = 1.0;

      function updateScene() {{
        if (scenes.length === 0) return;
        const sc = scenes[currentIdx];
        document.getElementById('v-time').innerText = "⏱️ Кадр " + (currentIdx + 1) + " / " + scenes.length + " (" + (sc.timecode || "") + ")";
        document.getElementById('v-visual').innerHTML = sc.visual || "";
        document.getElementById('v-subtitles').innerText = "🗣️ " + (sc.narration || "");
      }}

      function speakCurrentScene() {{
        if (!('speechSynthesis' in window)) {{
          alert("Ваш браузер не підтримує голосовий синтез. Спробуйте Chrome або Safari.");
          return;
        }}
        synth.cancel();

        const sc = scenes[currentIdx];
        currentUtterance = new SpeechSynthesisUtterance(sc.narration);
        currentUtterance.lang = 'uk-UA';
        currentUtterance.rate = speechSpeed;

        currentUtterance.onend = function() {{
          if (isPlaying && currentIdx < scenes.length - 1) {{
            currentIdx++;
            updateScene();
            speakCurrentScene();
          }} else if (currentIdx === scenes.length - 1) {{
            isPlaying = false;
            document.getElementById('play-btn').innerText = "▶️ Повторити спочатку";
          }}
        }};

        synth.speak(currentUtterance);
      }}

      function togglePlay() {{
        if (isPlaying) {{
          synth.cancel();
          isPlaying = false;
          document.getElementById('play-btn').innerText = "▶️ Продовжити";
        }} else {{
          if (currentIdx >= scenes.length - 1) {{
            currentIdx = 0;
          }}
          isPlaying = true;
          document.getElementById('play-btn').innerText = "⏸️ Пауза";
          updateScene();
          speakCurrentScene();
        }}
      }}

      function nextScene() {{
        synth.cancel();
        if (currentIdx < scenes.length - 1) {{
          currentIdx++;
          updateScene();
          if (isPlaying) speakCurrentScene();
        }}
      }}

      function prevScene() {{
        synth.cancel();
        if (currentIdx > 0) {{
          currentIdx--;
          updateScene();
          if (isPlaying) speakCurrentScene();
        }}
      }}

      function changeSpeed() {{
        speechSpeed = parseFloat(document.getElementById('speed-select').value);
        if (isPlaying) {{
          speakCurrentScene();
        }}
      }}

      // Init
      updateScene();
    </script>
    </body>
    </html>
    """
    return html_code

def render_smart_video(url):
    if not url or not url.strip():
        return
    clean_url = url.strip()
    yt_match = re.search(r'(?:youtu\.be/|youtube\.com/(?:embed/|v/|watch\?v=|shorts/))([\w-]{11})', clean_url)
    if yt_match:
        yt_id = yt_match.group(1)
        st.video(f"https://www.youtube.com/watch?v={yt_id}")
    elif "pistacja.tv" in clean_url:
        st.markdown(f"""
        <div style="background:#e8f5e9; border:2px dashed #4a7c59; padding:18px; border-radius:16px; text-align:center;">
            <h4>🎬 Відеоурок з Pistacja.tv</h4>
            <p>Натисніть нижче, щоб відкрити матеріал:</p>
            <a href="{clean_url}" target="_blank" style="background:#4a7c59; color:white; padding:10px 20px; border-radius:20px; text-decoration:none; font-weight:bold; display:inline-block;">▶️ Відкрити відео на Pistacja.tv</a>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"🔗 [Перейти до відео/матеріалів уроку]({clean_url})")

def render_presentation_html(slides, external_pres_url, theme_key):
    if external_pres_url and external_pres_url.strip():
        ext_url = external_pres_url.strip()
        st.markdown(f"""
        <div style="background:#fffdf9; border:2px dashed #4a7c59; padding:20px; border-radius:18px; text-align:center; margin-bottom:15px;">
            <h4>💻 Інтегрована презентація (NotebookLM / Google Slides)</h4>
            <p style="font-size:14px; color:#555;">Клацніть кнопку, щоб відкрити повномасштабну презентацію:</p>
            <a href="{ext_url}" target="_blank" style="background:#4a7c59; color:white; padding:12px 26px; border-radius:25px; text-decoration:none; font-weight:bold; display:inline-block; box-shadow:2px 2px 0px #2e4a32;">🚀 Відкрити презентацію у повному вікні</a>
        </div>
        """, unsafe_allow_html=True)
        return

    if not slides:
        return
    
    theme = THEMES.get(theme_key, THEMES["🌿 Затишний Скетчбук (Коричневий-Зелений)"])
    slides_json = json.dumps(slides, ensure_ascii=False)
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <link href="https://fonts.googleapis.com/css2?family=Comfortaa:wght@500;700&family=Neucha&display=swap" rel="stylesheet">
    <style>
      body {{ font-family: 'Comfortaa', cursive, sans-serif; background: transparent; margin: 0; padding: 10px; display: flex; flex-direction: column; align-items: center; }}
      .slide-container {{ width: 100%; max-width: 820px; min-height: 340px; background: {theme['slide_bg']}; color: {theme['slide_text']}; border-radius: 20px; border: 3px dashed {theme['slide_accent']}; padding: 30px; box-sizing: border-box; box-shadow: 6px 6px 0px rgba(0,0,0,0.1); position: relative; display: flex; flex-direction: column; justify-content: space-between; }}
      .slide-title {{ font-family: 'Neucha', cursive, sans-serif; font-size: 28px; font-weight: 700; color: {theme['slide_accent']}; margin-bottom: 12px; border-bottom: 2px dashed {theme['slide_accent']}; padding-bottom: 8px; }}
      .takeaway-box {{ background: rgba(74, 124, 89, 0.1); border-left: 4px solid {theme['slide_accent']}; padding: 10px 15px; margin-bottom: 15px; font-size: 14px; font-weight: bold; border-radius: 4px; }}
      .slide-content {{ font-size: 16px; line-height: 1.7; flex-grow: 1; }}
      .slide-content ul {{ margin-top: 5px; padding-left: 20px; }}
      .slide-content li {{ margin-bottom: 8px; }}
      .controls {{ display: flex; justify-content: space-between; align-items: center; margin-top: 20px; }}
      .btn {{ background-color: {theme['slide_accent']}; color: white; border: 2px solid #2e4a32; padding: 10px 24px; border-radius: 20px; cursor: pointer; font-family: 'Comfortaa', cursive; font-weight: 700; font-size: 15px; box-shadow: 3px 3px 0px #2e4a32; transition: all 0.2s; }}
      .btn:hover {{ transform: translate(-1px, -1px); box-shadow: 5px 5px 0px #2e4a32; }}
      .counter {{ font-family: 'Neucha', cursive; font-size: 20px; font-weight: 700; }}
    </style>
    </head>
    <body>

    <div class="slide-container">
      <div>
        <div class="slide-title" id="s-title">Заголовок</div>
        <div class="takeaway-box" id="s-takeaway">💡 Головний висновок...</div>
        <div class="slide-content" id="s-content">Зміст слайду...</div>
      </div>
      <div class="controls">
        <button class="btn" onclick="prevSlide()">⬅️ Назад</button>
        <span class="counter" id="s-counter">1 / 1</span>
        <button class="btn" onclick="nextSlide()">Далі ➡️</button>
      </div>
    </div>

    <script>
      const slides = {slides_json};
      let currIdx = 0;

      function updateSlide() {{
        document.getElementById('s-title').innerText = slides[currIdx].title;
        document.getElementById('s-takeaway').innerHTML = "💡 " + (slides[currIdx].takeaway || "Ключова думка слайду");
        document.getElementById('s-content').innerHTML = slides[currIdx].content;
        document.getElementById('s-counter').innerText = (currIdx + 1) + " / " + slides.length;
      }}

      function nextSlide() {{
        if (currIdx < slides.length - 1) {{ currIdx++; updateSlide(); }}
        else {{ currIdx = 0; updateSlide(); }}
      }}

      function prevSlide() {{
        if (currIdx > 0) {{ currIdx--; updateSlide(); }}
        else {{ currIdx = slides.length - 1; updateSlide(); }}
      }}

      if (slides.length > 0) updateSlide();
    </script>
    </body>
    </html>
    """
    return html_code

def render_flashcards_html(flashcards, theme_key):
    if not flashcards:
        return ""
    
    theme = THEMES.get(theme_key, THEMES["🌿 Затишний Скетчбук (Коричневий-Зелений)"])
    cards_data_json = json.dumps(flashcards, ensure_ascii=False)
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <link href="https://fonts.googleapis.com/css2?family=Comfortaa:wght@500;700&family=Neucha&display=swap" rel="stylesheet">
    <style>
      body {{ font-family: 'Comfortaa', cursive, sans-serif; background: transparent; margin: 0; padding: 10px; display: flex; flex-direction: column; align-items: center; }}
      .scene {{ width: 100%; max-width: 500px; height: 240px; perspective: 1000px; cursor: pointer; }}
      .card {{ width: 100%; height: 100%; position: relative; transform-style: preserve-3d; transition: transform 0.6s cubic-bezier(0.4, 0.2, 0.2, 1); border-radius: 20px; box-shadow: 4px 4px 0px rgba(0,0,0,0.15); }}
      .card.is-flipped {{ transform: rotateY(180deg); }}
      .card-face {{ position: absolute; width: 100%; height: 100%; backface-visibility: hidden; border-radius: 20px; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 25px; box-sizing: border-box; text-align: center; font-size: 18px; line-height: 1.5; font-weight: 500; }}
      .card-front {{ background: {theme['bg_front']}; color: #ffffff; border: 3px dashed {theme['border_front']}; }}
      .card-back {{ background: {theme['bg_back']}; color: #ffffff; transform: rotateY(180deg); border: 3px dashed {theme['border_back']}; }}
      .hint {{ font-family: 'Neucha', cursive; font-size: 15px; margin-top: 12px; opacity: 0.9; letter-spacing: 1px; }}
      .controls {{ display: flex; gap: 15px; align-items: center; margin-top: 15px; }}
      .btn {{ background-color: {theme['slide_accent']}; color: white; border: 2px solid #2e4a32; padding: 8px 20px; border-radius: 20px; cursor: pointer; font-family: 'Comfortaa', cursive; font-weight: 700; font-size: 14px; box-shadow: 2px 2px 0px #2e4a32; transition: all 0.2s; }}
      .btn:hover {{ transform: translate(-1px, -1px); box-shadow: 4px 4px 0px #2e4a32; }}
      .counter {{ font-family: 'Neucha', cursive; font-size: 18px; font-weight: 700; }}
    </style>
    </head>
    <body>

    <div class="scene" onclick="flipCard()">
      <div class="card" id="card">
        <div class="card-face card-front">
          <div id="card-front-text">Термін</div>
          <div class="hint">💡 Натисніть, щоб перевернути</div>
        </div>
        <div class="card-face card-back">
          <div id="card-back-text">Пояснення</div>
          <div class="hint">🔄 Натисніть, щоб повернути</div>
        </div>
      </div>
    </div>

    <div class="controls">
      <button class="btn" onclick="prevCard()">⬅️ Назад</button>
      <span class="counter" id="counter">1 / 1</span>
      <button class="btn" onclick="nextCard()">Далі ➡️</button>
    </div>

    <script>
      const cards = {cards_data_json};
      let currentIndex = 0;

      function updateCard() {{
        document.getElementById('card').classList.remove('is-flipped');
        setTimeout(() => {{
          document.getElementById('card-front-text').innerText = cards[currentIndex].front;
          document.getElementById('card-back-text').innerText = cards[currentIndex].back;
          document.getElementById('counter').innerText = (currentIndex + 1) + " / " + cards.length;
        }}, 150);
      }}

      function flipCard() {{
        document.getElementById('card').classList.toggle('is-flipped');
      }}

      function nextCard() {{
        if (currentIndex < cards.length - 1) {{ currentIndex++; updateCard(); }}
        else {{ currentIndex = 0; updateCard(); }}
      }}

      function prevCard() {{
        if (currentIndex > 0) {{ currentIndex--; updateCard(); }}
        else {{ currentIndex = cards.length - 1; updateCard(); }}
      }}

      if (cards.length > 0) updateCard();
    </script>
    </body>
    </html>
    """
    return html_code

# ---------------------------------------------------------
# 8. БОКОВЕ
