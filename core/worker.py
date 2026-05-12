import asyncio

async def worker(queue, orchestrator):
    while True:
        task_data = await queue.get() # {'id': '...', 'task': '...'}
        # 🔥 BURASI KRİTİK: task_id'yi mutlaka geçmelisin
        await orchestrator.run(task_data["task"], task_data["id"])