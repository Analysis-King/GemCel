import os
import sys
import sqlite3
import shutil

# Proje dizin yapılandırması
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "memory", "celebi_memory.db")
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

def reset_system_memory():
    """
    MemoryManager sınıfından bağımsız olarak tüm veritabanlarını temizler.
    """
    print("\n" + "="*40)
    print("🧭 ÇELEBİ HAFIZA SIFIRLAMA OPERASYONU")
    print("="*40)

    # 1. SQLite Veritabanını Temizle
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Tabloları silmek yerine içeriklerini boşaltıyoruz (Schema korunur)
            cursor.execute('DELETE FROM task_history')
            cursor.execute('DELETE FROM learned_rules')
            
            conn.commit()
            conn.close()
            print("✅ SQLite: Görev geçmişi ve kurallar temizlendi.")
        except Exception as e:
            print(f"❌ SQLite Hatası: {e}")
    else:
        print("ℹ️  SQLite veritabanı dosyası bulunamadı, atlanıyor.")

    # 2. ChromaDB Vektör Hafızasını Temizle
    if os.path.exists(CHROMA_PATH):
        try:
            # ChromaDB'yi tamamen temizlemek için en güvenli yol 
            # dizini silip yeniden oluşturulmasına izin vermektir
            import chromadb
            client = chromadb.PersistentClient(path=CHROMA_PATH)
            
            # Koleksiyonu silip yeniden oluşturarak içini boşaltıyoruz
            try:
                client.delete_collection(name="celebi_memory")
                client.create_collection(name="celebi_memory")
                print("✅ ChromaDB: Vektör koleksiyonu sıfırlandı.")
            except Exception:
                # Koleksiyon yoksa sadece dizini kontrol etmesi yeterli
                print("ℹ️  Vektör koleksiyonu zaten temiz veya mevcut değil.")
                
        except ImportError:
            print("⚠️  ChromaDB kütüphanesi yüklü değil, vektör hafızası temizlenemedi.")
        except Exception as e:
            print(f"❌ ChromaDB Hatası: {e}")
    else:
        print("ℹ️  ChromaDB dizini bulunamadı, atlanıyor.")

    print("="*40)
    print("✨ İşlem Tamamlandı: Çelebi artık tertemiz bir hafızayla başlayacak.")
    print("="*40 + "\n")

if __name__ == "__main__":
    # Kullanıcıdan onay alma (Opsiyonel - Doğrudan çalıştırmak için kaldırılabilir)
    confirm = input("Tüm hafızayı silmek istediğinize emin misiniz? (e/h): ")
    if confirm.lower() == 'e':
        reset_system_memory()
    else:
        print("İşlem iptal edildi.")