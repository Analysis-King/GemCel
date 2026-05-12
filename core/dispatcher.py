# core/dispatcher.py

class AgentDispatcher:
    def __init__(self, agents, emitter):
        self.agents = agents
        self.emitter = emitter

    async def run(self, router_output, task, task_id=None):
        print(f"DEBUG: Dispatcher'a gelen Task ID: {task_id}")
        # 1. Router çıktısını temizleyelim (Bazen 'CHAT' yerine {'intent': 'CHAT'} gelebilir)

        await self.emitter.emit(task_id, {
        "event": "thought",
        "data": {"thought": "Dispatcher aktif, ajan seçiliyor...", "stage": "DISPATCHER"}
        })
        
        if isinstance(router_output, dict):
            intent = router_output.get("intent", "").upper()
        else:
            intent = str(router_output).upper()

        await self.emitter.emit(task_id, {
            "event": "thought",
            "data": {"thought": f"Analiz bitti: Görev '{intent}' kategorisine atandı.", "stage": "DISPATCHER"}
        })

        # 2. Mantıksal Kapılar
        if "CHAT" in intent:
            await self.emitter.emit(task_id, {"event": "thought", "data": {"thought": "Sohbet ajanı hazırlanıyor...", "stage": "CHAT"}})
            # Burada 'run' metodunun senkron/asenkron oluşuna dikkat
            res = self.agents["CHAT"].run(task)
            return {"intent": "CHAT", "result": res}

        elif "CODE" in intent:
            await self.emitter.emit(task_id, {"event": "thought", "data": {"thought": "Yazılım uzmanları (Planner/Coder) devreye giriyor...", "stage": "DISPATCHER"}})
            plan = self.agents["PLANNER"].run(task)
            code = self.agents["CODER"].run(plan)
            return {"intent": "CODE", "result": code}

        # 3. Fallback (Eğer hiçbir şey tutmazsa varsayılan olarak CHAT'e yönlendir)
        await self.emitter.emit(task_id, {"event": "thought", "data": {"thought": "Kategori net değil, genel sohbet üzerinden ilerleniyor...", "stage": "CHAT"}})
        res = self.agents["CHAT"].run(task)
        return {"intent": "CHAT", "result": res}