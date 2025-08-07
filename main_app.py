import streamlit as st
import os
from services.llm_service import LLMService
from services.novel_service import NovelService
from llm_client import GeminiClient, OpenAIClient, ClaudeClient
from faiss_manager import FaissManager
from prompts.prompt_manager import PromptManager
from config import LLM_MODELS, DEFAULT_MODEL_ID, config
from novel_data_manager import Character, Novel, NovelSettings

# === 1. 초기화 (session_state에 의존성 주입) ===
if 'llm_service' not in st.session_state:
    st.set_page_config(layout="wide")

    # secrets.toml에서 API 키를 안전하게 가져옵니다.
    try:
        api_keys = {
            "google": st.secrets["GOOGLE_API_KEY"],
            "openai": st.secrets["OPENAI_API_KEY"],
            "anthropic": st.secrets["ANTHROPIC_API_KEY"]
        }
    except KeyError as e:
        st.error(f"API 키를 찾을 수 없습니다: {e}. `.streamlit/secrets.toml` 파일을 확인해주세요.")
        st.stop()

    # 클라이언트 인스턴스 생성 및 주입
    llm_clients = {
        "google": GeminiClient(api_key=api_keys.get("google")),
        "openai": OpenAIClient(api_key=api_keys.get("openai")),
        "anthropic": ClaudeClient(api_key=api_keys.get("anthropic"))
    }

    st.session_state.prompt_manager = PromptManager()
    st.session_state.faiss_manager = FaissManager()
    st.session_state.llm_service = LLMService(
        llm_clients=llm_clients,
        prompt_manager=st.session_state.prompt_manager,
        faiss_manager=st.session_state.faiss_manager
    )
    st.session_state.novel_service = NovelService()

    # 기본 상태 설정
    st.session_state.novel = None
    st.session_state.llm_service.set_active_model(DEFAULT_MODEL_ID)
    st.session_state.total_tokens = 0
    st.session_state.current_tokens = {}

# === 2. UI 레이아웃 및 기능 구현 ===
st.title("AI 소설 작가")

# 사이드바
with st.sidebar:
    st.header("설정")

    # LLM 모델 선택
    model_options = list(LLM_MODELS.keys())
    active_model_id = st.session_state.llm_service.active_model_id
    selected_model_id = st.selectbox(
        "사용할 LLM 모델 선택",
        options=model_options,
        index=model_options.index(active_model_id) if active_model_id in model_options else 0
    )
    if selected_model_id != active_model_id:
        st.session_state.llm_service.set_active_model(selected_model_id)

    # 소설 파일 관리
    st.header("소설 파일 관리")
    novel_files = st.session_state.novel_service.list_novels()
    selected_novel = st.selectbox("소설 불러오기", options=["새 소설"] + novel_files)
    
    col_load, col_save = st.columns(2)
    with col_load:
        if st.button("소설 불러오기", use_container_width=True, disabled=(selected_novel == "새 소설")):
            st.session_state.novel, st.session_state.faiss_manager = st.session_state.novel_service.load_novel(selected_novel)
            if st.session_state.novel:
                st.success(f"'{selected_novel}' 소설이 불러와졌습니다.")
                st.rerun()
    with col_save:
        if st.button("현재 소설 저장", use_container_width=True, disabled=(st.session_state.novel is None)):
            st.session_state.novel_service.save_novel(st.session_state.novel, st.session_state.faiss_manager)
            st.success(f"'{st.session_state.novel.title}' 소설이 성공적으로 저장되었습니다.")

    st.header("소설 설정")
    if st.session_state.novel:
        st.session_state.novel.title = st.text_input("소설 제목", value=st.session_state.novel.title, key="novel_title")
    else:
        novel_title = st.text_input("새 소설 제목", value="새로운 소설", key="new_novel_title")
        if st.button("새 소설 시작", use_container_width=True):
            st.session_state.novel = st.session_state.novel_service.create_new_novel(novel_title)
            st.session_state.faiss_manager = FaissManager()
            st.success(f"'{novel_title}' 소설이 시작되었습니다.")
            st.rerun()

    if st.session_state.novel:
        with st.expander("세부 설정", expanded=False):
            st.session_state.novel.settings.style = st.text_input("문체/장르", value=st.session_state.novel.settings.style, key="style")
            st.session_state.novel.settings.pov = st.selectbox("시점", options=["1인칭", "3인칭 전지적", "3인칭 관찰자"], index=["1인칭", "3인칭 전지적", "3인칭 관찰자"].index(st.session_state.novel.settings.pov), key="pov")
            st.session_state.novel.settings.time_bg = st.text_area("시간적 배경", value=st.session_state.novel.settings.time_bg, key="time_bg")
            st.session_state.novel.settings.space_bg = st.text_area("공간적 배경", value=st.session_state.novel.settings.space_bg, key="space_bg")
            st.session_state.novel.settings.social_bg = st.text_area("사회적 배경", value=st.session_state.novel.settings.social_bg, key="social_bg")

            st.markdown("---")
            st.subheader("등장인물")
            if 'character_count' not in st.session_state:
                st.session_state.character_count = len(st.session_state.novel.settings.characters)
            
            for i in range(st.session_state.character_count):
                st.session_state.novel.settings.characters[i].name = st.text_input(f"{i+1}. 이름", value=st.session_state.novel.settings.characters[i].name, key=f"char_name_{i}")
                st.session_state.novel.settings.characters[i].personality = st.text_input("성격 (쉼표로 구분)", value=", ".join(st.session_state.novel.settings.characters[i].personality), key=f"char_pers_{i}").split(', ')
                st.session_state.novel.settings.characters[i].appearance = st.text_input("외모 (쉼표로 구분)", value=", ".join(st.session_state.novel.settings.characters[i].appearance), key=f"char_app_{i}").split(', ')

            col_add, col_remove = st.columns(2)
            with col_add:
                if st.button("인물 추가", use_container_width=True):
                    st.session_state.character_count += 1
                    st.session_state.novel.settings.characters.append(Character(name="", personality=[], appearance=[]))
                    st.rerun()
            with col_remove:
                if st.button("인물 제거", use_container_width=True, disabled=st.session_state.character_count==0):
                    if st.session_state.character_count > 0:
                        st.session_state.character_count -= 1
                        st.session_state.novel.settings.characters.pop()
                        st.rerun()
                        
    if st.session_state.novel:
        st.subheader("토큰 사용량")
        st.info(f"**누적:** {st.session_state.total_tokens:,} 토큰")

# 메인 화면
st.header("소설 본문")
if not st.session_state.novel:
    st.warning("새 소설을 시작하거나 기존 소설을 불러오세요.")
else:
    novel_full_text = st.session_state.novel.get_full_text()
    if st.session_state.novel.chapters:
        st.text_area("소설 내용", value=novel_full_text, height=800, disabled=True)
    else:
        st.info("프롤로그 생성을 기다리고 있습니다...")

    st.divider()

    st.subheader("챕터 생성")
    if not st.session_state.novel.chapters:
        if st.button("프롤로그 생성 시작", use_container_width=True, disabled=(st.session_state.novel.title == "")):
            with st.spinner("프롤로그를 생성 중입니다..."):
                try:
                    novel_obj, tokens = st.session_state.llm_service.generate_prologue(st.session_state.novel)
                    st.session_state.novel = novel_obj
                    st.session_state.current_tokens = tokens
                    st.session_state.total_tokens += tokens['total_tokens']
                    st.success("프롤로그가 성공적으로 생성되었습니다!")
                    st.rerun()
                except ValueError as e:
                    st.error(f"오류 발생: {e}")
                except Exception as e:
                    st.error(f"예상치 못한 오류가 발생했습니다: {e}")
    else:
        st.session_state.novel.next_chapter_prompt = st.text_area(
            "다음 챕터에 대한 작가 지시를 입력하세요. (선택사항)",
            value=st.session_state.novel.next_chapter_prompt,
            key="next_chapter_prompt"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("다음 챕터 생성", use_container_width=True):
                with st.spinner("다음 챕터를 생성 중입니다..."):
                    try:
                        novel_obj, tokens = st.session_state.llm_service.generate_next_chapter(st.session_state.novel)
                        st.session_state.novel = novel_obj
                        st.session_state.current_tokens = tokens
                        st.session_state.total_tokens += tokens['total_tokens']
                        st.success("다음 챕터가 성공적으로 생성되었습니다!")
                        st.rerun()
                    except ValueError as e:
                        st.error(f"오류 발생: {e}")
                    except Exception as e:
                        st.error(f"예상치 못한 오류가 발생했습니다: {e}")
        with col2:
            st.info(f"**현재 챕터 토큰 사용량:** {st.session_state.current_tokens.get('total_tokens', 0):,} 토큰")
