import asyncio

class Emitter:
    def __init__(self):
        self.queues = {}

    def register(self, task_id):
        if task_id not in self.queues:
            self.queues[task_id] = asyncio.Queue()

    # 🔥 EKSİK OLAN METOD:
    def unregister(self, task_id):
        """İşlem bittiğinde veya bağlantı koptuğunda kuyruğu temizler."""
        if task_id in self.queues:
            del self.queues[task_id]
            print(f"[EMITTER] Bellek temizlendi: {task_id}")

    async def emit(self, task_id, data):
        if task_id in self.queues:
            await self.queues[task_id].put(data)

    async def listen(self, task_id):
        if task_id in self.queues:
            return await self.queues[task_id].get()
        return None