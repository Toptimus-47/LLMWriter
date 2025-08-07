import streamlit as st
import os
import sys

# 의존성들을 모두 임포트
from clients.llm_client import GeminiClient
from services.novel_service import NovelService
from services.llm_service import LLMService
from services.file_service import FileService
from prompts.prompt_manager import PromptManager
from models.novel import Novel, NovelSettings, Character, Chapter
from config import config

# --- 페이지 설정 ---
st.set_page_config(page_title="AI 소설 어시스턴트", layout="wide")

# --- 서비스 초기화 (DI 컨테이너 역할) ---
if 'novel_service' not in st.session_state:
    try:
        # API 키를 secrets에서 안전하게 가져옴
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("GOOGLE_API_KEY가 Streamlit Secrets에 설정되지 않았습니다.")
            st.stop()
        
        # 1. 가장 하위 의존성(Clients, Prompts)부터 생성
        gemini_client = GeminiClient(api_key=api_key)
        prompt_manager = PromptManager()
        file_service = FileService()
        
        # 2. 다음 단계 의존성(Services) 생성 시 상위 의존성을 주입
        llm_service = LLMService(
            llm_client=gemini_client,
            prompt_manager=prompt_manager
        )
        
        # 3. 최상위 서비스(NovelService) 생성 시 모든 의존성 주입
        st.session_state.novel_service = NovelService(
            file_service=file_service,
            llm_service=llm_service
        )
        
        # 모델 목록을 캐싱하여 API 호출 횟수를 줄임
        if 'available_models' not in st.session_state:
            st.session_state.available_models = llm_service.get_available_models()

    except Exception as e:
        st.error(f"서비스 초기화 중 오류 발생: {e}")
        st.stop()

# --- 헬퍼 함수 ---
def reset_ui_state():
    """새 소설을 시작하거나 불러올 때 UI 상태 초기화"""
    st.session_state.current_novel = None
    st.session_state.character_list = []
    st.session_state.new_char_name = ""
    st.session_state.new_char_personality = ""
    st.session_state.new_char_appearance = ""
    st.session_state.selected_chapter_title = None

def load_novel_to_session(novel_title):
    """선택된 소설을 세션 상태로 불러오는 함수"""
    novel_service = st.session_state.novel_service
    novel = novel_service.load_novel(novel_title)
    if novel:
        st.session_state.current_novel = novel
        st.session_state.character_list = novel.settings.characters
        st.success(f"'{novel_title}' 소설을 성공적으로 불러왔습니다.")
    else:
        st.error("소설을 불러오는 데 실패했습니다.")
        reset_ui_state()

# --- 사이드바 UI ---
with st.sidebar:
    st.title("📚 AI 소설 어시스턴트")
    st.markdown("---")

    st.header("새 소설 시작")
    new_novel_title = st.text_input("소설 제목 입력", key="new_novel_title_input")
    if st.button("새 소설 만들기"):
        if new_novel_title:
            reset_ui_state()
            novel_service = st.session_state.novel_service
            novel = novel_service.create_new_novel(new_novel_title)
            st.session_state.current_novel = novel
            st.success(f"새 소설 '{new_novel_title}' 생성 완료! 설정을 시작하세요.")
        else:
            st.warning("소설 제목을 입력해주세요.")

    st.markdown("---")
    st.header("소설 불러오기")
    
    novel_service = st.session_state.novel_service
    available_novels = novel_service.list_novels()
    
    selected_novel_to_load = st.selectbox(
        "불러올 소설 선택",
        options=[""] + available_novels,
        key="load_novel_select"
    )

    if st.button("선택한 소설 불러오기"):
        if selected_novel_to_load:
            reset_ui_state()
            load_novel_to_session(selected_novel_to_load)
        else:
            st.warning("불러올 소설을 선택해주세요.")

# --- 메인 페이지 UI ---
if 'current_novel' not in st.session_state:
    st.session_state.current_novel = None

if st.session_state.current_novel:
    novel = st.session_state.current_novel
    st.header(f"📖 현재 작업중인 소설: {novel.title}")

    # 소설 생성 전 설정 탭
    if not novel.chapters:
        st.info("소설 생성을 시작하기 전에 아래 설정을 완료하고 '프롤로그 생성' 버튼을 눌러주세요.")
        
        settings_tab, characters_tab = st.tabs(["기본 설정", "등장인물"])

        with settings_tab:
            st.subheader("기본 설정")
            novel.settings.style = st.text_area("문체", value=novel.settings.style, placeholder="예: 건조하고 간결한 문체, 화려하고 시적인 묘사")
            
            # 모델 선택 드롭다운 박스
            available_models = st.session_state.available_models
            model_options = list(available_models.keys())
            if not model_options:
                st.warning("사용 가능한 모델이 없습니다. API 키를 확인해주세요.")
            else:
                selected_model_name = st.selectbox(
                    "모델 선택",
                    options=model_options,
                    index=0
                )
                novel.settings.model_id = available_models[selected_model_name]
            
            novel.settings.pov = st.selectbox("시점", ["1인칭 주인공", "3인칭 관찰자", "3인칭 전지적"], index=2)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                novel.settings.time_bg = st.text_input("시간적 배경", value=novel.settings.time_bg, placeholder="예: 2077년, 근미래")
            with col2:
                novel.settings.space_bg = st.text_input("공간적 배경", value=novel.settings.space_bg, placeholder="예: 사이버펑크 도시 '네오-서울'")
            with col3:
                novel.settings.social_bg = st.text_input("사회적 배경", value=novel.settings.social_bg, placeholder="예: 거대 기업이 모든 것을 지배하는 사회")

            novel.settings.prologue_length = st.number_input("프롤로그 분량 (단어 수)", min_value=100, max_value=2000, value=novel.settings.prologue_length, step=100)
            novel.settings.chapter_length = st.number_input("챕터당 평균 분량 (단어 수)", min_value=100, max_value=3000, value=novel.settings.chapter_length, step=100)

        with characters_tab:
            st.subheader("등장인물 관리")
            
            if 'character_list' not in st.session_state:
                st.session_state.character_list = novel.settings.characters

            for i, char in enumerate(st.session_state.character_list):
                with st.expander(f"**{char.name}**"):
                    st.write(f"**성격:** {', '.join(char.personality)}")
                    st.write(f"**외모:** {', '.join(char.appearance)}")
                    if st.button(f"{char.name} 삭제", key=f"del_char_{i}"):
                        st.session_state.character_list.pop(i)
                        novel.settings.characters = st.session_state.character_list
                        st.rerun()

            st.markdown("---")
            st.subheader("새 등장인물 추가")
            
            with st.form("new_char_form", clear_on_submit=True):
                char_name = st.text_input("이름", key="new_char_name")
                
                personality_keywords_str = st.text_input("성격 키워드 (쉼표로 구분)", key="new_char_personality")
                appearance_keywords_str = st.text_input("외모 키워드 (쉼표로 구분)", key="new_char_appearance")

                submitted = st.form_submit_button("등장인물 추가")
                if submitted and char_name:
                    personality = [k.strip() for k in personality_keywords_str.split(',') if k.strip()]
                    appearance = [k.strip() for k in appearance_keywords_str.split(',') if k.strip()]
                    new_char = Character(name=char_name, personality=personality, appearance=appearance)
                    st.session_state.character_list.append(new_char)
                    novel.settings.characters = st.session_state.character_list
                    st.success(f"등장인물 '{char_name}' 추가 완료!")

        st.markdown("---")
        if st.button("✨ 프롤로그 생성 시작", type="primary", use_container_width=True):
            if not novel.settings.model_id:
                st.error("모델을 먼저 선택해주세요.")
            else:
                selected_model_name = next(
                    (key for key, value in st.session_state.available_models.items() if value == novel.settings.model_id),
                    novel.settings.model_id
                )
                with st.spinner(f"{selected_model_name}가 프롤로그를 창작하고 있습니다..."):
                    try:
                        novel_service = st.session_state.novel_service
                        input_tokens, output_tokens = novel_service.generate_prologue(novel)
                        st.success("프롤로그 생성이 완료되었습니다!")
                        st.info(f"✅ 토큰 사용량: 입력 {input_tokens} | 출력 {output_tokens} | 총 {input_tokens + output_tokens}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"프롤로그 생성 중 오류 발생: {e}")

    # 소설 생성 후 뷰
    else:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📜 소설 본문")
            
            chapter_titles = [f"프롤로그"] + [f"챕터 {i+1}" for i in range(len(novel.chapters) - 1)]
            
            if 'selected_chapter_title' not in st.session_state or st.session_state.selected_chapter_title is None:
                st.session_state.selected_chapter_title = chapter_titles[-1]

            def on_chapter_select():
                st.session_state.selected_chapter_title = st.session_state.chapter_selector
            
            st.selectbox(
                "열람할 챕터 선택", 
                options=chapter_titles, 
                index=chapter_titles.index(st.session_state.selected_chapter_title),
                key="chapter_selector",
                on_change=on_chapter_select
            )

            selected_index = chapter_titles.index(st.session_state.selected_chapter_title)
            st.markdown(f"### {st.session_state.selected_chapter_title}")
            st.markdown(novel.chapters[selected_index].content.replace("\n", "\n\n"))

        with col2:
            st.subheader("⚙️ 작업 관리")
            
            # 여기서 사건 진행 프롬프트를 입력받습니다.
            novel.next_chapter_prompt = st.text_area(
                "다음 챕터에 대한 작가의 사건 진행 프롬프트", 
                value=novel.next_chapter_prompt or "",
                height=150,
                placeholder="예: 주인공이 새로운 인물을 만나고, 과거의 비밀에 대한 힌트를 얻게 된다."
            )
            
            if st.button("다음 챕터 생성", use_container_width=True):
                with st.spinner("다음 챕터를 생성하고 있습니다..."):
                    try:
                        novel_service = st.session_state.novel_service
                        input_tokens, output_tokens = novel_service.generate_next_chapter(novel, user_prompt=novel.next_chapter_prompt)
                        novel.next_chapter_prompt = "" # 프롬프트 입력창 초기화
                        st.session_state.selected_chapter_title = f"챕터 {len(novel.chapters) - 1}"
                        st.success("다음 챕터 생성 완료!")
                        st.info(f"✅ 토큰 사용량: 입력 {input_tokens} | 출력 {output_tokens} | 총 {input_tokens + output_tokens}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"챕터 생성 중 오류 발생: {e}")

            if st.button("💾 현재 소설 저장", use_container_width=True):
                with st.spinner("소설을 저장하는 중..."):
                    try:
                        novel_service = st.session_state.novel_service
                        novel_service.save_novel(novel)
                        st.success("소설이 성공적으로 저장되었습니다.")
                    except Exception as e:
                        st.error(f"저장 중 오류 발생: {e}")

            st.markdown("---")
            st.subheader("🧠 소설 메모리 (요약)")
            st.text_area("요약", value=novel.summary, height=200, disabled=True)

else:
    st.info("👈 사이드바에서 '새 소설 만들기'를 선택하거나 기존 소설을 불러와주세요.")
