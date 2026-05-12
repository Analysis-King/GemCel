@app.websocket("/ws/{task_id}")
async def ws(websocket: WebSocket, task_id: str):

    await websocket.accept()

    await websocket.send_json({
        "type": "debug",
        "msg": "ws connected"
    })

    try:
        while True:
            msg = await emitter.listen(task_id)

            await websocket.send_json({
                "type": "event",
                "data": msg
            })

    except Exception as e:
        print("WS ERROR:", e)