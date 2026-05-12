from langchain_ollama import OllamaLLM
from config import CHAT_MODEL
from prompts.reasoning_prompt import SYSTEM_PROMPT_REASONING # Prompt eklendi

class ReasoningAgent:
    def __init__(self, memory=None, scorer=None):
        self.memory = memory
        self.scorer = scorer
        self.llm = OllamaLLM(model=CHAT_MODEL)
        self.system_prompt = SYSTEM_PROMPT_REASONING

    def run(self, task):
        # Prompt ve Task birleştiriliyor
        full_prompt = f"{self.system_prompt}\n\nİNCELENECEK GÖREV:\n{task}"
        
        reasoning_output = self.llm.invoke(full_prompt)
        
        # Skor ayrıştırma (Parsing)
        confidence = 0
        try:
            if "GÜVEN_SKORU:" in reasoning_output:
                score_str = reasoning_output.split("GÜVEN_SKORU:")[1].strip().split("\n")[0]
                confidence = int(score_str)
        except:
            confidence = 50

        if self.scorer:
            self.scorer.update("reasoning", confidence > 75)

        return {
            "analysis": reasoning_output,
            "confidence": confidence,
            "status": "SUCCESS" if confidence > 50 else "FAILED"
        }