# Hafıza yönetimi için gerekli kütüphanelerin içe aktarılması
import sqlite3
import uuid
import chromadb
from datetime import datetime
import os

class MemoryManager:
    def __init__(self, db_path="memory/celebi_memory.db", chroma_path="./chroma_db"):
        """
        Sistem Hafıza Yöneticisi: Yapısal (SQLite) ve Semantik (ChromaDB) hafızayı yönetir.
        """
        self.sqlite_path = db_path
        self._init_sqlite()
        
        # ChromaDB - Vektörel Hafıza Başlatma
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.chroma_client.get_or_create_collection(name="celebi_memory")

    def _init_sqlite(self):
        """SQLite tablolarını hazırlar: Görev geçmişi ve öğrenilmiş kurallar."""
        os.makedirs(os.path.dirname(self.sqlite_path), exist_ok=True)
        with sqlite3.connect(self.sqlite_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                task TEXT,
                result TEXT,
                status TEXT,
                error_msg TEXT
            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS learned_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                rule TEXT,
                priority INTEGER DEFAULT 1
            )''')
            conn.commit()

    def reset_memory(self):
        """Hafızayı kalıcı olarak temizler."""
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM task_history')
                cursor.execute('DELETE FROM learned_rules')
                conn.commit()
            results = self.collection.get()
            if results and results['ids']:
                self.collection.delete(ids=results['ids'])
            return True
        except: return False

    def save_interaction(self, user_query, ai_response):
        try:
            content = f"Kullanıcı: {user_query}\nÇelebi: {ai_response}"
            self.collection.add(
                documents=[content],
                ids=[str(uuid.uuid4())],
                metadatas=[{"type": "chat_history", "timestamp": str(datetime.now())}]
            )
            self.save_task_status(user_query, ai_response, "SUCCESS")
        except: pass

    def get_context(self, current_query, n_results=3):
        try:
            results = self.collection.query(query_texts=[str(current_query)], n_results=n_results)
            return "\n---\n".join(results['documents'][0]) if results['documents'] else ""
        except: return ""

    def save_task_status(self, task, result, status, error_msg=None):
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''INSERT INTO task_history 
                    (timestamp, task, result, status, error_msg) 
                    VALUES (?, ?, ?, ?, ?)''', 
                    (datetime.now(), str(task), str(result), str(status), str(error_msg)))
                conn.commit()
        except: pass

    def get_recent_history(self, limit=5):
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''SELECT task, result FROM task_history WHERE status = 'SUCCESS' 
                                  ORDER BY timestamp DESC LIMIT ?''', (limit,))
                rows = cursor.fetchall()
                return "\n---\n".join([f"Kullanıcı: {t}\nÇelebi: {r}" for t, r in reversed(rows)]) or "Etkileşim yok."
        except: return "Hafıza okunamıyor."

    def get_rules_summary(self):
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT category, rule FROM learned_rules')
                return "\n".join([f"[{r[0]}] {r[1]}" for r in cursor.fetchall()]) or "Kural yok."
        except: return "Kurallar yüklenemedi."

    def get_active_memory(self, query):
        context = self.get_context(query)
        rules = self.get_rules_summary()
        return {
            "historical_context": context,
            "learned_rules": rules,
            "strict_instruction": (
                "### KRİTİK OPERASYONEL PROTOKOL (V14.0 - ABSOLUTE REALITY):\n"
                "1. SIFIR TAHMİN (ÖLÜMCÜL KURAL): Bir dosyanın adını bilmen, içeriğini bildiğin anlamına gelmez. 'read_file' aracından 'ERROR' veya 'Dosya bulunamadı' yanıtı alırsan, ASLA ama ASLA içerik uydurma (flask, numpy vb. yazma). Sadece 'Hata aldım, dosya okunamadı' de.\n"
                "2. ARAÇ SONUCU MUTLAKTIR: Eğer 'read_file' sonucu boş gelirse, dosya boştur. Eğer hata gelirse, dosya yoktur. Hafızandaki eski (uydurma) verileri kesinlikle YOK SAY.\n"
                "3. WSL YOL TEMİZLİĞİ: Kullanıcı '\\\\wsl.localhost\\Ubuntu\\home\\karabasan\\Gemini\\Requirements.txt' verirse, sen bunu '/home/karabasan/Gemini/Requirements.txt' olarak işleme al. Eğer WORKSPACE içindeyse sadece dosya adını ('Requirements.txt') kullan.\n"
                "4. SOHBET YASAKTIR: Dosya okuma/yazma görevlerinde 'Niyet: CHAT' olamaz. Her zaman bir TOOL_CALL tetiklenmelidir.\n"
                "5. KOD BLOKLARI ENGELLİ: Kullanıcıya çözüm için kod yazıp verme. O kodu 'run_python' ile sen çalıştır ve sadece sonucu söyle.\n"
                "6. DİL: Sadece TÜRKÇE konuş."
            )
        }

    def get_stats(self):
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT status, COUNT(*) FROM task_history GROUP BY status")
                counts = dict(cursor.fetchall())
                cursor.execute("SELECT COUNT(*) FROM learned_rules")
                return {
                    "successes": counts.get("SUCCESS", 0),
                    "failures": counts.get("FAILURE", 0),
                    "rules": cursor.fetchone()[0],
                    "embedded": self.collection.count()
                }
        except: return {"successes": 0, "failures": 0, "rules": 0, "embedded": 0}