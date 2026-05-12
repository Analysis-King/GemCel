from langchain_ollama import OllamaLLM
from config import REVIEWER_MODEL
from prompts.meta_prompt import SYSTEM_PROMPT_META

class ReflectorAgent: 
    def __init__(self, memory=None, reasoning=None):
        # Hafıza ve Akıl Yürütme birimlerini içeri alıyoruz
        self.memory = memory
        self.reasoning = reasoning
        self.llm = OllamaLLM(model=REVIEWER_MODEL)
        self.prompt = SYSTEM_PROMPT_META

    def run(self, task):
        """
        Meta ajan, sistemin genel performansını ve verilen yanıtın 
        kalitesini 'yansıma' (reflection) metoduyla analiz eder.
        """
        
        # 1. ADIM: ÖZ-YANSIMA (SELF-REFLECTION)
        # Mevcut görevi ve sistemin buna verdiği tepkiyi analiz etmesi istenir.
        reflection_prompt = f"{self.prompt}\n\nAnaliz Edilecek Süreç/Görev: {task}\n\nAnaliz:"
        reflection_output = self.llm.invoke(reflection_prompt)

        # 2. ADIM: REASONING İLE MANTIKSAL DERİNLİK KONTROLÜ
        # Meta ajanın yaptığı analizi, Reasoning birimine 'Mantıklı mı?' diye soruyoruz.
        if self.reasoning:
            meta_check_prompt = f"""
            Sistem Analizi (Meta): {reflection_output}
            Bu analizde bir mantık hatası var mı? Sistemin gelişimi için 
            ekstra bir strateji önerir misin?
            """
            reasoning_feedback = self.reasoning.run(meta_check_prompt)
            
            # Reasoning'den gelen stratejik feedback'i sonuca ekle
            return f"Meta-Analiz: {reflection_output}\n\nStratejik Tavsiye (Reasoning): {reasoning_feedback}"

        return f"Meta-Analiz: {reflection_output}"