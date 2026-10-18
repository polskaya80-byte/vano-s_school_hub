import streamlit as st
import json
import os
import re
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
        padding: 30px !important;
    }

    /* Стилізація радіокнопок у тесті (крупні, зручні варіанти) */
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
# 2. ТЕЛЕГРАМ СПОВІЩЕННЯ
# ---------------------------------------------------------
def send_telegram_notification(subject, topic, test_mode, score_pct, score_text, completed_at):
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
        f"📊 *Результат:* {score_pct}% ({score_text})\n"
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
# 3. ЗЧИТУВАННЯ PDF
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
# 4. ТЕМАТИЧНІ ПРЕСЕТИ
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
# 5. РОЗУМНА ГЕНЕРАЦІЯ
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
# 6. ВІДЖЕТИ ВІДЕО ТА ПРЕЗЕНТАЦІЙ (NOTEBOOKLM LEVEL)
# ---------------------------------------------------------
def render_smart_video(url):
    if not url or not url.strip():
        return
    
    clean_url = url.strip()
    
    # YouTube Normalization
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
# 7. БОКОВЕ МЕНЮ (НАВІГАЦІЯ)
# ---------------------------------------------------------
st.sidebar.title("🦊 RudaFox Hub")
role = st.sidebar.radio(
    "Оберіть простори:", 
    ["🎓 Місце страждань та досягнень Іванка", "🦊 Місце сили RudaFox"]
)

st.sidebar.markdown("---")
st.sidebar.info("Затишний сімейний навчальний простір v3.2 (NotebookLM & Enhanced UI)")

# =========================================================
# РЕЖИМ: МІСЦЕ СИЛИ RUDAFOX
# =========================================================
if role == "🦊 Місце сили RudaFox":
    st.header("🦊 Місце сили RudaFox: Панель Управління")
    
    tab_gen, tab_dash, tab_settings = st.tabs(["🤖 AI-Конструктор Уроків", "📊 Дашборд Досягнень", "⚙️ Налаштування Ключів"])
    
    # -----------------------------------------------------
    # ВКЛАДКА 1: ГЕНЕРАТОР УРОКІВ
    # -----------------------------------------------------
    with tab_gen:
        st.subheader("🛠️ Конструктор нового уроку")
        
        col1, col2 = st.columns(2)
        with col1:
            subject = st.selectbox("Предмет:", [
                "Алгебра", "Геометрія", "Фізика", "Хімія", "Біологія", 
                "Історія України", "Всесвітня історія", "Українська мова", 
                "Українська література", "Англійська мова", "Географія", "Інформатика"
            ])
            lesson_date = st.date_input("Дата проведення:", datetime.today())
        
        with col2:
            topic = st.text_input("Тема уроку (з календарного плану):", placeholder="наприклад: Чинники розміщення виробництва")
            video_url = st.text_input("Посилання на відео (YouTube, Pistacja.tv, сайти):", placeholder="https://...")

        st.markdown("---")
        st.subheader("💻 Презентація (NotebookLM / Google Slides / AI)")
        
        col_pres1, col_pres2 = st.columns(2)
        with col_pres1:
            make_presentation = st.checkbox("🤖 Згенерувати AI-презентацію рівня NotebookLM", value=True)
            selected_theme = st.selectbox("Базовий колірний пресет:", list(THEMES.keys()))
        with col_pres2:
            external_pres_url = st.text_input("Або вкажіть посилання на власну презентацію (NotebookLM / Slides):", placeholder="https://...")
            custom_design_prompt = st.text_input("Побажання до дизайну/атмосфери:", placeholder="наприклад: Скетчбук, S.T.A.L.K.E.R., Minecraft, Ghibli...")

        st.markdown("---")
        st.subheader("💡 Нюанси подачі (Гумор, Лайфхаки, Аналогії)")
        
        content_nuances = st.multiselect(
            "Оберіть фішки для подачі матеріалу:",
            options=[
                "😂 Гумор, жарти та легка іронія",
                "🧠 Мнемонічні лайфхаки для швидкого запам'ятовування",
                "🎮 Аналогії з ігор та серіалів (S.T.A.L.K.E.R., Minecraft, Рік і Морті тощо)",
                "⚡ Короткі 'шпори'-лайфхаки для іспиту",
                "📜 Сюжетна подача (ігровий квест / пригода)"
            ],
            default=["🧠 Мнемонічні лайфхаки для швидкого запам'ятовування"]
        )
        
        custom_nuances_text = st.text_area(
            "Власні побажання щодо тематики, аналогій чи гумору:", 
            placeholder="наприклад: Поясни Закон Ома через аналогію з проходженням КПП у Зоні S.T.A.L.K.E.R..."
        )

        st.markdown("---")
        st.subheader("📚 Власні джерела та файли уроку")
        
        uploaded_pdf = st.file_uploader("📂 Завантажити PDF-файл підручника або конспекту:", type=["pdf", "txt"])
        
        source_materials = st.text_area(
            "Скопійований текст або виписка з NotebookLM:", 
            placeholder="Вставте сюди додатковий текст з NotebookLM чи конспекту...",
            height=110
        )

        st.markdown("---")
        st.subheader("⚙️ Налаштування тесту та флешкарток")
        
        col_opt1, col_opt2 = st.columns(2)
        
        with col_opt1:
            test_mode = st.radio(
                "Категорія тесту:", 
                ["🏋️ Тренувальний (з логічними підказками)", "🎯 Контрольний (сухий контроль знань)"]
            )
            num_questions = st.slider("Кількість питань у тесті:", min_value=3, max_value=24, value=5, step=1)
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

        custom_instructions = st.text_area("Додаткові інструкції (опціонально):", placeholder="наприклад: Зроби акцент на деталях...")
        
        if st.button("🚀 Згенерувати повноцінний урок", type="primary"):
            api_key = st.secrets.get("GEMINI_API_KEY", None) or st.session_state.get("user_gemini_key", "")
            
            if not api_key:
                st.error("❌ Не налаштовано Gemini API Key! Додайте ключ у вкладці 'Налаштування Ключів' або в Secrets.")
            elif not topic:
                st.warning("⚠️ Будь ласка, вкажіть тему уроку.")
            else:
                with st.spinner("🤖 Обробка матеріалів та генерація уроку рівня NotebookLM..."):
                    
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
                    Ти — професійний учитель, методист та сценарист інтерактивного навчання рівня NotebookLM для 9 класу української школи.
                    Створи повноцінний інтерактивний урок за наступними параметрами:
                    - Предмет: {subject}
                    - Тема: {topic}
                    - Категорія тесту: {"ТРЕНУВАЛЬНИЙ (із логічними підказками)" if is_practice else "КОНТРОЛЬНИЙ (без підказок)"}
                    - Складність тесту: {difficulty}
                    - Кількість питань у тесті: {num_questions}
                    - Напрямки/Фокус тесту: {focus_str}
                    - Згенерувати слайди презентації: {"Так (5-7 детальних слайдів рівня NotebookLM)" if make_presentation else "Ні"}
                    - Згенерувати флешкартки: {"Так (5-8 карток)" if generate_flashcards else "Ні"}
                    
                    АТМОСФЕРА, ДИЗАЙН ТА СТИЛЬ ПОДАЧІ:
                    - Кастомний стиль дизайну: {custom_design_prompt if custom_design_prompt else "Затишний крафтовий скетчбук"}
                    - Обрані фішки вмісту: {nuances_str}
                    - Сюжетні аналогії, гумор, мнемонічні лайфхаки від вчителя: {custom_nuances_text if custom_nuances_text else "Немає"}
                    - Додаткові інструкції: {custom_instructions}
                    {source_context}

                    ВИМОГИ ДО ПРЕЗЕНТАЦІЇ (NotebookLM Quality):
                    Кожен слайд повинен містити:
                    1. 'title' - чіткий заголовок слайду.
                    2. 'takeaway' - короткий головний висновок (1 речення).
                    3. 'content' - детальні тези з HTML-форматуванням (використовуй <ul>, <li>, <b> для ключових термінів).

                    Поверни ВІДПОВІДЬ СТРОГО У ФОРМАТІ JSON без додаткового тексту чи markdown-обгортки ```json.
                    
                    Структура JSON:
                    {{
                        "summary": "Зрозумілий конспект уроку з гумором, мнемонічними лайфхаками та візуальними акцентами у форматуванні Markdown (до 350 слів).",
                        "slides": [
                            {{
                                "title": "Слайд 1: Ключове поняття", 
                                "takeaway": "Головний висновок слайду для швидкого розуміння.",
                                "content": "<ul><li><b>Термін:</b> Детальне пояснення...</li><li><b>Приклад:</b> Аналогія...</li></ul>"
                            }}
                        ],
                        "flashcards": [
                            {{"front": "Термін / Лайфхак 1", "back": "Пояснення 1"}}
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
                            "slides": lesson_content.get("slides", []) if make_presentation else [],
                            "flashcards": lesson_content.get("flashcards", []) if generate_flashcards else [],
                            "quiz": lesson_content.get("quiz", [])
                        }
                        
                        db["lessons"].append(new_lesson)
                        save_data(db)
                        
                        st.success(f"✅ Урок з теми '{topic}' успішно створено та додано до розкладу Іванка!")
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

# =========================================================
# РЕЖИМ: МІСЦЕ СТРАЖДАНЬ ТА ДОСЯГНЕНЬ ІВАНКА
# =========================================================
else:
    st.header("🎓 Місце страждань та досягнень Іванка")
    
    if not db["lessons"]:
        st.warning("Наразі немає створених уроків. Зазирни пізніше або попроси RudaFox додати уроки!")
    else:
        available_dates = sorted(list(set([l["date"] for l in db["lessons"]])), reverse=True)
        selected_date = st.selectbox("📅 Оберіть дату навчання:", available_dates)
        
        day_lessons = [l for l in db["lessons"] if l["date"] == selected_date]
        lesson_subjects = [l["subject"] for l in day_lessons]
        
        selected_subject = st.radio("📚 Оберіть предмет:", lesson_subjects, horizontal=True)
        
        current_lesson = next((l for l in day_lessons if l["subject"] == selected_subject), None)
        
        if current_lesson:
            theme_key = current_lesson.get("theme", "🌿 Затишний Скетчбук (Коричневий-Зелений)")
            mode_badge = "🏋️ Тренувальний урок (із підказками)" if current_lesson.get("test_mode") == "Тренувальний" else "🎯 Контрольний урок"
            
            st.markdown(f"## {current_lesson['subject']}: {current_lesson['topic']}")
            st.caption(f"Стиль матеріалів: **{theme_key}** | Режим: **{mode_badge}**")
            
            already_done = next((r for r in db["results"] if r.get("lesson_id") == current_lesson["id"]), None)
            if already_done:
                st.success(f"✅ Цей урок вже виконано! Твій результат: {already_done['score_percent']}% ({already_done['score_text']})")
            
            st.markdown("---")
            
            # 1. ПРЕЗЕНТАЦІЯ (NOTEBOOKLM / AI)
            slides = current_lesson.get("slides", [])
            ext_pres = current_lesson.get("external_pres_url", "")
            if slides or ext_pres:
                st.subheader("💻 1. Інтерактивна слайд-презентація")
                pres_html = render_presentation_html(slides, ext_pres, theme_key)
                if pres_html:
                    st.components.v1.html(pres_html, height=420)
            
            # 2. ТЕОРІЯ
            st.subheader("📖 2. Теоретичний конспект")
            st.markdown(current_lesson["summary"])
            
            # 3. ВІДЕО / ПОСИЛАННЯ (РОЗУМНИЙ ПЛЕЄР)
            if current_lesson.get("video_url"):
                st.subheader("🎬 3. Навчальне відео / Матеріали")
                render_smart_video(current_lesson["video_url"])
            
            # 4. ФЛЕШКАРТКИ
            flashcards = current_lesson.get("flashcards", [])
            if flashcards:
                st.subheader("🎴 4. Інтерактивні флешкартки")
                flashcards_html = render_flashcards_html(flashcards, theme_key)
                st.components.v1.html(flashcards_html, height=340)
            
            # 5. ТЕСТ (ЗБІЛЬШЕНИЙ, ЗРУЧНИЙ БЛОК)
            st.subheader("📝 5. Тест для перевірки знань")
            
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
                        
                        # ВІДПРАВКА В ТЕЛЕГРАМ
                        tg_ok, tg_err = send_telegram_notification(
                            current_lesson["subject"], 
                            current_lesson["topic"], 
                            current_lesson.get("test_mode", "Контрольний"), 
                            score_pct, 
                            f"{correct_count}/{total_q}", 
                            completed_time
                        )
                        
                        st.balloons()
                        if tg_ok:
                            st.success(f"🎉 Урок здано! Твій результат: {correct_count} з {total_q} ({score_pct}%). Сповіщення надіслано в Telegram RudaFox! 📲")
                        else:
                            st.warning(f"🎉 Урок здано! Твій результат: {correct_count} з {total_q} ({score_pct}%).\n\n⚠️ Повідомлення в Telegram не відправилось: {tg_err}")
