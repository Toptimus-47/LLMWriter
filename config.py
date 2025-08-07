# config.py
import os
import streamlit as st
import json

class AppConfig:
    """애플리케이션 전반에 사용되는 설정 클래스"""
    
    # --- API 키 ---
    # .env 파일에 GOOGLE_API_KEY="YOUR_API_KEY" 형식으로 저장하세요.
    GOOGLE_API_KEY= st.secrets["GOOGLE_API_KEY"]

    # --- LLM 모델 ---
    # 사용할 모델 ID. Gemini 2.5 Flash를 기본으로 설정합니다.
    MAIN_LLM_MODEL = "gemini-2.5-Flash" 
    
    # --- 파일 경로 ---
    NOVELS_DIR = "novels"
    SETTINGS_FILENAME = "settings.json"
    CHAPTERS_DIR = "chapters"
    VECTOR_STORE_DIR = "vector_store"
    FAISS_INDEX_NAME = "novel.faiss"
    
    # --- RAG (Faiss) 설정 ---
    # 한국어 임베딩에 특화된 모델 사용
    EMBEDDING_MODEL = 'jhgan/ko-sroberta-multitask'
    RAG_TOP_K = 3 # 다음 챕터 생성 시 참조할 관련 챕터 수

config = AppConfig()
