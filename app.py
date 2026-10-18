import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd
import google.generativeai as genai

# ---------------------------------------------------------
# 1. НАЛАШТУВАННЯ СТОРІНКИ ТА СТИЛІВ
# ---------------------------------------------------------
st.set_page_config(
    page_title="Навчальний Хаб 9 Клас",
    page_icon="🎓",
    layout="wide"
)

# Шлях до локального файлу збереження (fallback, якщо немає Google Sheets)
DATA_FILE = "lessons_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"lessons": [], "results": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Завантажуємо актуальні дані
db = load_data()

# ---------------------------------------------------------
# 2. НАЛАШТУВАННЯ GEMINI API
# ---------------------------------------------------------
def get_gemini_model():
    api_key = st.secrets.get("GEMINI_API_KEY", None)
    if not api_key:
        api_key = st.session_state.get("user_gemini_key", "")
    
    if api_key:
        genai.configure(api_key=api_key)
        # 1. Спроба автоматично знайти найновішу активну модель Flash від Google
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods and 'flash' in m.name:
                    return genai.GenerativeModel(m.name)
        except Exception:
            pass
        
        # 2. Резервний перебір версій, якщо список моделей недоступний
        for name in ['gemini-3.8-flash', 'gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-flash']:
            try:
                return genai.GenerativeModel(name)
            except Exception:
                continue
    return None
# ---------------------------------------------------------
# 3. БОКОВЕ МЕНЮ (НАВІГАЦІЯ)
# ---------------------------------------------------------
st.sidebar.title("🎓 Навчальний Хаб")
role = st.sidebar.radio("Оберіть режим:", ["🎓 Кабінет Учня", "👩‍🏫 Кабінет Мами"])

st.sidebar.markdown("---")
st.sidebar.info("Система сімейного навчання 9 класу v2.0 (Автоматизована)")

# =========================================================
# РЕЖИМ: КАБІНЕТ МАМИ (ГЕНЕРАЦІЯ ТА МОНІТОРИНГ)
# =========================================================
if role == "👩‍🏫 Кабінет Мами":
    st.header("👩‍🏫 Панель Управління Навчанням")
    
    tab_gen, tab_dash, tab_settings = st.tabs(["🤖 AI-Генератор Уроків", "📊 Дашборд Успішності", "⚙️ Налаштування Ключів"])
    
    # -----------------------------------------------------
    # ВКЛАДКА 1: ГЕНЕРАТОР УРОКІВ ЧЕРЕЗ GEMINI API
    # -----------------------------------------------------
    with tab_gen:
        st.subheader("Створення нового уроку в 1 клік")
        
        col1, col2 = st.columns(2)
        with col1:
            subject = st.selectbox("Предмет:", [
                "Алгебра", "Геометрія", "Фізика", "Хімія", "Біологія", 
                "Історія України", "Всесвітня історія", "Українська мова", 
                "Українська література", "Англійська мова", "Географія", "Інформатика"
            ])
            lesson_date = st.date_input("Дата проведения:", datetime.today())
        
        with col2:
            topic = st.text_input("Тема уроку (з календарного плану):", placeholder="наприклад: Закон Ома для ділянки кола")
            youtube_url = st.text_input("Посилання на YouTube / Pistacja (опціонально):", placeholder="https://www.youtube.com/watch?v=...")

        custom_instructions = st.text_area("Додаткові побажання до уроку (опціонально):", placeholder="наприклад: Зроби акцент на практичних задачах з формулами")
        
        if st.button("🚀 Згенерувати повноцінний урок", type="primary"):
            model = get_gemini_model()
            if not model:
                st.error("❌ Не налаштовано Gemini API Key! Додайте ключ у вкладці 'Налаштування Ключів'.")
            elif not topic:
                st.warning("⚠️ Будь ласка, вкажіть тему уроку.")
            else:
                with st.spinner("🤖 Gemini створює конспект, тести та HTML-тренажер... Зачекайте 10-15 секунд..."):
                    prompt = f"""
                    Ти — професійний учитель та методист для 9 класу української школи.
                    Створи повноцінний інтерактивний урок за наступними параметрами:
                    - Предмет: {subject}
                    - Тема: {topic}
                    - Додаткові вимоги: {custom_instructions}

                    Поверни ВІДПОВІДЬ СТРОГО У ФОРМАТІ JSON без додаткового тексту чи markdown-обгортки ```json.
                    Структура JSON:
                    {{
                        "summary": "Короткий, зрозумілий конспект уроку з виділенням головних термінів у форматуванні Markdown (до 250 слів).",
                        "quiz": [
                            {{
                                "question": "Текст питання 1?",
                                "options": ["Варіант A", "Варіант B", "Варіант C", "Варіант D"],
                                "correct_idx": 0,
                                "explanation": "Пояснення, чому саме цей варіант правильний."
                            }},
                            {{
                                "question": "Текст питання 2?",
                                "options": ["Варіант A", "Варіант B", "Варіант C", "Варіант D"],
                                "correct_idx": 1,
                                "explanation": "Пояснення."
                            }},
                            {{
                                "question": "Текст питання 3?",
                                "options": ["Варіант A", "Варіант B", "Варіант C", "Варіант D"],
                                "correct_idx": 2,
                                "explanation": "Пояснення."
                            }}
                        ],
                        "html_game": "<div style='font-family:sans-serif; text-align:center; padding:15px; background:#f0f2f6; border-radius:10px;'><h3>🎮 Міні-тренажер: Перевірка понять</h3><p>Визначте ключовий термін уроку!</p></div>"
                    }}
                    """
                    try:
                        response = model.generate_content(prompt)
                        clean_text = response.text.strip()
                        if clean_text.startswith("```json"):
                            clean_text = clean_text[7:]
                        if clean_text.endswith("```"):
                            clean_text = clean_text[:-3]
                        
                        lesson_content = json.loads(clean_text)
                        
                        # Зберігаємо урок у базу
                        new_lesson = {
                            "id": f"{subject}_{lesson_date.strftime('%Y%m%d')}_{len(db['lessons'])}",
                            "subject": subject,
                            "date": str(lesson_date),
                            "topic": topic,
                            "youtube_url": youtube_url,
                            "summary": lesson_content.get("summary", ""),
                            "quiz": lesson_content.get("quiz", []),
                            "html_game": lesson_content.get("html_game", "")
                        }
                        
                        db["lessons"].append(new_lesson)
                        save_data(db)
                        
                        st.success(f"✅ Урок з теми '{topic}' успішно створено та додано до розкладу!")
                        st.json(new_lesson)
                    except Exception as e:
                        st.error(f"Помилка при генерації уроку: {e}")

    # -----------------------------------------------------
    # ВКЛАДКА 2: ДАШБОРД УСПІШНОСТІ
    # -----------------------------------------------------
    with tab_dash:
        st.subheader("📊 Зведена таблиця результатів сина")
        
        if not db["results"]:
            st.info("Поки немає зданих уроків. Результати з'являться тут одразу після виконання завдань сином.")
        else:
            df_results = pd.DataFrame(db["results"])
            st.dataframe(
                df_results[['date', 'subject', 'topic', 'score_percent', 'score_text', 'completed_at']],
                column_config={
                    "date": "Дата уроку",
                    "subject": "Предмет",
                    "topic": "Тема",
                    "score_percent": st.column_config.ProgressColumn("Результат (%)", format="%d%%", min_value=0, max_value=100),
                    "score_text": "Правильних відповідей",
                    "completed_at": "Час здачі"
                },
                use_container_width=True
            )

    # -----------------------------------------------------
    # ВКЛАДКА 3: НАЛАШТУВАННЯ КЛЮЧІВ
    # -----------------------------------------------------
    with tab_settings:
        st.subheader("⚙️ Ключі доступу")
        key_input = st.text_input("Введіть ваш Gemini API Key (з Google AI Studio):", value=st.session_state.get("user_gemini_key", ""), type="password")
        if st.button("Зберегти ключ"):
            st.session_state["user_gemini_key"] = key_input
            st.success("Ключ збережено в поточній сесії!")
        st.caption("Отримати безкоштовний ключ можна на сайті: [https://aistudio.google.com/](https://aistudio.google.com/)")

# =========================================================
# РЕЖИМ: КАБІНЕТ УЧНЯ (ПРОХОДЖЕННЯ УРОКІВ)
# =========================================================
else:
    st.header("🎓 Кабінет Учня: Навчання на сьогодні")
    
    if not db["lessons"]:
        st.warning("Наразі немає створених уроків. Попросіть маму додати уроки в Кабінеті Мами!")
    else:
        # Фільтрація уроків за датою
        available_dates = sorted(list(set([l["date"] for l in db["lessons"]])), reverse=True)
        selected_date = st.selectbox("📅 Оберіть дату навчання:", available_dates)
        
        # Уроки на обрану дату
        day_lessons = [l for l in db["lessons"] if l["date"] == selected_date]
        lesson_subjects = [l["subject"] for l in day_lessons]
        
        selected_subject = st.radio("📚 Оберіть предмет:", lesson_subjects, horizontal=True)
        
        # Поточний урок
        current_lesson = next((l for l in day_lessons if l["subject"] == selected_subject), None)
        
        if current_lesson:
            st.markdown(f"## {current_lesson['subject']}: {current_lesson['topic']}")
            
            # Перевіряємо, чи урок вже здано
            already_done = next((r for r in db["results"] if r.get("lesson_id") == current_lesson["id"]), None)
            if already_done:
                st.success(f"✅ Цей урок вже виконано! Ваш результат: {already_done['score_percent']}% ({already_done['score_text']})")
            
            st.markdown("---")
            
            # 1. МАТЕРІАЛИ УРОКУ
            st.subheader("📖 1. Теоретичний конспект")
            st.markdown(current_lesson["summary"])
            
            if current_lesson.get("youtube_url"):
                st.subheader("🎬 2. Навчальне відео")
                st.video(current_lesson["youtube_url"])
            
            # 2. HTML ТРЕНАЖЕР
            if current_lesson.get("html_game"):
                st.subheader("🎮 3. Інтерактивна вправа / Тренажер")
                st.components.v1.html(current_lesson["html_game"], height=250, scrolling=True)
            
            # 3. ТЕСТ САМОПЕРЕВІРКИ
            st.subheader("📝 4. Тест для перевірки знань")
            
            quiz = current_lesson.get("quiz", [])
            user_answers = {}
            
            with st.form(key=f"quiz_form_{current_lesson['id']}"):
                for idx, q in enumerate(quiz):
                    st.write(f"**Питання {idx+1}: {q['question']}**")
                    user_answers[idx] = st.radio(
                        f"Оберіть відповідь на питання №{idx+1}:", 
                        q['options'], 
                        key=f"q_{current_lesson['id']}_{idx}",
                        index=None
                    )
                    st.write("")
                
                submit_button = st.form_submit_button("🚀 Завершити та здати урок", type="primary")
            
            if submit_button:
                if None in user_answers.values():
                    st.warning("⚠️ Будь ласка, дайте відповідь на всі питання тесту перед здачею!")
                else:
                    correct_count = 0
                    for idx, q in enumerate(quiz):
                        selected_option = user_answers[idx]
                        correct_option = q['options'][q['correct_idx']]
                        if selected_option == correct_option:
                            correct_count += 1
                    
                    total_q = len(quiz)
                    score_pct = int((correct_count / total_q) * 100) if total_q > 0 else 100
                    
                    # Зберігаємо результат
                    result_record = {
                        "lesson_id": current_lesson["id"],
                        "date": current_lesson["date"],
                        "subject": current_lesson["subject"],
                        "topic": current_lesson["topic"],
                        "score_percent": score_pct,
                        "score_text": f"{correct_count}/{total_q}",
                        "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # Видаляємо старий результат, якщо він був, і додаємо новий
                    db["results"] = [r for r in db["results"] if r.get("lesson_id") != current_lesson["id"]]
                    db["results"].append(result_record)
                    save_data(db)
                    
                    st.balloons()
                    st.success(f"🎉 Урок здано! Ваш результат: {correct_count} з {total_q} ({score_pct}%)")
