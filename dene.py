import onnxruntime as ort
import os

# Bulduğumuz gerçek yol
model_path = "/home/karabasan/.cache/chroma/onnx_models/all-MiniLM-L6-v2/onnx/model.onnx"

if not os.path.exists(model_path):
    print("❌ HATA: Dosya yolu yanlış, lütfen yolu kontrol et.")
else:
    # TensorRT hatasından kaçmak için sadece CUDA ve CPU
    providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
    
    try:
        session = ort.InferenceSession(model_path, providers=providers)
        print("✅ Başarılı! ChromaDB'nin Embedding modeli CUDA ile yüklendi.")
        print(f"Aktif Sağlayıcı: {session.get_providers()}")
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")