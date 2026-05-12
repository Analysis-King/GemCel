import json
from prompts.router_prompt import SYSTEM_PROMPT_ROUTER

class RouterAgent:
    def __init__(self, scorer, memory=None, reasoning=None):
        self.scorer = scorer
        self.memory = memory
        self.reasoning = reasoning 

    def run(self, task, **kwargs):
        """
        Görevi analiz ederken hafızadaki katı kuralları ve bağlamı enjekte eder.
        """
        # 1. HAFIZADAN KURALLARI VE BAĞLAMI ÇEK
        active_memory = self.memory.get_active_memory(task) if self.memory else {}
        learned_rules = active_memory.get("learned_rules", "")
        historical_context = active_memory.get("historical_context", "")
        strict_ins = active_memory.get("strict_instruction", "")

        # 2. ARAÇ ŞEMALARI
        tools = kwargs.get('tools', [])
        
        # 3. PROMPT GÜÇLENDİRME (Hallucination Guardrail)
        tool_instruction = ""
        if tools:
            tool_instruction = (
                f"\n\n### ÖĞRENİLMİŞ SİSTEM KURALLARI:\n{learned_rules}\n"
                f"### GEÇMİŞ BAĞLAM:\n{historical_context}\n"
                f"### OPERASYONEL TALİMAT: {strict_ins}\n"
                f"\n### KULLANILABİLİR ARAÇLAR:\n{json.dumps(tools, indent=2)}"
            )

        analysis_query = (
            f"{SYSTEM_PROMPT_ROUTER}\n"
            f"{tool_instruction}\n"
            f"\n\nKullanıcı İsteği: {task}\n"
            f"\nYANIT FORMATI: JSON (intent) veya Native Tool Call üret."
        )

        if self.reasoning:
            # LLM'e hem kuralları hem araç listesini gönderiyoruz
            analysis = self.reasoning.run(analysis_query, tools=tools)
            
            if isinstance(analysis, dict):
                return json.dumps(analysis)
            return analysis
            
        return json.dumps({"intent": "CHAT"})