import json
from langchain_ollama import OllamaLLM
from config import REVIEWER_MODEL
from prompts.reviewer_prompt import SYSTEM_PROMPT_REVIEWER

class ReviewerAgent:
    def __init__(self, memory=None, reasoning=None):
        self.memory = memory
        self.reasoning = reasoning
        self.llm = OllamaLLM(model=REVIEWER_MODEL)
        self.system_prompt = SYSTEM_PROMPT_REVIEWER

    def run(self, code: str):
        """
        Reviewer artık hem basit kural kontrolü yapıyor hem de 
        Reasoning birimine kodun mantıksal doğruluğunu onaylatıyor.
        """
        
        # 1. ADIM: BASİT KURAL KONTROLLERİ (Hızlı Denetim)
        issues = []
        if "print(" in code: issues.append("Debug print detected")
        if "TODO" in code: issues.append("Incomplete implementation")
        
        # 2. ADIM: REASONING İLE MANTIKSAL DENETİM (Derin Denetim)
        logic_score = 100
        if self.reasoning:
            logic_check_prompt = f"""
            Aşağıdaki kodu teknik ve mantıksal açıdan incele. 
            Güvenlik açığı, performans kaybı veya mantık hatası var mı?
            Kod:
            {code}
            
            Yanıtını şu formatta ver:
            MANTIK_SKORU: [0-100]
            TESPİTLER: [Hataları virgülle ayırarak yaz]
            """
            logic_analysis = self.reasoning.run(logic_check_prompt)
            
            # Reasoning'den gelen skoru ve hataları ayıklıyoruz
            try:
                if "MANTIK_SKORU:" in logic_analysis:
                    logic_score = int(logic_analysis.split("MANTIK_SKORU:")[1].split("\n")[0].strip())
                if "TESPİTLER:" in logic_analysis:
                    logic_issues = logic_analysis.split("TESPİTLER:")[1].strip().split(",")
                    issues.extend([i.strip() for i in logic_issues if i.strip()])
            except:
                logic_score = 70 # Hata durumunda güvenli liman

        # 3. ADIM: NİHAİ SKOR HESAPLAMA
        # Basit hatalar ve mantık skoru harmanlanıyor
        base_score = 100 - (len([i for i in issues if "detected" in i or "TODO" in i]) * 10)
        final_score = (base_score + logic_score) // 2

        return {
            "score": final_score, 
            "issues": issues, 
            "status": "OK" if final_score > 75 else "NEEDS_IMPROVEMENT"
        }