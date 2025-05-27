# qwen_chat_backend

Folder Structure
```
chat-backend/
│
├── main.py                       # FastAPI app entrypoint
│
├── app/
│   ├── config.py                 # Redis + vLLM config
│
│   ├── routers/
│   │   └── chat.py               # /chat endpoint (streaming + normal)
│
│   ├── schemas/
│   │   └── chat_schema.py        # Request/response models
│
│   ├── core/
│   │   ├── llm.py                # Call vLLM server
│   │   └── redis_store.py        # Redis chat history/session logic
│
│   ├── services/
│   │   └── chat_service.py       # Logic to handle chat request flow
│
├── .env                          # Redis URL, session TTL, limits
├── requirements.txt
└── README.md
```
