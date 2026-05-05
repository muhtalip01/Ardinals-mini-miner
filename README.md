# Ardinals Mini Miner

Ardinals Mini Miner, Ardi / Ardinals tarzı commit-reveal yapısına sahip riddle oyunlarında açık epoch pencerelerini takip eden, çok dilli bilmeceleri LLM modelleriyle çözmeye çalışan deneysel bir Python otomasyon aracıdır.

Bu araç Groq ve OpenRouter destekler. Önce Groq denenir, Groq rate limit veya hata verirse OpenRouter fallback olarak devreye girer.

## Özellikler

- `ardi-agent context` çıktısını okuyarak açık commit window tespiti
- Çok dilli riddle çözümü
- Groq ana LLM sağlayıcısı
- OpenRouter fallback desteği
- Confidence filtresi
- Dry-run modu
- Gerçek commit için güvenlik kilidi
- Pending commit takibi
- Reveal otomasyonu
- Inscribe otomasyonu
- Eski epoch kayıtlarını atlamak için `ARDI_PENDING_MIN_EPOCH`
- Epoch başına commit limitine uygun çalışma
- JSON parse hatalarında döngünün çökmesini engelleme

## Uyarı

Bu repo deneysel amaçlıdır. Finansal tavsiye değildir. Zincir üstü işlemler gerçek maliyet oluşturabilir.

Yanlış cevaplar, rate limit, ağ hataları, reveal/inscribe zamanlaması veya oyun kurallarındaki değişikliklerden kaynaklanan kayıplardan kullanıcı sorumludur.

API key, private key, seed phrase veya `.env` dosyanızı asla GitHub'a yüklemeyin.

## Gereksinimler

- Python 3.10+
- `ardi-agent`
- Groq API key
- OpenRouter API key, opsiyonel ama önerilir
- Linux / WSL ortamı

