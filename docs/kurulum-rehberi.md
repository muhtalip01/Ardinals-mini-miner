# Ardinals Mini Miner Kurulum ve Kullanım Rehberi

Bu rehber, Ardinals Mini Miner botunu sıfırdan kurmak isteyen kullanıcılar için hazırlanmıştır.

Rehberde şu konular anlatılır:

- Botun ne yaptığı
- Commit / reveal / inscribe mantığı
- Cüzdan hazırlığı
- Token ve stake mantığı
- `ardi-agent` gereksinimi
- Groq API key ayarı
- OpenRouter API key ayarı
- Botun dry-run ile test edilmesi
- Gerçek commit / reveal / inscribe otomasyonunun açılması
- Güvenli ve agresif çalışma modları
- Sık görülen hatalar

> Uyarı: Bu bot deneysel amaçlıdır. Finansal tavsiye değildir. Zincir üstü işlemler gerçek maliyet oluşturabilir. Yanlış cevaplar, yanlış ayarlar, API maliyeti, gas ücreti, stake/bond riski, reveal/inscribe zamanlaması veya oyun kurallarındaki değişikliklerden kullanıcı sorumludur.

---

## 1. Ardinals Mini Miner Nedir?

Ardinals Mini Miner, Ardi / Ardinals tarzı commit-reveal yapısına sahip riddle oyunlarında çalışan deneysel bir otomasyon botudur.

Botun amacı şudur:

1. Açık epoch pencerelerini takip etmek
2. Riddle / bilmece listesini okumak
3. LLM modelleriyle cevap üretmek
4. Güvenilir görünen cevapları seçmek
5. Commit işlemi yapmak
6. Reveal zamanı gelince reveal yapmak
7. Uygunsa inscribe işlemini denemek

Bot Groq ve OpenRouter destekler.

Önce Groq kullanılır. Groq rate limit veya hata verirse OpenRouter fallback olarak devreye girer.

---

## 2. Commit-Reveal Sistemi Nedir?

Bu tip oyunlarda cevap doğrudan gönderilmez.

Önce cevap gizli şekilde commit edilir:

```text
commit = cevabın hash'i
```

Sonra reveal zamanı geldiğinde gerçek cevap açıklanır:

```text
reveal = daha önce commit edilen cevabı açıklama
```

Eğer cevap doğruysa veya oyun kurallarına göre kazanırsa, son aşamada inscription / inscribe işlemi yapılabilir.

Genel akış:

```text
1. Commit
2. Bekle
3. Reveal
4. Bekle
5. Inscribe
```

Bu yüzden bot sadece cevap üretmez. Aynı zamanda commit, reveal ve inscribe zamanlamasını da takip eder.

---

## 3. Botun Genel Çalışma Mantığı

Bot çalışınca şu adımları izler:

```text
1. ardi-agent context çalıştırılır.
2. Açık commit window var mı kontrol edilir.
3. Açık epoch varsa riddle listesi alınır.
4. Riddle listesinden belirli sayıda soru seçilir.
5. Seçilen sorular Groq'a gönderilir.
6. Groq limit verirse OpenRouter devreye girer.
7. Model cevapları JSON olarak döndürür.
8. Confidence filtresi uygulanır.
9. Uygun cevaplar için commit denenir.
10. Pending kayıtlar kontrol edilir.
11. Reveal zamanı geldiyse reveal denenir.
12. Inscribe zamanı geldiyse inscribe denenir.
```

---

## 4. Gereksinimler

Botu kullanmak için şunlara ihtiyaç vardır:

- Linux veya WSL Ubuntu
- Python 3.10+
- Git
- `ardi-agent`
- Uygun bir cüzdan
- Oyun için gerekli token / stake
- Groq API key
- OpenRouter API key
- Terminal kullanımı

Windows kullanıcıları için WSL Ubuntu önerilir.

---

## 5. WSL / Ubuntu Hazırlığı

Ubuntu terminalinde sistem güncellenir:

```bash
sudo apt update
sudo apt upgrade -y
```

Gerekli paketler kurulur:

```bash
sudo apt install -y git python3 python3-pip python3-venv curl nano
```

Python kontrolü:

```bash
python3 --version
```

Git kontrolü:

```bash
git --version
```

---

## 6. Repoyu İndirme

Repo klonlanır:

```bash
git clone https://github.com/muhtalip01/Ardinals-mini-miner.git
cd Ardinals-mini-miner
```

Gerekli Python paketleri kurulur:

```bash
pip install -r requirements.txt
```

---

## 7. Cüzdan Hazırlığı

Botun zincir üstü işlem yapabilmesi için `ardi-agent` tarafından kullanılan bir cüzdan gerekir.

Genel cüzdan hazırlık akışı:

```text
1. Yeni bir cüzdan oluşturulur.
2. Private key / seed phrase güvenli şekilde saklanır.
3. Cüzdana gerekli gas veya oyun tokeni gönderilir.
4. Oyun için gerekli stake işlemi yapılır.
5. ardi-agent bu cüzdanla commit / reveal / inscribe işlemlerini yapar.
```

Private key veya seed phrase asla paylaşılmamalıdır.

Şu bilgiler GitHub'a veya herhangi bir kişiye gönderilmemelidir:

```text
private key
seed phrase
wallet.json
.env
API key
cüzdan yedek dosyaları
```

Repo içindeki `.gitignore` dosyası bu tarz dosyaların yanlışlıkla GitHub'a yüklenmesini engellemek için hazırlanmıştır.

---

## 8. Token ve Stake Mantığı

Bazı commit-reveal oyunlarında commit atabilmek için cüzdanda belirli token bulunması veya stake yapılması gerekir.

Genel mantık:

```text
1. Cüzdana gerekli token gönderilir.
2. Stake işlemi yapılır.
3. ardi-agent stake sahibi cüzdanı görür.
4. Commit işlemlerinde bu stake kullanılır.
```

Stake gereksinimi, minimum miktar, token adı ve ağ bilgisi oyunun kendi kurallarına göre değişebilir.

Bu repo şu konularda garanti vermez:

```text
sabit kazanç
sabit stake miktarı
kesin doğru cevap
kesin kazanma
sıfır risk
```

Stake ve cüzdan durumunu kontrol etmek için projenin kendi `ardi-agent` komutları kullanılmalıdır.

Örnek:

```bash
ardi-agent status
```

veya:

```bash
ardi-agent commits
```

---

## 9. ardi-agent Gereksinimi

Bu bot `ardi-agent` komut satırı aracına ihtiyaç duyar.

Bot şu komutları kullanır:

```bash
ardi-agent context
ardi-agent commits
ardi-agent commit
ardi-agent reveal
ardi-agent inscribe
```

`ardi-agent` sistemde kurulu mu kontrol edilir:

```bash
which ardi-agent
```

Örnek çıktı:

```text
/home/youruser/.local/bin/ardi-agent
```

Bu yol daha sonra `ARDI_AGENT_BIN` değişkeninde kullanılır.

Örnek:

```bash
export ARDI_AGENT_BIN="/home/youruser/.local/bin/ardi-agent"
```

`ardi-agent context` kontrolü:

```bash
/home/youruser/.local/bin/ardi-agent context
```

Açık commit window yoksa buna benzer çıktı görülebilir:

```json
{
  "status": "ok",
  "message": "No epoch is currently in commit window.",
  "data": {
    "current": null
  }
}
```

Bu hata değildir. Sadece o anda açık commit window yok demektir.

---

## 10. Groq API Key Ayarı

Groq, botun ana LLM sağlayıcısıdır.

Genel adımlar:

```text
1. Groq hesabı oluşturulur.
2. API Keys bölümünden yeni key alınır.
3. Key terminal ortam değişkeni olarak ayarlanır.
```

Geçici kullanım için:

```bash
export GROQ_API_KEY="your_groq_api_key_here"
export GROQ_MODEL="llama-3.3-70b-versatile"
```

Kalıcı kullanım için `~/.bashrc` dosyasına eklenir:

```bash
nano ~/.bashrc
```

Dosyanın sonuna eklenir:

```bash
export GROQ_API_KEY="your_groq_api_key_here"
export GROQ_MODEL="llama-3.3-70b-versatile"
```

Aktif edilir:

```bash
source ~/.bashrc
```

Kontrol:

```bash
echo $GROQ_MODEL
```

API key gizli bilgidir. Ekran görüntülerinde veya GitHub reposunda paylaşılmamalıdır.

---

## 11. OpenRouter API Key Ayarı

OpenRouter, Groq rate limit yerse fallback sağlayıcı olarak kullanılır.

Genel adımlar:

```text
1. OpenRouter hesabı oluşturulur.
2. Hesaba kredi yüklenir.
3. API Keys bölümünden yeni key alınır.
4. Key için harcama limiti belirlenmesi önerilir.
5. Key terminal ortam değişkeni olarak ayarlanır.
```

Geçici kullanım için:

```bash
export OPENROUTER_API_KEY="your_openrouter_api_key_here"
export OPENROUTER_MODEL="meta-llama/llama-3.3-70b-instruct"
```

Kalıcı kullanım için `~/.bashrc` dosyasına eklenir:

```bash
nano ~/.bashrc
```

Dosyanın sonuna eklenir:

```bash
export OPENROUTER_API_KEY="your_openrouter_api_key_here"
export OPENROUTER_MODEL="meta-llama/llama-3.3-70b-instruct"
```

Aktif edilir:

```bash
source ~/.bashrc
```

Kontrol:

```bash
echo $OPENROUTER_MODEL
```

Bot önce Groq'u dener. Groq hata veya rate limit verirse OpenRouter devreye girer.

Beklenen örnek log:

```text
Groq error 429
LLM provider=openrouter model=meta-llama/llama-3.3-70b-instruct
```

---

## 12. Ortam Değişkenleri

Bot aşağıdaki ortam değişkenlerini kullanır:

| Değişken | Açıklama |
|---|---|
| `GROQ_API_KEY` | Groq API anahtarı |
| `GROQ_MODEL` | Groq modeli |
| `OPENROUTER_API_KEY` | OpenRouter API anahtarı |
| `OPENROUTER_MODEL` | OpenRouter fallback modeli |
| `ARDI_AGENT_BIN` | ardi-agent dosya yolu |
| `ARDI_ENABLE_COMMIT` | `YES` ise gerçek commit açılır |
| `ARDI_ENABLE_PENDING` | `YES` ise reveal / inscribe takibi açılır |
| `ARDI_PENDING_MIN_EPOCH` | Bu epoch altındaki eski pending kayıtları atlar |
| `ARDI_MAX_COMMITS_PER_EPOCH` | Epoch başına maksimum commit sayısı |

Örnek:

```bash
export ARDI_AGENT_BIN="/home/youruser/.local/bin/ardi-agent"
```

---

## 13. .env Dosyası Kullanımı

Repo içinde `.env.example` dosyası vardır.

Örnek dosyadan gerçek `.env` oluşturulabilir:

```bash
cp .env.example .env
nano .env
```

Örnek `.env` içeriği:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct

ARDI_AGENT_BIN=/home/youruser/.local/bin/ardi-agent

ARDI_ENABLE_COMMIT=NO
ARDI_ENABLE_PENDING=NO
ARDI_PENDING_MIN_EPOCH=0
ARDI_MAX_COMMITS_PER_EPOCH=5
```

Gerçek API key içeren `.env` dosyası GitHub'a yüklenmemelidir.

---

## 14. İlk Test: Dry-Run

Gerçek işlem yapmadan önce dry-run ile test yapılmalıdır.

```bash
ARDI_ENABLE_PENDING=YES \
ARDI_PENDING_MIN_EPOCH=0 \
ARDI_AGENT_BIN=/home/youruser/.local/bin/ardi-agent \
GROQ_MODEL=llama-3.3-70b-versatile \
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct \
python3 mini_ardi_miner.py --dry-run --max 5
```

Dry-run modunda:

```text
Commit atılmaz.
Reveal yapılmaz.
Inscribe yapılmaz.
Sadece botun ne yapacağı gösterilir.
```

Örnek çıktı:

```text
[mini-ardi] selected riddle: {...}
[mini-ardi] LLM provider=groq
[mini-ardi] candidate word=... answer=... conf=...
[mini-ardi] dry-run would commit epoch=... word=... answer=...
```

---

## 15. Gerçek Commit Açma

Gerçek commit için `ARDI_ENABLE_COMMIT=YES` gerekir.

Örnek:

```bash
ARDI_ENABLE_COMMIT=YES \
ARDI_AGENT_BIN=/home/youruser/.local/bin/ardi-agent \
python3 mini_ardi_miner.py --max 5
```

Eğer `ARDI_ENABLE_COMMIT=YES` verilmezse bot gerçek commit atmaz.

Bu güvenlik için bilerek eklenmiştir.

---

## 16. Reveal ve Inscribe Takibi

Pending kayıtları takip etmek için:

```bash
ARDI_ENABLE_PENDING=YES
```

Bu açıkken bot şu mantıkla çalışır:

```text
status == committed  → reveal zamanı geldiyse reveal
status == revealed   → inscribe denemesi
status == won        → inscribe denemesi
```

Eski epoch kayıtlarını karıştırmamak için:

```bash
ARDI_PENDING_MIN_EPOCH=124
```

Bu ayar sayesinde belirtilen epoch altındaki eski pending kayıtlar atlanır.

Örnek:

```text
epoch 23  → atlanır
epoch 44  → atlanır
epoch 124 → takip edilir
epoch 155 → takip edilir
```

---

## 17. Dengeli Çalıştırma Modu

Dengeli mod daha az risklidir.

```bash
while true; do
  date
  ARDI_ENABLE_COMMIT=YES \
  ARDI_ENABLE_PENDING=YES \
  ARDI_PENDING_MIN_EPOCH=124 \
  ARDI_MAX_COMMITS_PER_EPOCH=5 \
  ARDI_AGENT_BIN=/home/youruser/.local/bin/ardi-agent \
  GROQ_MODEL=llama-3.3-70b-versatile \
  OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct \
  python3 mini_ardi_miner.py --max 5 || true
  echo "-----"
  sleep 60
done
```

Bu modda bot daha az riddle çözer. Yanlış cevap riski daha düşüktür.

---

## 18. Agresif Çalıştırma Modu

Agresif mod daha fazla riddle çözer.

```bash
while true; do
  date
  ARDI_ENABLE_COMMIT=YES \
  ARDI_ENABLE_PENDING=YES \
  ARDI_PENDING_MIN_EPOCH=124 \
  ARDI_MAX_COMMITS_PER_EPOCH=5 \
  ARDI_AGENT_BIN=/home/youruser/.local/bin/ardi-agent \
  GROQ_MODEL=llama-3.3-70b-versatile \
  OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct \
  python3 mini_ardi_miner.py --max 15 || true
  echo "-----"
  sleep 60
done
```

Bu modda daha fazla fırsat taranır. Ancak yanlış cevap, API maliyeti ve işlem maliyeti riski artar.

Durdurmak için:

```text
CTRL + C
```

---

## 19. Confidence Ayarı

Bot cevapları confidence değerine göre filtreler.

Genel mantık:

```text
0.90 ve üstü → güvenli mod
0.85 ve üstü → orta agresif mod
0.80 ve üstü → agresif mod
```

Daha düşük confidence daha çok commit çıkarır. Ancak yanlış cevap riski de artar.

Güvenli başlangıç için yüksek confidence önerilir.

---

## 20. max Değeri

`--max` değeri kaç riddle'ın modele gönderileceğini belirler.

Örnek:

```bash
python3 mini_ardi_miner.py --max 5
```

Daha agresif kullanım:

```bash
python3 mini_ardi_miner.py --max 15
```

Genel öneri:

```text
--max 5   → güvenli
--max 10  → orta
--max 15  → agresif
```

---

## 21. Epoch Başına Commit Sınırı

Bazı oyunlarda epoch başına commit sınırı olabilir.

Örnek hata:

```text
EPOCH_COMMIT_CAP_REACHED
Already used your 5-commit cap
```

Bu durumda aynı epoch içinde daha fazla commit atılamaz.

Bu nedenle `ARDI_MAX_COMMITS_PER_EPOCH` kullanılır:

```bash
ARDI_MAX_COMMITS_PER_EPOCH=5
```

---

## 22. Sık Görülen Hatalar

### no open commit window

Açık epoch yoktur. Hata değildir.

### Groq error 429

Groq rate limit dolmuştur. OpenRouter fallback varsa bot devam eder.

### LLM returned non-list content

Model bozuk veya yarım JSON döndürmüştür. Bot o turu atlayabilir.

### ALREADY_COMMITTED

Aynı epoch ve wordId için daha önce commit atılmıştır.

### EPOCH_COMMIT_CAP_REACHED

Epoch başına commit sınırına ulaşılmıştır.

### reveal not ready

Reveal zamanı henüz gelmemiştir. Bot sonraki döngülerde tekrar kontrol eder.

### inscribe not ready

Inscribe zamanı henüz gelmemiştir. Bot sonraki döngülerde tekrar kontrol eder.

---

## 23. Güvenlik Kontrolü

Repo paylaşılmadan önce şu kontroller yapılmalıdır:

```bash
grep -R "sk-or-v1" .
grep -R "gsk_" .
grep -R "PRIVATE" .
grep -R "private_key" .
grep -R "seed" .
grep -R "GROQ_API_KEY=" .
grep -R "OPENROUTER_API_KEY=" .
```


---

## 24. Son Uyarılar

Bu bot kazanç garanti etmez.

Riskler:

- Yanlış cevap commit edilebilir.
- Reveal zamanı kaçabilir.
- Inscribe başarısız olabilir.
- API maliyeti oluşabilir.
- Zincir üstü işlem ücreti oluşabilir.
- Stake veya bond riske girebilir.
- Oyun kuralları değişebilir.
- LLM modeli yanlış veya yarım cevap verebilir.

Bu repo eğitim, araştırma ve deneysel otomasyon amacıyla paylaşılmıştır.
