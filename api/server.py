import asyncio
import uuid
from fastapi import FastAPI, WebSocket, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Core Bileşenler
from core.emitter import Emitter
from core.scoring import ScoreManager
from core.orchestrator import Orchestrator
from core.dispatcher import AgentDispatcher

# Hafıza (Memory)
from memory.memory_manager import MemoryManager


# Ajanlar ve Araçlar
from agents.chat import ChatAgent
from agents.coder import CoderAgent
from agents.info import InfoAgent
from agents.meta import ReflectorAgent
from agents.planner import PlannerAgent
from agents.reasoning import ReasoningAgent
from agents.reviewer import ReviewerAgent
from agents.tool_agent import ToolAgent
from agents.router import RouterAgent
from tools.tool_registry import ToolRegistry
from tools.code_exec import ToolExecutor
from tools.web_search import web_get
from tools.python_exec import python_exec
from config import ROUTER_MODEL

stats = {
    "successes": 0,
    "failures": 0,
    "rules": 0,
    "embedded": 0
}

app = FastAPI()

# --- 1. SİSTEM BİLEŞENLERİNİN BAŞLATILMASI ---
emitter = Emitter()
scorer = ScoreManager()
memory_manager = MemoryManager()
registry = ToolRegistry()
registry.register("web_get", web_get,"İnternet üzerinden veri çekmek için kullanılır.")
registry.register("python_exec", python_exec,"Python kodunu çalıştırmak için kullanılır.")

# 2. Modelleri ve Engine'leri Oluştur
# Hata burada: 'router' isminde bir değişkeni burada tanımlamış olmalısın



# --- 2. AJAN KONFİGÜRASYONU ---
agents = {
    "ROUTER": RouterAgent(scorer, memory=memory_manager),
    "PLANNER": PlannerAgent(memory=memory_manager),
    "CODER": CoderAgent(memory=memory_manager),
    "REVIEWER": ReviewerAgent(memory=memory_manager),
    "CHAT": ChatAgent(memory=memory_manager),
    "META": ReflectorAgent(memory=memory_manager),
    "INFO": InfoAgent(memory=memory_manager),
    "REASONING": ReasoningAgent(memory=memory_manager),
    "TOOL": ToolAgent(ToolExecutor(registry), memory=memory_manager)
}

dispatcher = AgentDispatcher(agents=agents, emitter=emitter)

orchestrator = Orchestrator(
    router=agents["ROUTER"],       # 'router' değişkeni yerine sözlükteki ROUTER ajanını veriyoruz
    dispatcher=dispatcher, # Eğer dispatcher sınıfın varsa onu, yoksa mantığını ver
    agents=agents,                 # Tüm ajan sözlüğünü olduğu gibi paslıyoruz
    emitter=emitter,
    memory=memory_manager,
    tool_registry=registry
)
# --- 3. API ENDPOINT'LERİ ---

@app.post("/api/task")
async def create_task(payload: dict, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    content = payload["task"]
    
    # WebSocket için task_id'yi kaydediyoruz
    emitter.register(task_id)
    
    # 🔥 KRİTİK: Queue yerine doğrudan Orchestrator'ı arka planda başlatıyoruz
    # Bu sayede HTTP 200 dönerken, Çelebi arkada düşünmeye başlar.
    background_tasks.add_task(orchestrator.run, content, task_id)
    
    return {"task_id": task_id}

@app.websocket("/ws/{task_id}")
async def ws_endpoint(websocket: WebSocket, task_id: str):
    await websocket.accept()
    print(f"📡 WS Bağlantısı Açıldı: {task_id}")
    try:
        while True:
            # Emitter'dan o task_id'ye ait yeni mesajları bekle
            msg = await emitter.listen(task_id)
            if msg:
                print(f"DEBUG - Frontend'e Giden: {msg}")
                await websocket.send_json(msg)
                
                # İşlem bittiyse bağlantıyı temizce kapat
                if msg.get("event") == "final":
                    break 
    except Exception as e:
        print(f"⚠️ WS Hatası ({task_id}): {e}")
    finally:
        # Kaynakları temizle
        emitter.unregister(task_id)
        print(f"🔌 WS Kapatıldı: {task_id}")

@app.get("/")
async def read_index():
    # Web klasöründeki arayüzü sunar
    return FileResponse('web/index.html')

# Statik dosyalar (JS, CSS) için
# app.mount("/static", StaticFiles(directory="web/static"), name="static")