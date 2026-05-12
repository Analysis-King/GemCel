"""
Çelebi Agent - Merkezi Konfigürasyon Dosyası v1.0

Bu dosya sistem genelinde kullanılan yol (path) tanımlamalarını, 
güvenlik limitlerini ve zaman aşımı sürelerini içerir.
"""
from pathlib import Path
import os

# --- YOL TANIMLAMALARI ---
# Projenin ana dizini
BASE_DIR = Path(__file__).parent.resolve()

# Ajana ayrılan çalışma alanı (Sandbox)
# Eğer bu klasör yoksa, güvenlik için oluşturulur.
WORKSPACE = BASE_DIR / "workspace"
if not WORKSPACE.exists():
    WORKSPACE.mkdir(parents=True, exist_ok=True)

# --- GÜVENLİK VE PERFORMANS LİMİTLERİ ---
# Kod çalıştırma (run_python, execute_command) için zaman aşımı süresi (saniye)
EXEC_TIMEOUT = 30

# Araçlardan dönen verilerin (Observation) maksimum karakter uzunluğu
# Bu sınır, LLM'in bağlam penceresini (context window) korumak için önemlidir.
MAX_OBSERVATION_LEN = 3500

# --- WEB ARAŞTIRMA AYARLARI ---
# Web fetcher için varsayılan zaman aşımı
FETCH_TIMEOUT = 15

# Agent tanımlayıcı (User-Agent)
USER_AGENT = "CelebiAgent/1.0 (otonom araştırma botu)"

# --- LOGLAMA VE STATS ---
STATS_FILE = BASE_DIR / "memory" / "system_stats.json"
DB_PATH = BASE_DIR / "memory" / "celebi_memory.db"
CHROMA_PATH = str(BASE_DIR / "chroma_db")

# Ajan Modelleri (16GB VRAM için Mühürlenmiş Versiyon)
ROUTER_MODEL = "qwen2.5:3b"        
CHAT_MODEL = "qwen2.5:7b"         
INFO_MODEL = "qwen2.5:7b"          

# Mantık ve Planlama (Aynı model ailesi, VRAM'de yer değiştirirken hızlıdır)
PLANNER_MODEL = "deepseek-r1:14b"  

# Kodlama ve Denetleme (BURASI KRİTİK)
CODER_MODEL = "qwen2.5-coder:7b"   # Yazım aşaması ışık hızında olsun
REVIEWER_MODEL = "deepseek-coder-v2:16b-lite-instruct-q4_K_M" # Onay makamı ağır abi olsun

REASONING_MODEL = "qwen3:14b"

# Sistem Ayarları
KEEP_ALIVE = "5m"  # Hafif modeller RAM'de 5 dakika kalsın
OLLAMA_BASE_URL = "http://localhost:11434"

# Dosya Yolları
STATS_FILE = "data/system_stats.json"
MEMORY_PATH = "./chroma_db"