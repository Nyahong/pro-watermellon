import streamlit as st
st.set_page_config(page_title="수박 전문가 AI", page_icon="🍉")
import streamlit.components.v1 as components
import openai
import json
import time
import base64
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime
from zoneinfo import ZoneInfo

matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 설정
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API_KEY = st.secrets["API_KEY"]
MODEL   = "10ai0377-gpt-4o-mini"

client = openai.AzureOpenAI(
    api_key=API_KEY,
    azure_endpoint="https://10ai037-openai.openai.azure.com/",
    api_version="2024-05-01-preview"
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 실시간 날씨 (wttr.in, API 키 불필요)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@st.cache_data(ttl=600)  # 10분마다 갱신
def fetch_weather(city="Seoul"):
    try:
        res  = requests.get(f"https://wttr.in/{city}?format=j1", timeout=5)
        data = res.json()
        cur  = data['current_condition'][0]
        return {
            "temp":       cur['temp_C'],
            "feels_like": cur['FeelsLikeC'],
            "humidity":   cur['humidity'],
            "wind":       cur['windspeedKmph'],
            "desc":       cur['weatherDesc'][0]['value'],
        }
    except:
        return None

def weather_emoji(desc):
    d = desc.lower()
    if any(w in d for w in ["sunny", "clear"]):        return "☀️"
    if any(w in d for w in ["partly", "cloudy"]):      return "⛅"
    if "overcast" in d:                                 return "☁️"
    if any(w in d for w in ["rain", "drizzle"]):       return "🌧️"
    if "snow" in d:                                     return "❄️"
    if any(w in d for w in ["thunder", "storm"]):      return "⛈️"
    if any(w in d for w in ["fog", "mist"]):           return "🌫️"
    return "🌡️"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [1] 함수 정의 (새 기능 추가 시 여기에 작성)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WEATHER_DATA = {
    "tokyo":         {"temperature": "10", "unit": "celsius"},
    "san francisco": {"temperature": "72", "unit": "fahrenheit"},
    "paris":         {"temperature": "22", "unit": "celsius"},
    "seoul":         {"temperature": "25", "unit": "celsius"},
    "london":        {"temperature": "15", "unit": "celsius"},
    "berlin":        {"temperature": "18", "unit": "celsius"},
    "new york":      {"temperature": "68", "unit": "fahrenheit"},
}

TIMEZONE_DATA = {
    "tokyo":         "Asia/Tokyo",
    "san francisco": "America/Los_Angeles",
    "paris":         "Europe/Paris",
    "seoul":         "Asia/Seoul",
    "new york":      "America/New_York",
    "london":        "Europe/London",
    "berlin":        "Europe/Berlin",
}

def get_current_weather(location, unit=None):
    location_lower = location.lower()
    for key in WEATHER_DATA:
        if key in location_lower:
            weather = WEATHER_DATA[key]
            return json.dumps({
                "location": location,
                "temperature": weather["temperature"],
                "unit": unit if unit else weather["unit"]
            })
    return json.dumps({"location": location, "temperature": "unknown"})

def get_current_time(location):
    location_lower = location.lower()
    for key, timezone in TIMEZONE_DATA.items():
        if key in location_lower:
            current_time = datetime.now(ZoneInfo(timezone)).strftime("%I:%M %p")
            return json.dumps({"location": location, "current_time": current_time})
    return json.dumps({"location": location, "current_time": "unknown"})

def multiply(a, b):
    return json.dumps({"a": a, "b": b, "result": a * b})

def calculate(expression):
    try:
        result = eval(expression)
        return json.dumps({"expression": expression, "result": result})
    except:
        return json.dumps({"error": "계산할 수 없는 수식입니다."})

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [2] 함수 라우터 (함수 추가 시 여기도 추가)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FUNCTION_MAP = {
    "get_current_weather": get_current_weather,
    "get_current_time":    get_current_time,
    "multiply":            multiply,
    "calculate":           calculate,
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [3] tools 정의 (함수 추가 시 여기도 추가)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "특정 도시의 현재 날씨를 반환합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "도시 이름 (예: Seoul)"},
                    "unit":     {"type": "string", "enum": ["celsius", "fahrenheit"]}
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "특정 도시의 현재 시간을 반환합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "도시 이름 (예: Tokyo)"}
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "multiply",
            "description": "두 수를 입력받아 곱을 리턴합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "첫 번째 숫자"},
                    "b": {"type": "number", "description": "두 번째 숫자"}
                },
                "required": ["a", "b"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "수식을 계산합니다. 덧셈, 뺄셈, 곱셈, 나눗셈 가능.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "계산할 수식 (예: '123 + 456')"}
                },
                "required": ["expression"]
            }
        }
    }
]

INSTRUCTIONS = """
당신은 세계 최고의 수박 전문가 AI이면서 날씨, 시간, 계산도 도와주는 멀티 어시스턴트입니다.

[수박 기본 지식]
- 학명: Citrullus lanatus, 박과(Cucurbitaceae) 식물
- 원산지: 아프리카 칼라하리 사막
- 성분: 수분 92%, 당분 7~8%, 라이코펜, 시트룰린, 비타민 A·C, 칼륨
- 칼로리: 100g당 약 30kcal

[수박 품종]
- 삼복꿀수박, 블랙망고수박, 애플수박(미니수박), 노란수박, 씨없는수박, 복수박

[수박 고르는 법]
- 두드렸을 때 '통통' 소리, 꼭지가 T자형, 줄무늬 선명, 배꼽 작을수록 당도 높음

[수박 보관법]
- 통수박: 실온 2주 / 자른 수박: 냉장 3~5일

[수박 레시피]
- 수박화채, 수박주스, 수박피자, 수박샐러드, 수박껍질 깍두기

그래프 요청 시 matplotlib 코드를 ```python 블록으로 제공하세요.
모든 답변은 친절하고 열정적으로 해주세요!
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Assistant & Thread 초기화 (세션당 한 번만 생성)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if "assistant_id" not in st.session_state:
    assistant = client.beta.assistants.create(
        name="수박 멀티 AI",
        instructions=INSTRUCTIONS,
        model=MODEL,
        tools=tools
    )
    st.session_state.assistant_id = assistant.id

if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요? 저는 수박박사입니다. 🍉\n수박에 관한 모든 것은 물론, 날씨·시간·계산까지 뭐든지 물어보세요!"}
    ]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Assistant 실행 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def run_assistant(user_message, image_b64=None, image_mime=None):
    # 메시지 내용 구성
    if image_b64:
        content = [
            {"type": "text", "text": user_message},
            {"type": "image_url", "image_url": {"url": f"data:{image_mime};base64,{image_b64}"}}
        ]
    else:
        content = user_message

    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=content
    )

    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=st.session_state.assistant_id
    )

    while True:
        run = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id,
            run_id=run.id
        )

        if run.status == "completed":
            break

        elif run.status == "requires_action":
            tool_outputs = []
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                func      = FUNCTION_MAP.get(func_name)
                result    = func(**func_args) if func else json.dumps({"error": "unknown"})
                tool_outputs.append({"tool_call_id": tool_call.id, "output": result})

            client.beta.threads.runs.submit_tool_outputs(
                thread_id=st.session_state.thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )

        elif run.status in ["failed", "cancelled", "expired"]:
            return "오류가 발생했습니다. 다시 시도해주세요."

        time.sleep(1)

    messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
    return messages.data[0].content[0].text.value

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 전체 수박 테마 CSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp { background-color: #1a1a1a; }

    /* 사이드바 */
    [data-testid="stSidebar"] { background-color: #222222 !important; }

    /* 채팅 입력창 */
    [data-testid="stChatInput"] textarea {
        background-color: #1a3a1c !important;
        color: #f0fff0 !important;
        border: 1px solid #4caf50 !important;
        border-radius: 12px !important;
    }

    /* 버튼 */
    .stButton > button {
        background: linear-gradient(135deg, #2d6a2d, #1a472a) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #e63946, #c1121f) !important;
    }

    /* 제목 */
    h1 { color: #ff6b6b !important; }

    /* 구분선 */
    hr { border-color: #2d6a2d !important; }
</style>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UI 헤더
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
components.html("""
<div style="
    background: linear-gradient(135deg, #e8f5e9, #fce4ec);
    border-radius: 16px;
    padding: 20px 28px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 16px;
    border: 1px solid #f0d8df;
">
    <div style="font-size: 52px; line-height:1;">🍉</div>
    <div>
        <div style="font-size:24px; font-weight:700; color:#4a4a4a;">수박 전문가 AI</div>
        <div style="font-size:13px; color:#888; margin-top:3px;">수박 질문은 물론, 날씨 · 시간 · 계산까지!</div>
    </div>
</div>
""", height=105)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 실시간 시계 + 날씨 대시보드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
weather = fetch_weather("Seoul")
emoji   = weather_emoji(weather['desc']) if weather else "❓"

col1, col2 = st.columns(2)

with col1:
    components.html("""
    <div style="
        background: linear-gradient(135deg, #1a472a, #2d6a2d);
        border-radius: 16px;
        padding: 20px 24px;
        color: white;
        font-family: 'Segoe UI', sans-serif;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        border: 1px solid #4caf50;
    ">
        <div style="font-size:13px; color:#a5d6a7; margin-bottom:4px;">🍉 서울 현재 시각</div>
        <div id="clock" style="font-size:36px; font-weight:700; letter-spacing:2px; color:#ffffff;"></div>
        <div id="date"  style="font-size:13px; color:#a5d6a7; margin-top:6px;"></div>
    </div>
    <script>
        function update() {
            const now = new Date();
            const options = { timeZone: 'Asia/Seoul' };
            const timeStr = now.toLocaleTimeString('ko-KR', {...options, hour:'2-digit', minute:'2-digit', second:'2-digit'});
            const dateStr = now.toLocaleDateString('ko-KR', {...options, year:'numeric', month:'long', day:'numeric', weekday:'long'});
            document.getElementById('clock').innerText = timeStr;
            document.getElementById('date').innerText  = dateStr;
        }
        update();
        setInterval(update, 1000);
    </script>
    """, height=150)

with col2:
    if weather:
        components.html(f"""
        <div style="
            background: linear-gradient(135deg, #0f3460, #533483);
            border-radius: 16px;
            padding: 20px 24px;
            color: white;
            font-family: 'Segoe UI', sans-serif;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
            border: 1px solid #7e57c2;
        ">
            <div style="font-size:13px; color:#ce93d8; margin-bottom:4px;">{emoji} 서울 현재 날씨</div>
            <div style="font-size:36px; font-weight:700; color:#ffffff;">{weather['temp']}°C
                <span style="font-size:16px; font-weight:400; color:#ce93d8;">{weather['desc']}</span>
            </div>
            <div style="font-size:13px; color:#ce93d8; margin-top:8px; display:flex; gap:16px;">
                <span>🌡️ 체감 {weather['feels_like']}°C</span>
                <span>💧 습도 {weather['humidity']}%</span>
                <span>💨 바람 {weather['wind']}km/h</span>
            </div>
        </div>

        """, height=150)
    else:
        st.warning("날씨 정보를 불러올 수 없습니다.")

st.divider()

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 10px 0 16px;">
        <div style="font-size:48px;">🍉</div>
        <div style="font-size:18px; font-weight:700; color:#ff6b6b;">수박 AI 메뉴</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    **물어볼 수 있는 것들:**
    - 🍉 수박 고르는 법 / 품종 / 효능
    - 🍳 수박 레시피 / 재배 방법
    - 📊 그래프 요청
    - 🌤️ 날씨 / ⏰ 시간 / 🔢 계산
    """)

    st.divider()
    st.header("📎 파일 & 이미지 업로드")
    uploaded_file = st.file_uploader(
        "파일을 업로드하면 분석해드려요",
        type=["txt", "csv", "png", "jpg", "jpeg", "webp", "gif"]
    )
    file_content = ""
    image_b64    = None
    image_mime   = None

    if uploaded_file:
        ftype = uploaded_file.type
        if ftype == "text/plain":
            file_content = uploaded_file.read().decode("utf-8")
        elif ftype == "text/csv":
            df = pd.read_csv(uploaded_file)
            file_content = df.to_string()
            st.dataframe(df)
        elif ftype.startswith("image/"):
            img_bytes  = uploaded_file.read()
            image_b64  = base64.b64encode(img_bytes).decode("utf-8")
            image_mime = ftype
            st.image(img_bytes, caption=uploaded_file.name)

        if file_content and st.button("요약 요청"):
            with st.spinner("요약 중..."):
                answer = run_assistant(f"다음 파일 내용을 요약해줘:\n\n{file_content[:3000]}")
            st.session_state.messages.append({"role": "user",      "content": "파일 요약 요청"})
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

        if image_b64 and st.button("이미지 분석 요청"):
            with st.spinner("이미지 분석 중..."):
                answer = run_assistant("이 이미지를 수박 전문가 입장에서 분석해줘.", image_b64, image_mime)
            st.session_state.messages.append({"role": "user",      "content": "🖼️ 이미지 분석 요청"})
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

    st.divider()
    if st.button("대화 초기화"):
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
        st.session_state.messages  = []
        st.rerun()

# 대화 기록 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 사용자 입력
if prompt := st.chat_input("무엇이든 물어보세요! 🍉"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("생각 중..."):
            answer = run_assistant(prompt)

        st.markdown(answer)

        # 그래프 코드 감지 및 실행
        if "```python" in answer:
            code = answer.split("```python")[1].split("```")[0].strip()
            try:
                plt.close('all')
                exec(code, {"plt": plt, "pd": pd})
                fig = plt.gcf()
                st.pyplot(fig)
            except Exception as e:
                st.error(f"그래프 실행 오류: {e}")

    st.session_state.messages.append({"role": "assistant", "content": answer})
