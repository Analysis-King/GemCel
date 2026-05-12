from langchain_ollama import OllamaLLM
from config import CODER_MODEL
from prompts.coder_prompt import SYSTEM_PROMPT_CODER

class CoderAgent:
    def __init__(self, memory=None, reasoning=None):
        # Hafıza ve Akıl Yürütme birimlerini enjekte ediyoruz
        self.memory = memory
        self.reasoning = reasoning
        self.llm = OllamaLLM(model=CODER_MODEL)

    def run(self, plan_data):
        """
        plan_data: Orchestrator'dan gelen (Plan + Görev + Hafıza) metni.
        """
        
        # 1. ADIM: MANTIKSAL ANALİZ (REASONING)
        # Kod yazmaya başlamadan önce, planın teknik doğruluğunu Reasoning'e soruyoruz.
        if self.reasoning:
            analysis_prompt = f"Şu planı teknik açıdan incele ve en verimli algoritmayı öner:\n{plan_data}"
            logic_advice = self.reasoning.run(analysis_prompt)
            
            # Reasoning'den gelen tavsiyeyi prompt'a ekliyoruz
            enriched_prompt = (
                f"{SYSTEM_PROMPT_CODER}\n\n"
                f"### TEKNİK STRATEJİ (REASONING):\n{logic_advice}\n\n"
                f"### UYGULANACAK PLAN:\n{plan_data}\n\n"
                f"Kodu en yüksek standartlarda yaz:"
            )
        else:
            enriched_prompt = f"{SYSTEM_PROMPT_CODER}\n\nUygulanacak Plan:\n{plan_data}\n\nKod:"

        # 2. ADIM: KOD ÜRETİMİ
        generated_code = self.llm.invoke(enriched_prompt)
        
        # 3. ADIM: HAFIZA KONTROLÜ (Opsiyonel)
        # Eğer hafızada bu kodun bir önceki versiyonu veya benzeri varsa, 
        # Coder buna göre ince ayar yapabilir. 
        # (Şu anki akışta Orchestrator bunu plan_data içinde veriyor zaten.)

        return generated_code