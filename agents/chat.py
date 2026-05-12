from langchain_ollama import OllamaLLM
from config import CHAT_MODEL
from prompts.base_persona import BASE_PERSONA

class ChatAgent:
    def __init__(self, memory=None, reasoning=None):
        # Hafıza ve Mantık birimlerini içeri alıyoruz
        self.memory = memory
        self.reasoning = reasoning
        self.llm = OllamaLLM(model=CHAT_MODEL)

    def run(self, task):
        """
        Orchestrator'dan gelen 'enriched_task' (hafıza + soru) zaten context içeriyor.
        Ancak ChatAgent, cevabını oluşturmadan önce Reasoning'e danışabilir.
        """
        
        # 1. PERSONA VE GÖREV BİRLEŞTİRME
        full_prompt = f"{BASE_PERSONA}\n\nKullanıcı İsteği: {task}"
        
        # 2. İLK CEVAP TASLAĞI ÜRETİMİ
        initial_response = self.llm.invoke(full_prompt)

        # 3. REASONING İLE CEVAP KALİTESİNİ VE MANTIĞINI SORGULAMA
        # Eğer sistemde bir Reasoning varsa, cevabı bir kez daha kontrol ettirelim
        if self.reasoning:
            reasoning_check = f"""
            Kullanıcı sorusu: {task}
            Üretilen cevap taslağı: {initial_response}
            
            Bu cevap mantıklı mı, eksik bilgi var mı? Cevap tatmin ediciyse 'OK', 
            iyileştirilmesi gerekiyorsa 'DÜZELT' ve önerini yaz.
            """
            check_result = self.reasoning.run(reasoning_check)
            
            # Eğer Reasoning skoru veya analizi 'iyileştirme' diyorsa cevabı revize et
            if "DÜZELT" in check_result.upper():
                final_prompt = f"{full_prompt}\n\nMantık Birimi Önerisi: {check_result}\n\nCevabı Revize Et:"
                final_response = self.llm.invoke(final_prompt)
                return final_response

        return initial_response