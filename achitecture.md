                ┌──────────────┐
User Request →  │  API Layer   │
                └──────┬───────┘
                       ↓
              ┌──────────────┐
              │  Task Queue  │  ← async queue
              └──────┬───────┘
                     ↓
          ┌──────────────────────┐
          │  Router Agent        │
          └────────┬─────────────┘
                   ↓
     ┌──────────────────────────────┐
     │ Parallel Execution Layer      │
     │                              │
     │  Planner   Memory Retriever  │
     │  Tool Executor               │
     └────────────┬─────────────────┘
                  ↓
          ┌──────────────┐
          │  Coder Agent  │
          └──────┬───────┘
                 ↓
          ┌──────────────┐
          │ Reviewer     │
          └──────┬───────┘
                 ↓
        Retry / Fallback Engine
                 ↓
            FINAL RESPONSE








ai_system/
│
├── api/
│   ├── server.py              # FastAPI + WebSocket
│   └── routes.py
│
├── core/
│   ├── queue.py              # Async task queue
│   ├── orchestrator.py       # main pipeline manager
│   └── emitter.py            # event stream system
│
├── agents/
│   ├── router.py
│   ├── planner.py
│   ├── coder.py
│   ├── reviewer.py
│   ├── memory_agent.py
│   └── tool_agent.py
│
├── tools/
│   ├── tool_registry.py
│   ├── executor.py
│   └── web_search.py
│
├── engine/
│   ├── retry.py
│   └── fallback.py
│
├── memory/
│   ├── vector_store.py      # FAISS / Chroma
│   └── memory_manager.py
│
└── web(GUI)/
    └── index.html