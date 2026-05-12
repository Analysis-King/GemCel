from langchain_ollama import OllamaLLM
from config import INFO_MODEL
from prompts.info_prompt import SYSTEM_PROMPT_INFO

class InfoAgent:
    def __init__(self, memory=None, reasoning=None):
        # Hafıza ve Akıl Yürütme birimlerini içeri alıyoruz
        self.memory = memory
        self.reasoning = reasoning
        self.llm = OllamaLLM(model=INFO_MODEL)
        self.system_prompt = SYSTEM_PROMPT_INFO

    def run(self, plan_data):
        # Dispatcher'dan gelen plan verisini işle
        plan_str = str(plan_data)
        
        # 1. ADIM: BİLGİ/KOD TASLAĞI ÜRETİMİ
        full_prompt = f"{self.system_prompt}\n\nAşağıdaki plana uygun teknik döküm/kod hazırla:\n{plan_str}\n\nÇıktı:"
        initial_response = self.llm.invoke(full_prompt)
        
        # 2. ADIM: REASONING İLE TEKNİK DOĞRULAMA
        # Üretilen bilginin doğruluğunu Reasoning birimine sorgulatıyoruz
        if self.reasoning:
            validation_prompt = f"""
            Üretilen Teknik Çıktı: {initial_response}
            İstek/Plan: {plan_str}
            
            Bu çıktı teknik olarak doğru mu? Güven skoru nedir (0-100)? 
            Eksik veya riskli bir durum varsa 'REVİZE' etiketiyle belirt.
            """
            validation_result = self.reasoning.run(validation_prompt)
            
            # Eğer Reasoning 'REVİZE' diyorsa veya güven düşükse tekrar işle
            if "REVİZE" in validation_result.upper():
                refined_prompt = (
                    f"{full_prompt}\n\n"
                    f"### TESPİT EDİLEN HATALAR/RİSKLER:\n{validation_result}\n\n"
                    f"Lütfen yukarıdaki uyarıları dikkate alarak çıktıyı mükemmelleştir:"
                )
                return self.llm.invoke(refined_prompt)
        
        return initial_response