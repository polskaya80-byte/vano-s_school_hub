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

st.set_page_config(
    page_title="RudaFox Professional Learning Hub",
    page_icon="🦊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Comfortaa:wght@500;600;700&family=Montserrat:wght@400;500;600;700&family=Neucha&display=swap');

    /* Основний дизайн: Палітра Eco-Craft / Modern Editorial */
    :root {
        --bg-main: #FAF8F5;
        --bg-card: #FFFFFF;
        --bg-sidebar: #F2EDE4;
        --primary-green: #2C4C3B;
        --primary-green-hover: #1E3629;
        --accent-terracotta: #C86D51;
        --accent-terracotta-hover: #A8533A;
        --text-dark: #2D2321;
        --text-muted: #7A6B68;
        --border-color: #E8E2D8;
        --border-dashed: #D6CBD8;
        --shadow-soft: 0 10px 30px rgba(45, 35, 33, 0.05);
        --shadow-card: 0 4px 16px rgba(44, 76, 59, 0.08);
    }

    /* Загальне оформлення сторінки */
    .stApp {
        background-color: var(--bg-main) !important;
        color: var(--text-dark) !important;
        font-family: 'Montserrat', sans-serif !important;
    }

    /* Вишукані заголовки */
    h1, h2, h3, .stHeader {
        font-family: 'Comfortaa', cursive !important;
        color: var(--primary-green) !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }

    h4, h5, h6 {
        font-family: 'Montserrat', sans-serif !important;
        color: var(--accent-terracotta) !important;
        font-weight: 600 !important;
    }

    /* Бічна панель */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border-color) !important;
    }

    /* Преміальні кнопки з м'яким градієнтом */
    .stButton>button {
        background: linear-gradient(135deg, #2C4C3B 0%, #3D6A52 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 10px 24px !important;
        font-family: 'Comfortaa', cursive !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        box-shadow: 0 4px 14px rgba(44, 76, 59, 0.2) !important;
        transition: all 0.25s ease !important;
    }

    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(44, 76, 59, 0.3) !important;
        background: linear-gradient(135deg, #233E30 0%, #325844 100%) !important;
    }

    /* Стильні блоки контейнерів та форм */
    div[data-testid="stForm"], div[data-testid="stExpander"], div.stMarkdown div.hub-card {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 20px !important;
        box-shadow: var(--shadow-soft) !important;
        padding: 24px !important;
        margin-bottom: 20px !important;
    }

    /* Інтерактивні варіанти відповідей у радіокнопках */
    div[role="radiogroup"] label {
        background-color: #FAF8F5 !important;
        border: 1.5px solid var(--border-color) !important;
        border-radius: 14px !important;
        padding: 12px 20px !important;
        margin-bottom: 10px !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }

    div[role="radiogroup"] label:hover {
        border-color: var(--accent-terracotta) !important;
        background-color: #FDF6F0 !important;
    }

    /* Навігаційні вкладки */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        border-bottom: 2px solid var(--border-color);
    }

    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        color: var(--text-muted) !important;
        font-family: 'Comfortaa', cursive !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        padding: 12px 20px !important;
    }

    .stTabs [aria-selected="true"] {
        color: var(--primary-green) !important;
        border-bottom: 3px solid var(--primary-green) !important;
    }

    /* Метрики та прогрес-бари */
    div[data-testid="stMetricValue"] {
        font-family: 'Comfortaa', cursive !important;
        color: var(--primary-green) !important;
        font-weight: 700 !important;
    }

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #2C4C3B 0%, #C86D51 100%) !important;
        border-radius: 10px !important;
    }

    /* Інформаційні дудл-карточки */
    .hub-card {
        background: #FFFFFF;
        border: 1px solid var(--border-color);
        border-radius: 18px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
    }

    .badge-tag {
        display: inline-block;
        background: #F2EDE4;
        color: #2C4C3B;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 700;
        margin-right: 6px;
    }
</style>
""", unsafe_allow_html=True)

DATA_FILE = "lessons_data.json"

def load_data():
    """Завантаження уроків та результатів з JSON-файлу"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    data = {}
                data.setdefault("lessons", [])
                data.setdefault("results", [])
                return data
        except Exception:
            return {"lessons": [], "results": []}
    return {"lessons": [], "results": []}

def save_data(data):
    """Збереження даних уроків та результатів"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

db = load_data()

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
    """Генерація стабільної цитати дня за датою"""
    try:
        seed = int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())
    except Exception:
        seed = 42
    rnd = random.Random(seed)
    q = rnd.choice(MOTIVATIONAL_QUOTES)
    h = rnd.choice(TEEN_LIFEHACKS)
    return q, h

def send_telegram_notification(subject, topic, test_mode, score_pct, score_text, completed_at, day_progress_str=""):
    """Відправка сповіщення про проходження уроку у Telegram"""
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

def extract_text_from_pdf(uploaded_file):
    """Зчитування текстового контенту з завантажених PDF підручників"""
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

THEMES = {
    "🌿 Затишний Еко-Скетчбук": {
        "bg_front": "linear-gradient(135deg, #2C4C3B 0%, #3D6A52 100%)",
        "bg_back": "linear-gradient(135deg, #C86D51 0%, #A65238 100%)",
        "border_front": "#2C4C3B",
        "border_back": "#A65238",
        "slide_bg": "#FFFFFF",
        "slide_text": "#2D2321",
        "slide_accent": "#2C4C3B"
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

def generate_lesson_with_fallback(prompt, api_key):
    """Запит до Gemini API з каскадним перемиканням моделей"""
    genai.configure(api_key=api_key)
    candidate_models = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-flash']
    
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

def render_smart_video(url):
    """Інтелектуальне вбудовування відео з YouTube або Pistacja.tv"""
    if not url or not url.strip():
        return
    clean_url = url.strip()
    yt_match = re.search(r'(?:youtu\.be/|youtube\.com/(?:embed/|v/|watch\?v=|shorts/))([\w-]{11})', clean_url)
    if yt_match:
        yt_id = yt_match.group(1)
        st.video(f"https://www.youtube.com/watch?v={yt_id}")
    elif "pistacja.tv" in clean_url:
        st.markdown(f"""
        <div style="background:#E8F5E9; border:2px dashed #2C4C3B; padding:18px; border-radius:16px; text-align:center; margin-bottom:15px;">
            <h4 style="margin-top:0; color:#2C4C3B;">🎬 Навчальний відеоурок з Pistacja.tv</h4>
            <p style="color:#333; font-size:14px;">Перегляньте матеріал за посиланням нижче:</p>
            <a href="{clean_url}" target="_blank" style="background:#2C4C3B; color:white; padding:10px 22px; border-radius:20px; text-decoration:none; font-weight:bold; display:inline-block;">▶️ Відкрити відео на Pistacja.tv</a>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"🔗 [Перейти до відео/матеріалів уроку]({clean_url})")

def render_presentation_html(slides, external_pres_url, theme_key):
    """Відображення інтерактивної презентації або зовнішнього посилання"""
    if external_pres_url and external_pres_url.strip():
        ext_url = external_pres_url.strip()
        st.markdown(f"""
        <div style="background:#FFFFFF; border:2px dashed #C86D51; padding:20px; border-radius:18px; text-align:center; margin-bottom:15px;">
            <h4 style="margin-top:0; color:#C86D51;">💻 Інтегрована презентація (NotebookLM / Google Slides)</h4>
            <p style="font-size:14px; color:#555;">Клацніть кнопку, щоб відкрити повномасштабну презентацію:</p>
            <a href="{ext_url}" target="_blank" style="background:#C86D51; color:white; padding:12px 26px; border-radius:25px; text-decoration:none; font-weight:bold; display:inline-block; box-shadow:0 4px 12px rgba(200,109,81,0.3);">🚀 Відкрити презентацію у повному вікні</a>
        </div>
        """, unsafe_allow_html=True)
        return None

    if not slides:
        return None
    
    theme = THEMES.get(theme_key, THEMES["🌿 Затишний Еко-Скетчбук"])
    slides_json = json.dumps(slides, ensure_ascii=False)
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <link href="https://fonts.googleapis.com/css2?family=Comfortaa:wght@700&family=Montserrat:wght@400;600&display=swap" rel="stylesheet">
    <style>
      body {{ font-family: 'Montserrat', sans-serif; background: transparent; margin: 0; padding: 10px; display: flex; flex-direction: column; align-items: center; }}
      .slide-container {{ width: 100%; max-width: 820px; min-height: 340px; background: {theme['slide_bg']}; color: {theme['slide_text']}; border-radius: 20px; border: 2px solid #E8E2D8; padding: 30px; box-sizing: border-box; box-shadow: 0 8px 24px rgba(0,0,0,0.06); position: relative; display: flex; flex-direction: column; justify-content: space-between; }}
      .slide-title {{ font-family: 'Comfortaa', cursive; font-size: 24px; font-weight: 700; color: {theme['slide_accent']}; margin-bottom: 12px; border-bottom: 2px solid #E8E2D8; padding-bottom: 8px; }}
      .takeaway-box {{ background: rgba(44, 76, 59, 0.08); border-left: 4px solid {theme['slide_accent']}; padding: 10px 15px; margin-bottom: 15px; font-size: 14px; font-weight: 600; border-radius: 4px; color: #2C4C3B; }}
      .slide-content {{ font-size: 15px; line-height: 1.7; flex-grow: 1; }}
      .slide-content ul {{ margin-top: 5px; padding-left: 20px; }}
      .slide-content li {{ margin-bottom: 8px; }}
      .controls {{ display: flex; justify-content: space-between; align-items: center; margin-top: 20px; }}
      .btn {{ background-color: {theme['slide_accent']}; color: white; border: none; padding: 10px 24px; border-radius: 20px; cursor: pointer; font-family: 'Comfortaa', cursive; font-weight: 700; font-size: 14px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); transition: all 0.2s; }}
      .btn:hover {{ opacity: 0.9; transform: translateY(-1px); }}
      .counter {{ font-family: 'Comfortaa', cursive; font-size: 15px; font-weight: 700; color: #7A6B68; }}
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
    """Генератор інтерактивних 3D-флешкарток"""
    if not flashcards:
        return ""
    
    theme = THEMES.get(theme_key, THEMES["🌿 Затишний Еко-Скетчбук"])
    cards_data_json = json.dumps(flashcards, ensure_ascii=False)
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <link href="https://fonts.googleapis.com/css2?family=Comfortaa:wght@700&family=Montserrat:wght@500;600&display=swap" rel="stylesheet">
    <style>
      body {{ font-family: 'Montserrat', sans-serif; background: transparent; margin: 0; padding: 10px; display: flex; flex-direction: column; align-items: center; }}
      .scene {{ width: 100%; max-width: 500px; height: 240px; perspective: 1000px; cursor: pointer; }}
      .card {{ width: 100%; height: 100%; position: relative; transform-style: preserve-3d; transition: transform 0.6s cubic-bezier(0.4, 0.2, 0.2, 1); border-radius: 20px; box-shadow: 0 8px 20px rgba(0,0,0,0.08); }}
      .card.is-flipped {{ transform: rotateY(180deg); }}
      .card-face {{ position: absolute; width: 100%; height: 100%; backface-visibility: hidden; border-radius: 20px; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 25px; box-sizing: border-box; text-align: center; font-size: 16px; line-height: 1.5; font-weight: 500; }}
      .card-front {{ background: {theme['bg_front']}; color: #ffffff; border: 2px solid {theme['border_front']}; }}
      .card-back {{ background: {theme['bg_back']}; color: #ffffff; transform: rotateY(180deg); border: 2px solid {theme['border_back']}; }}
      .hint {{ font-family: 'Comfortaa', cursive; font-size: 13px; margin-top: 12px; opacity: 0.85; letter-spacing: 0.5px; }}
      .controls {{ display: flex; gap: 15px; align-items: center; margin-top: 15px; }}
      .btn {{ background-color: {theme['slide_accent']}; color: white; border: none; padding: 8px 20px; border-radius: 20px; cursor: pointer; font-family: 'Comfortaa', cursive; font-weight: 700; font-size: 14px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); transition: all 0.2s; }}
      .btn:hover {{ opacity: 0.9; transform: translateY(-1px); }}
      .counter {{ font-family: 'Comfortaa', cursive; font-size: 15px; font-weight: 700; color: #7A6B68; }}
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

st.sidebar.title("🦊 RudaFox Hub")
role = st.sidebar.radio(
    "Оберіть простори:", 
    ["🎓 Місце страждань та досягнень Іванка", "🦊 Місце сили RudaFox"]
)

st.sidebar.markdown("---")
st.sidebar.info("Преміальний сімейний навчальний простір v4.5 (Interactive HTML Trainer Studio)")

if role == "🦊 Місце сили RudaFox":
    st.header("🦊 Місце сили RudaFox: Панель Управління")
    
    tab_gen, tab_dash, tab_settings = st.tabs(["🤖 AI-Конструктор Уроків", "📊 Дашборд Досягнень", "⚙️ Налаштування Ключів"])
    
    # -----------------------------------------------------
    # ВКЛАДКА 1: ГЕНЕРАТОР УРОКІВ ТА HTML-ТРЕНАЖЕРІВ
    # -----------------------------------------------------
    with tab_gen:
        st.subheader("🛠️ Конструктор покрокового уроку та HTML-тренажера")
        
        col1, col2 = st.columns(2)
        with col1:
            subject = st.selectbox("Предмет:", [
                "Алгебра", "Геометрія", "Фізика", "Хімія", "Біологія", 
                "Історія України", "Всесвітня історія", "Українська мова", 
                "Українська література", "Англійська мова", "Географія", "Інформатика"
            ])
            lesson_date = st.date_input("Дата проведення:", datetime.today())
        
        with col2:
            topic = st.text_input("Тема уроку (з календарного плану):", placeholder="наприклад: Закони Постійного Струму")
            video_url = st.text_input("Посилання на навчальне відео (YouTube, Pistacja.tv):", placeholder="https://...")

        st.markdown("---")
        st.subheader("💡 Формат матеріалів, мультимедіа та HTML-тренажера")
        
        col_pres1, col_pres2 = st.columns(2)
        with col_pres1:
            make_html_game = st.checkbox("🎮 Згенерувати повноцінний інтерактивний HTML-Урок / Тренажер для Іванка", value=True)
            make_presentation = st.checkbox("💻 Згенерувати AI-презентацію рівня NotebookLM", value=True)
            selected_theme = st.selectbox("Базовий колірний пресет:", list(THEMES.keys()))
        with col_pres2:
            external_pres_url = st.text_input("Посилання на власну презентацію (NotebookLM / Slides):", placeholder="https://...")
            custom_design_prompt = st.text_input("Побажання до стилю/атмосфери:", placeholder="наприклад: Еко-Скетчбук, S.T.A.L.K.E.R., Minecraft, Studio Ghibli...")

        st.markdown("---")
        st.subheader("🎯 Педагогічна методика для підлітка 13 років")
        
        content_nuances = st.multiselect(
            "Оберіть методичні прийоми подачі матеріалу:",
            options=[
                "😂 Гумор, легка іронія та мемні аналогії",
                "🧠 Мнемонічні правила та лайфхаки для швидкого запам'ятовування",
                "🎮 Аналогії з ігор та серіалів (S.T.A.L.K.E.R., Minecraft, Рік і Морті тощо)",
                "⚡ Короткі 'шпори'-лайфхаки для контрольної",
                "📜 Покрокова сюжетна подача (від простого до складного)"
            ],
            default=["🧠 Мнемонічні правила та лайфхаки для швидкого запам'ятовування", "📜 Покрокова сюжетна подача (від простого до складного)"]
        )
        
        custom_nuances_text = st.text_area(
            "Власні побажання щодо тематики, аналогій чи сюжету:", 
            placeholder="наприклад: Поясни Закон Ома через аналогію з проходженням КПП у Зоні S.T.A.L.K.E.R. з балами за правильний розрахунок..."
        )

        st.markdown("---")
        st.subheader("📚 Джерела, PDF підручники або Власний HTML-код")
        
        uploaded_pdf = st.file_uploader("📂 Завантажити PDF підручника або параграф:", type=["pdf", "txt"])
        
        source_materials = st.text_area(
            "Скопійований текст або виписка з NotebookLM:", 
            placeholder="Вставте сюди додатковий текст з підручника, конспекту або NotebookLM...",
            height=100
        )
        
        manual_html_code = st.text_area(
            "Власний HTML/JS код тренажера (опціонально, якщо зібрано вручну):",
            placeholder="<!DOCTYPE html><html>... (якщо залишити порожнім — ШІ згенерує автономний HTML-модуль самостійно)</html>",
            height=100
        )

        st.markdown("---")
        st.subheader("⚙️ Налаштування тесту та флешкарток")
        
        col_opt1, col_opt2 = st.columns(2)
        
        with col_opt1:
            test_mode = st.radio(
                "Категорія тесту:", 
                ["🏋️ Тренувальний (з логічними підказками)", "🎯 Контрольний (сухий контроль знань)"]
            )
            num_questions = st.slider("Кількість питань у тесті:", min_value=3, max_value=20, value=5, step=1)
            generate_flashcards = st.checkbox("🎴 Згенерувати 3D-флешкартки для термінів", value=True)
            
        with col_opt2:
            difficulty = st.selectbox("Рівень складності:", ["Базовий", "Середній", "Поглиблений / Олімпіадний"])
            quiz_focus = st.multiselect(
                "Фокус тесту (можна обрати декілька):", 
                options=[
                    "Загальна теорія та терміни", 
                    "Формули та практичні задачі", 
                    "Дати, події та ключові факти", 
                    "Критичне мислення та аналіз"
                ],
                default=["Загальна теорія та терміни"]
            )

        custom_instructions = st.text_area("Додаткові інструкції вчителю (опціонально):", placeholder="наприклад: Зроби акцент на практичних прикладах з життя...")
        
        if st.button("✨ Згенерувати повноцінний урок", type="primary"):
            api_key = st.secrets.get("GEMINI_API_KEY", None) or st.session_state.get("user_gemini_key", "")
            
            if not api_key:
                st.error("❌ Не налаштовано Gemini API Key! Додайте ключ у вкладці 'Налаштування Ключів' або в Secrets.")
            elif not topic:
                st.warning("⚠️ Будь ласка, вкажіть тему уроку.")
            else:
                with st.spinner("🤖 Методична обробка та генерація покрокового інтерактивного уроку..."):
                    
                    pdf_text = ""
                    if uploaded_pdf:
                        if uploaded_pdf.name.endswith(".pdf"):
                            pdf_text = extract_text_from_pdf(uploaded_pdf)
                        else:
                            pdf_text = uploaded_pdf.read().decode("utf-8", errors="ignore")
                    
                    combined_source = (source_materials.strip() + "\n" + pdf_text).strip()
                    source_context = f"\nБАЗОВІ МАТЕРІАЛИ ТА ТЕКСТ З ПІДРУЧНИКА/PDF/NOTEBOOKLM:\n{combined_source}\n" if combined_source else ""
                    
                    is_practice = "Тренувальний" in test_mode
                    focus_str = ", ".join(quiz_focus) if quiz_focus else "Загальна теорія та терміни"
                    nuances_str = ", ".join(content_nuances) if content_nuances else "Стандартна подача"
                    
                    prompt = f"""
                    Ти — висококваліфікований методист та розробник навчальних програм для 9 класу української школи.
                    Створи повноцінний, покроковий та захоплюючий урок для підлітка 13 років (Іванка), який навчається ПОВНІСТЮ САМОСТІЙНО.

                    Параметри уроку:
                    - Предмет: {subject}
                    - Тема: {topic}
                    - Категорія тесту: {"ТРЕНУВАЛЬНИЙ (із логічними підказками)" if is_practice else "КОНТРОЛЬНИЙ (без підказок)"}
                    - Складність тесту: {difficulty}
                    - Кількість питань у тесті: {num_questions}
                    - Напрямки/Фокус тесту: {focus_str}
                    - Згенерувати інтерактивний HTML-Тренажер/Урок: {"Так" if make_html_game else "Ні"}
                    - Згенерувати слайди презентації: {"Так (5-7 детальних слайдів)" if make_presentation else "Ні"}
                    - Згенерувати флешкартки: {"Так (5-8 карток)" if generate_flashcards else "Ні"}
                    
                    ПЕДАГОГІЧНА СТРУКТУРА ТА СТИЛЬ ПОДАЧІ:
                    - Обов'язково проводь учня ПОКРОКОВО від простого до складного (Крок 1: Вступ і мотивація -> Крок 2: Пояснення та мнемоніка -> Крок 3: Практичний приклад -> Крок 4: Підсумок).
                    - Включай мнемонічні лайфхаки, легкий гумор, мнемоніку та яскраві аналогії.
                    - Кастомний стиль: {custom_design_prompt if custom_design_prompt else "Затишний стильний Еко-Скетчбук"}
                    - Обрані фішки вмісту: {nuances_str}
                    - Власні побажання: {custom_nuances_text if custom_nuances_text else "Немає"}
                    - Додаткові інструкції: {custom_instructions}
                    {source_context}

                    ВИМОГИ ДО HTML-ТРЕНАЖЕРА (html_game_code):
                    Якщо замовлено, створи ПОВНОЦІННИЙ, стильний HTML/JS модуль (автономна веб-сторінка з CSS та JavaScript у єдиному блоці), що містить:
                    - Покрокові інтерактивні картки або квест із кнопками перевірки дій.
                    - Інтерактивні підказки та розбір помилок.
                    - Гарне візуальне оформлення під тему.

                    Поверни ВІДПОВІДЬ СТРОГО У ФОРМАТІ JSON без додаткового тексту чи markdown-обгортки ```json.
                    
                    Структура JSON:
                    {{
                        "summary": "Зрозумілий, покроковий конспект уроку з мнемонічними лайфхаками та візуальними акцентами у форматуванні Markdown (до 400 слів).",
                        "html_game_code": "<!DOCTYPE html><html>... стильний інтерактивний тренажер ...</html>",
                        "slides": [
                            {{
                                "title": "Крок 1: Вступ", 
                                "takeaway": "Головний висновок кроку.",
                                "content": "<ul><li><b>Термін:</b> Пояснення...</li></ul>"
                            }}
                        ],
                        "flashcards": [
                            {{"front": "Термін 1", "back": "Пояснення 1"}}
                        ],
                        "quiz": [
                            {{
                                "question": "Текст питання 1?",
                                "options": ["Варіант A", "Варіант B", "Варіант C", "Варіант D"],
                                "correct_idx": 0,
                                "explanation": "Пояснення.",
                                "hint": "Логічна підказка"
                            }}
                        ]
                    }}
                    """
                    try:
                        raw_text = generate_lesson_with_fallback(prompt, api_key)
                        clean_text = raw_text.strip()
                        if clean_text.startswith("```json"):
                            clean_text = clean_text[7:]
                        if clean_text.endswith("```"):
                            clean_text = clean_text[:-3]
                        
                        lesson_content = json.loads(clean_text)
                        
                        final_html = manual_html_code.strip() if manual_html_code.strip() else lesson_content.get("html_game_code", "")
                        
                        new_lesson = {
                            "id": f"{subject}_{lesson_date.strftime('%Y%m%d')}_{len(db['lessons'])}",
                            "subject": subject,
                            "date": str(lesson_date),
                            "topic": topic,
                            "video_url": video_url,
                            "external_pres_url": external_pres_url,
                            "theme": selected_theme,
                            "test_mode": "Тренувальний" if is_practice else "Контрольний",
                            "summary": lesson_content.get("summary", ""),
                            "html_game_code": final_html,
                            "slides": lesson_content.get("slides", []) if make_presentation else [],
                            "flashcards": lesson_content.get("flashcards", []) if generate_flashcards else [],
                            "quiz": lesson_content.get("quiz", [])
                        }
                        
                        db["lessons"].append(new_lesson)
                        save_data(db)
                        
                        st.success(f"✅ Покроковий урок з теми '{topic}' успішно створено та додано до розкладу!")
                        st.json(new_lesson)
                    except Exception as e:
                        st.error(f"Помилка при генерації уроку: {e}")

    # -----------------------------------------------------
    # ВКЛАДКА 2: ДАШБОРД УСПІШНОСТІ
    # -----------------------------------------------------
    with tab_dash:
        st.subheader("📊 Зведена таблиця результатів Іванка")
        
        if not db["results"]:
            st.info("Поки немає зданих уроків. Результати з'являться тут одразу після виконання завдань Іванком.")
        else:
            df_results = pd.DataFrame(db["results"])
            st.dataframe(
                df_results[['date', 'subject', 'topic', 'test_mode', 'score_percent', 'score_text', 'completed_at']],
                column_config={
                    "date": "Дата уроку",
                    "subject": "Предмет",
                    "topic": "Тема",
                    "test_mode": "Тип тесту",
                    "score_percent": st.column_config.ProgressColumn("Результат (%)", format="%d%%", min_value=0, max_value=100),
                    "score_text": "Правильних відповідей",
                    "completed_at": "Час здачі"
                },
                use_container_width=True
            )

    # -----------------------------------------------------
    # ВКЛАДКА 3: НАЛАШТУВАННЯ КЛЮЧІВ ТА ТЕЛЕГРАМ
    # -----------------------------------------------------
    with tab_settings:
        st.subheader("⚙️ Ключі доступу")
        key_input = st.text_input("Введіть ваш Gemini API Key:", value=st.session_state.get("user_gemini_key", ""), type="password")
        if st.button("Зберегти Gemini Key"):
            st.session_state["user_gemini_key"] = key_input
            st.success("Gemini Key збережено в сесії!")
        
        st.markdown("---")
        st.subheader("📲 Налаштування Telegram-сповіщень")
        tg_token = st.text_input("Bot Token (з @BotFather):", value=st.session_state.get("user_tg_token", ""), type="password")
        tg_chat_id = st.text_input("Your Chat ID (з @userinfobot):", value=st.session_state.get("user_tg_chat_id", ""))
        
        if st.button("Зберегти ключі Telegram"):
            st.session_state["user_tg_token"] = tg_token
            st.session_state["user_tg_chat_id"] = tg_chat_id
            st.success("Налаштування Telegram збережено!")

else:
    st.header("🎓 Місце страждань та досягнень Іванка")
    
    if not db["lessons"]:
        st.warning("Наразі немає створених уроків. Зазирни пізніше або попроси RudaFox додати уроки!")
    else:
        tab_student_daily, tab_student_progress = st.tabs(["🎯 Квести Дня & Уроки", "📊 Мій Супер-Прогрес"])
        
        # -------------------------------------------------
        # ВКЛАДКА 1: КВЕСТИ ДНЯ ТА ДАШБОРД
        # -------------------------------------------------
        with tab_student_daily:
            available_dates = sorted(list(set([l["date"] for l in db["lessons"]])), reverse=True)
            selected_date = st.selectbox("📅 Оберіть дату навчання:", available_dates)
            
            day_lessons = [l for l in db["lessons"] if l["date"] == selected_date]
            total_day_count = len(day_lessons)
            
            completed_ids = [r["lesson_id"] for r in db["results"]]
            done_day_count = sum(1 for l in day_lessons if l["id"] in completed_ids)
            pct_done = int((done_day_count / total_day_count) * 100) if total_day_count > 0 else 0
            
            quote, hack = get_daily_quote_and_hack(selected_date)
            
            if pct_done == 0:
                status_msg = "🧟 **Статус Зони:** Борги висять, як ментальний дебаф! Час розміновувати першу таску."
                status_color = "warning"
            elif pct_done < 50:
                status_msg = "🐢 **Перший квест закрито!** Але борги все ще дивляться на тебе з докором."
                status_color = "info"
            elif pct_done < 100:
                status_msg = "🏃💨 **Екватор подолано!** Ще трохи — і чистий сейв та воля!"
                status_color = "info"
            else:
                status_msg = "🎉 **АБСОЛЮТНИЙ СЕЙВ!** Всі таски закриті, кукуха в безпеці, RudaFox пишається!"
                status_color = "success"
                
            st.markdown(f"""
            <div class="hub-card">
                <h3 style="margin-top:0;">📜 Мудрість Дня & Підтримка Кукухи</h3>
                <p style="font-size:15px; font-style:italic; color:#2C4C3B;">{quote}</p>
                <hr style="border:0; border-top:1px solid #E8E2D8; margin:12px 0;">
                <p style="font-size:14px; margin-bottom:0;">{hack}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.subheader(f"📊 Прогрес за {selected_date}: {done_day_count} з {total_day_count} уроків ({pct_done}%)")
            st.progress(pct_done / 100.0)
            
            if status_color == "success":
                st.success(status_msg)
            elif status_color == "warning":
                st.warning(status_msg)
            else:
                st.info(status_msg)
            
            st.markdown("---")
            st.subheader("📋 Чеклист запланованого на цей день:")
            
            checklist_data = []
            for l in day_lessons:
                res = next((r for r in db["results"] if r.get("lesson_id") == l["id"]), None)
                if res:
                    st_text = f"✅ Виконано ({res['score_percent']}%)"
                    score_val = res['score_text']
                else:
                    st_text = "⏳ Висит у боргах"
                    score_val = "—"
                
                checklist_data.append({
                    "Предмет": l["subject"],
                    "Тема": l["topic"],
                    "Режим": l.get("test_mode", "Контрольний"),
                    "Статус": st_text,
                    "Результат": score_val
                })
            
            st.dataframe(pd.DataFrame(checklist_data), use_container_width=True)
            
            st.markdown("---")
            st.subheader("📚 Вибір уроку для проходження:")
            
            lesson_subjects = [l["subject"] for l in day_lessons]
            selected_subject = st.radio("Оберіть предмет:", lesson_subjects, horizontal=True)
            current_lesson = next((l for l in day_lessons if l["subject"] == selected_subject), None)
            
            if current_lesson:
                theme_key = current_lesson.get("theme", "🌿 Затишний Еко-Скетчбук")
                mode_badge = "🏋️ Тренувальний урок (із підказками)" if current_lesson.get("test_mode") == "Тренувальний" else "🎯 Контрольний урок"
                
                st.markdown(f"### {current_lesson['subject']}: {current_lesson['topic']}")
                st.caption(f"Стиль матеріалів: **{theme_key}** | Режим: **{mode_badge}**")
                
                already_done = next((r for r in db["results"] if r.get("lesson_id") == current_lesson["id"]), None)
                if already_done:
                    st.success(f"✅ Цей урок вже виконано! Твій результат: {already_done['score_percent']}% ({already_done['score_text']})")
                
                st.markdown("---")
                
                # 1. ІНТЕРАКТИВНИЙ HTML-УРОК / ТРЕНАЖЕР
                html_game = current_lesson.get("html_game_code", "")
                if html_game and html_game.strip():
                    st.subheader("🎮 1. Інтерактивний HTML-Урок / Тренажер")
                    st.components.v1.html(html_game, height=480, scrolling=True)
                
                # 2. ПРЕЗЕНТАЦІЯ
                slides = current_lesson.get("slides", [])
                ext_pres = current_lesson.get("external_pres_url", "")
                if slides or ext_pres:
                    st.subheader("💻 2. Інтерактивна слайд-презентація")
                    pres_html = render_presentation_html(slides, ext_pres, theme_key)
                    if pres_html:
                        st.components.v1.html(pres_html, height=420)
                
                # 3. ТЕОРІЯ
                st.subheader("📖 3. Покроковий теоретичний конспект")
                st.markdown(current_lesson["summary"])
                
                # 4. ВІДЕО / ПОСИЛАННЯ
                if current_lesson.get("video_url"):
                    st.subheader("🎬 4. Навчальне відео / Матеріали")
                    render_smart_video(current_lesson["video_url"])
                
                # 5. ФЛЕШКАРТКИ
                flashcards = current_lesson.get("flashcards", [])
                if flashcards:
                    st.subheader("🎴 5. Інтерактивні флешкартки")
                    flashcards_html = render_flashcards_html(flashcards, theme_key)
                    st.components.v1.html(flashcards_html, height=340)
                
                # 6. ТЕСТ
                st.subheader("📝 6. Тест для перевірки знань")
                
                quiz = current_lesson.get("quiz", [])
                user_answers = {}
                
                if not quiz:
                    st.info("Для цього уроку немає тестів.")
                else:
                    with st.form(key=f"quiz_form_{current_lesson['id']}"):
                        for idx, q in enumerate(quiz):
                            st.markdown(f"#### ❓ Питання {idx+1}: {q['question']}")
                            
                            if current_lesson.get("test_mode") == "Тренувальний" and q.get("hint"):
                                with st.expander("💡 Отримати логічну підказку / натяк"):
                                    st.info(q["hint"])
                            
                            user_answers[idx] = st.radio(
                                f"Оберіть один із варіантів відповідей:", 
                                q['options'], 
                                key=f"q_{current_lesson['id']}_{idx}",
                                index=None
                            )
                            st.markdown("---")
                        
                        submit_button = st.form_submit_button("🚀 Завершити та здати урок", type="primary")
                    
                    if submit_button:
                        if None in user_answers.values():
                            st.warning("⚠️ Будь ласка, дай відповідь на всі питання тесту перед здачею!")
                        else:
                            correct_count = 0
                            for idx, q in enumerate(quiz):
                                selected_option = user_answers[idx]
                                correct_option = q['options'][q['correct_idx']]
                                if selected_option == correct_option:
                                    correct_count += 1
                            
                            total_q = len(quiz)
                            score_pct = int((correct_count / total_q) * 100) if total_q > 0 else 100
                            completed_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            result_record = {
                                "lesson_id": current_lesson["id"],
                                "date": current_lesson["date"],
                                "subject": current_lesson["subject"],
                                "topic": current_lesson["topic"],
                                "test_mode": current_lesson.get("test_mode", "Контрольний"),
                                "score_percent": score_pct,
                                "score_text": f"{correct_count}/{total_q}",
                                "completed_at": completed_time
                            }
                            
                            db["results"] = [r for r in db["results"] if r.get("lesson_id") != current_lesson["id"]]
                            db["results"].append(result_record)
                            save_data(db)
                            
                            new_done_count = sum(1 for l_item in day_lessons if any(r_item["lesson_id"] == l_item["id"] for r_item in db["results"]))
                            day_progress_str = f"{new_done_count} з {total_day_count} уроків закрито ({int((new_done_count/total_day_count)*100)}%)"
                            
                            # ВІДПРАВКА В ТЕЛЕГРАМ
                            tg_ok, tg_err = send_telegram_notification(
                                current_lesson["subject"], 
                                current_lesson["topic"], 
                                current_lesson.get("test_mode", "Контрольний"), 
                                score_pct, 
                                f"{correct_count}/{total_q}", 
                                completed_time,
                                day_progress_str
                            )
                            
                            st.balloons()
                            if tg_ok:
                                st.success(f"🎉 Урок здано! Твій результат: {correct_count} з {total_q} ({score_pct}%). Сповіщення надіслано в Telegram RudaFox! 📲")
                            else:
                                st.warning(f"🎉 Урок здано! Твій результат: {correct_count} з {total_q} ({score_pct}%).\n\n⚠️ Повідомлення в Telegram не відправилось: {tg_err}")

        # -------------------------------------------------
        # ВКЛАДКА 2: СУПЕР-ПРОГРЕС
        # -------------------------------------------------
        with tab_student_progress:
            st.subheader("📈 Загальний аналіз прогресу та ачівок")
            
            if not db["results"]:
                st.info("Поки немає даних для прогресу. Виконай перші уроки, щоб відкрити графіки успішності!")
            else:
                df_res = pd.DataFrame(db["results"])
                
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric("Виконано уроків всього:", len(df_res))
                with col_m2:
                    avg_score = int(df_res["score_percent"].mean())
                    st.metric("Середній бал за тести:", f"{avg_score}%")
                with col_m3:
                    top_subject = df_res["subject"].mode()[0] if not df_res.empty else "—"
                    st.metric("Найактивніший предмет:", top_subject)
                
                st.markdown("---")
                st.subheader("📚 Прогрес за окремими предметами:")
                
                subject_stats = df_res.groupby("subject").agg(
                    total_done=("lesson_id", "count"),
                    avg_pct=("score_percent", "mean")
                ).reset_index()
                
                for _, row in subject_stats.iterrows():
                    subj_name = row["subject"]
                    avg_p = int(row["avg_pct"])
                    count_d = row["total_done"]
                    
