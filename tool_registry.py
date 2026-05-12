"""
Tool Registry v6.9 — Dynamic Registration Support

server.py'nin 'registry.register' çağrısını karşılayacak şekilde güncellendi.
Artık yeni araçlar (web_get vb.) çalışma zamanında eklenebilir.
"""
import json
from tools.code_exec import run_python, execute_command
from tools.filesystem import read_file, write_file
from tools.web.fetcher import web_fetch

class ToolRegistry:
    def __init__(self):
        # Varsayılan araçların fonksiyonel eşleşmeleri
        self.tools = {
            "run_python": lambda inp: run_python(inp.get("code", "")),
            "execute_command": lambda inp: execute_command(inp.get("command", "")),
            "read_file": lambda inp: read_file(inp.get("path", "")),
            "write_file": lambda inp: write_file(
                inp.get("path", ""), inp.get("content", "")
            ),
            "web_fetch": lambda inp: web_fetch(
                inp.get("url", ""),
                inp.get("extract_text", False),
            ),
        }
        
        # Statik şemalar listesi
        self.schemas = self._get_default_schemas()

    def _get_default_schemas(self):
        """Varsayılan araçlar için JSON şemalarını tanımlar."""
        return [
            {
                "name": "read_file",
                "description": "Belirtilen yoldaki dosyanın içeriğini okur.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Dosya yolu"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "Belirtilen dosyaya içerik yazar.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Dosya yolu"},
                        "content": {"type": "string", "description": "Yazılacak içerik"}
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "run_python",
                "description": "Güvenli sandbox içinde Python kodu çalıştırır.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "Python kodu"}
                    },
                    "required": ["code"]
                }
            },
            {
                "name": "execute_command",
                "description": "Sistem komutu çalıştırır.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Bash komutu"}
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "web_fetch",
                "description": "Web sitesinden veya API'den veri çeker.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "Erişilecek URL"},
                        "extract_text": {"type": "boolean", "description": "Sadece metni ayıkla"}
                    },
                    "required": ["url"]
                }
            }
        ]

    def register(self, name, func, description=""):
        """
        FIX: server.py'den gelen yeni araçları sisteme dahil eder.
        """
        # Fonksiyonu araç listesine ekle
        self.tools[name] = func
        
        # Dinamik şemasını oluşturup listeye ekle
        new_schema = {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Araç girişi"}
                }
            }
        }
        self.schemas.append(new_schema)
        print(f"[REGISTRY] Yeni araç eklendi: {name}")

    def get_tool_schemas(self):
        """Aktif tüm araç şemalarını döner."""
        return self.schemas

    def execute(self, action: str, action_input: dict) -> str:
        """Belirtilen aracı çalıştırır."""
        if action not in self.tools:
            return f"HATA: '{action}' adında bir araç bulunmuyor."

        try:
            # Gelen veriyi işle ve çalıştır
            return self.tools[action](action_input)
        except Exception as e:
            return f"HATA: Araç ({action}) çalışırken bir aksaklık oldu: {str(e)}"