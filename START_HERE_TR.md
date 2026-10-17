# Smart File Organizer V1.0.1 — Başlangıç Rehberi

## 1. Gereksinimler

- Python 3.11 veya daha yeni bir sürüm
- Grafik arayüzü içeren Python kurulumu (Tkinter)
- Ek `pip install` gerekmiyor

Terminalden kontrol:

```bash
python3 --version
python3 -m tkinter
```

İkinci komut küçük bir Tk penceresi açmalıdır. Pencere açılmıyorsa Python dağıtımında Tkinter bulunmuyor olabilir.

## 2. Uygulamayı aç

ZIP'i `Desktop/GITHUB Hatyja` klasörüne çıkardıktan sonra:

```bash
cd /Users/macbookpro/Desktop/GITHUB\ Hatyja/smart-file-organizer
python3 app.py
```

## 3. Kullanım

1. **Choose a folder** ile düzenlemek istediğin klasörü seç.
2. Dosya sayısını, boyutu ve önerilen kategorileri kontrol et.
3. **Preview organization** düğmesine bas ve taşınacak dosyaları tek tek incele.
4. Yalnızca plan doğru görünüyorsa taşıma işlemini onayla.
5. Gerekirse **Undo last batch** ile son taşıma grubunu geri al.
6. **Find duplicates**, aynı içeriğe sahip dosyaları SHA-256 ile bulur; hiçbirini silmez.

## Güvenlik sınırları

- Yalnızca seçilen klasörün en üst seviyesindeki normal dosyalar taranır; alt klasörlerin içi değiştirilmez.
- Gizli dosyalar ve sembolik bağlantılar atlanır.
- Dosya taşıma işlemi önizleme ve onay olmadan başlamaz.
- Çakışan isimlerin üstüne yazılmaz; numaralı yeni isim seçilir.
- Dosyalar internet üzerinden gönderilmez.
- Son işlem bilgisi seçilen klasördeki `.smart-file-organizer-history.json` dosyasına yazılır.
- Önemli dosyalar için önceden yedek almak yine de önerilir.

## 4. Testler

```bash
python3 scripts/verify_project.py
python3 -m unittest discover -s tests -v
```

## 5. Bilinen kapsam

V1 dosya türü kurallarıyla çalışır; gerçek bir yapay zekâ modeli değildir. Dosya içeriklerini okumaz, isim değiştirmez, silme yapmaz ve alt klasörleri taramaz.
