class BaseAgent:
    """Tüm ajanlar için ortak ata sınıf."""
    def __init__(self, model, system_prompt, memory=None, reasoning=None):
        self.model = model
        self.system_prompt = system_prompt
        self.memory = memory
        self.reasoning = reasoning

    def run(self, task):
        # Genel LLM çağrısı burada standartlaştırılabilir
        pass

class ToolAgent:
    def __init__(self, executor, memory=None):
        # ToolAgent fiili iş yaptığı için genellikle reasoning'i 
        # executor katmanında kullanır, ama memory'yi log tutmak için alıyoruz.
        self.executor = executor
        self.memory = memory

    def run(self, task: dict):
        """
        task: {'tool': 'google_search', 'input': 'Eskişehir hava durumu'} gibi.
        """
        tool = task.get("tool")
        input_data = task.get("input")

        # İşlemi yürüt
        result = self.executor.execute(tool, input_data)
        
        # Eğer bir hafıza varsa, bu araç kullanımını günlüğe kaydedebiliriz
        if self.memory and hasattr(self.memory, 'log_tool_usage'):
            self.memory.log_tool_usage(tool, input_data, result)

        return result