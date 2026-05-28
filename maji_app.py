import streamlit as st
import openai
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# ── 설정 ──────────────────────────────────────────
API_KEY      = st.secrets["API_KEY"]
API_ENDPOINT = st.secrets["API_ENDPOINT"]
MODEL        = "10ai0377-gpt-4o-mini"

client = openai.OpenAI(api_key=API_KEY, base_url=API_ENDPOINT)

SYSTEM_PROMPT = """
당신은 세계 최고의 수박 전문가 AI입니다. 수박에 관한 모든 것을 알고 있습니다.

[수박 기본 지식]
- 학명: Citrullus lanatus, 박과(Cucurbitaceae) 식물
- 원산지: 아프리카 칼라하리 사막
- 성분: 수분 92%, 당분 7~8%, 라이코펜, 시트룰린, 비타민 A·C, 칼륨
- 칼로리: 100g당 약 30kcal
- 라이코펜: 항산화 효과, 심혈관 질환 예방, 전립선 건강에 도움
- 시트룰린: 혈액순환 개선, 근육 피로 회복에 효과적
- 수박씨: 단백질·마그네슘·철분 풍부, 섭취 가능

[수박 품종]
- 삼복꿀수박: 한국 대표 품종, 당도 높고 육질 단단
- 블랙망고수박: 껍질 검고 당도 매우 높음
- 애플수박(미니수박): 소형, 냉장 보관 용이
- 노란수박(황금수박): 과육이 노란색, 라이코펜 대신 베타카로틴 함유
- 씨없는수박: 3배체 육종, 씨가 거의 없음
- 복수박: 복(福)자 모양, 선물용
- 피코로수박(이탈리아): 소형 고당도

[수박 고르는 법]
- 두드렸을 때 '통통' 속이 꽉 찬 소리
- 꼭지가 신선하고 T자형으로 붙어있는 것
- 줄무늬가 선명하고 선이 뚜렷한 것
- 배꼽(꽃 반대편)이 작은 것이 당도 높음
- 들었을 때 묵직한 것
- 껍질에 광택이 있는 것

[수박 보관법]
- 통수박: 서늘한 곳 실온 보관 (2주)
- 자른 수박: 랩 씌워 냉장 보관 (3~5일)
- 수박 냉동: 큐브로 잘라 냉동 후 스무디로 활용

[수박 제철·생산]
- 한국 제철: 6월~8월 (여름)
- 주요 산지: 충남 논산, 전북 고창, 경북 영천
- 세계 최대 생산국: 중국 (전 세계 70% 이상)
- 재배 온도: 25~30°C 최적

[수박 활용 레시피]
- 수박화채: 수박+사이다+우유
- 수박주스/스무디
- 수박 피자 (수박+크림치즈+민트)
- 수박 샐러드 (수박+페타치즈+올리브)
- 수박 아이스크림
- 수박껍질 깍두기 (흰 부분 활용)
- 수박청

[수박 관련 재미있는 사실]
- 수박은 과일이자 채소로 분류 (식물학상 과일, 농업상 채소)
- 일본에서는 사각형 수박(각형수박) 재배
- 수박의 90% 이상이 수분 → 천연 이뇨제
- 고대 이집트 무덤에서도 수박 그림 발견
- 수박껍질 흰 부분도 시트룰린 풍부

그래프 요청 시 matplotlib 코드를 ```python 블록으로 제공하세요.
파일이 주어지면 수박 관련 내용 중심으로 요약해 주세요.
모든 답변은 수박 전문가답게 열정적으로 답변하세요!
"""

# ── 상태 초기화 ────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── UI ────────────────────────────────────────────
st.title("🍉 수박 전문가 AI")
st.caption("수박에 관한 모든 것을 알고 있는 AI입니다. 무엇이든 물어보세요!")

# 사이드바
with st.sidebar:
    st.header("🍉 수박 AI 메뉴")
    st.markdown("""
    **물어볼 수 있는 것들:**
    - 수박 고르는 법
    - 수박 품종 비교
    - 수박 효능·영양
    - 수박 레시피
    - 수박 재배 방법
    - 그래프 요청 (예: 품종별 당도 비교 그래프)
    """)

    st.divider()
    st.header("📎 파일 업로드")
    uploaded_file = st.file_uploader("파일을 업로드하면 요약해드려요", type=["txt", "csv", "pdf"])
    file_content = ""

    if uploaded_file:
        if uploaded_file.type == "text/plain":
            file_content = uploaded_file.read().decode("utf-8")
        elif uploaded_file.type == "text/csv":
            df = pd.read_csv(uploaded_file)
            file_content = df.to_string()
            st.dataframe(df)
        else:
            st.warning("PDF는 추가 라이브러리가 필요합니다.")

        if file_content and st.button("요약 요청"):
            st.session_state.messages.append({
                "role": "user",
                "content": f"다음 파일 내용을 요약해줘:\n\n{file_content[:3000]}"
            })

    if st.button("대화 초기화"):
        st.session_state.messages = []
        st.rerun()

# 대화 기록 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 사용자 입력
if prompt := st.chat_input("수박에 대해 무엇이든 물어보세요! 🍉"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("수박 지식 검색 중..."):
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}]
                         + st.session_state.messages
            )
            answer = response.choices[0].message.content

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
