from langchain_ollama import OllamaLLM
from config import CHAT_MODEL 
from prompts.planner_prompt import SYSTEM_PROMPT_PLANNER

class PlannerAgent:
    def __init__(self, memory=None, reasoning=None):
        self.memory = memory
        self.reasoning = reasoning
        self.llm = OllamaLLM(model=CHAT_MODEL)

    def run(self, task):
        """
        Planner'ın görevi: Karmaşık görevi analiz etmek, hafızadaki 
        tercihlerle birleştirmek ve mantıklı bir yol haritası çıkarmaktır.
        """
        
        # 1. ADIM: REASONING İLE STRATEJİK ANALİZ
        # Plan yapmadan önce problemin kök nedenini ve kısıtlarını analiz ettiriyoruz.
        if self.reasoning:
            analysis_request = f"Şu görevi analiz et ve olası teknik riskleri belirle: {task}"
            strategic_insight = self.reasoning.run(analysis_request)
            
            # Reasoning'den gelen öngörüyü plana dahil ediyoruz
            full_prompt = (
                f"{SYSTEM_PROMPT_PLANNER}\n\n"
                f"### STRATEJİK ÖNGÖRÜ (REASONING):\n{strategic_insight}\n\n"
                f"### GÖREV:\n{task}\n\n"
                f"Lütfen yukarıdaki öngörüyü dikkate alarak adım adım bir uygulama planı hazırla:"
            )
        else:
            full_prompt = f"{SYSTEM_PROMPT_PLANNER}\n\nGÖREV:\n{task}\n\nADIM ADIM PLAN:"

        # 2. ADIM: PLAN ÜRETİMİ
        plan_output = self.llm.invoke(full_prompt)
        
        # 3. ADIM: PLANI HAFIZAYA GÖRE KALİBRE ETME (Opsiyonel derinlik)
        # Eğer hafızada benzer bir projenin planı varsa, Planner burayı revize edebilir.
        
        return plan_output