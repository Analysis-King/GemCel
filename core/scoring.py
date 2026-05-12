class ScoreManager:
    def __init__(self):
        self.scores = {
            "reasoning": [],
            "reviewer": [],
            "tool": [],
            "overall_success": 0
        }

    def update(self, category, value):
        """Skorları günceller. value sayı (0-100) veya Boolean olabilir."""
        if category in self.scores:
            if isinstance(value, bool):
                value = 100 if value else 0
            self.scores[category].append(value)
            print(f"[SCORING] {category.upper()} güncellendi: {value}")

    def get_average(self, category):
        """Belirli bir kategorinin başarı ortalamasını döner."""
        values = self.scores.get(category, [])
        if not values:
            return 0
        return sum(values) / len(values)

    def get_report(self):
        """Sistemin genel sağlık raporunu döner."""
        return {cat: self.get_average(cat) for cat in self.scores if cat != "overall_success"}