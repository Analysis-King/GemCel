import time

class RetryEngine:
    def run(self, fn, *args, retries=3, delay=1, **kwargs):
        """
        fn: Çalıştırılacak fonksiyon (örn: agent.run)
        args: Fonksiyona gidecek pozisyonel argümanlar
        retries: Deneme sayısı
        delay: Denemeler arası bekleme süresi (saniye)
        kwargs: 🔥 Yeni: Fonksiyona gidecek her türlü isimlendirilmiş (keyword) argüman (örn: tools)
        """
        last_error = None

        for i in range(retries):
            try:
                # 🔥 KRİTİK DÜZELTME: Hem *args hem de **kwargs ile çağırıyoruz.
                # Bu sayede 'tools=tool_schemas' gibi parametreler hedefine ulaşır.
                return fn(*args, **kwargs)
            except Exception as e:
                last_error = e
                # Eskişehir yerelindeki sunucuda Ollama cevap vermezse veya 
                # bir bağlantı koparsa log basarak seni bilgilendirelim
                print(f"[RETRY] Deneme {i+1}/{retries} başarısız: {str(e)}")
                if i < retries - 1:
                    time.sleep(delay)

        # Profesyonel Dokunuş: None dönmek yerine hatayı fırlatalım ki 
        # Orchestrator'daki Fallback katmanı durumu fark edip devreye girebilsin.
        raise Exception(f"Tüm denemeler ({retries}) başarısız oldu. Son hata: {str(last_error)}")