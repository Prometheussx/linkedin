import os
import base64
import openai
from dotenv import load_dotenv
import tempfile

# Load environment variables (assuming you have your API key in .env)
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Sistem promptu (modelin saç uzmanı olduğunu belirtiyoruz)
system_prompt = (
    "Sen bir saç uzmanısın. "
    "Sana iletilen görseller üzerinden kişilerin saç sağlığı ile ilgili sorunlarını analiz ediyor ve estetik çözümler öneriyorsun. "
    "Analizlerin bilimsel ve estetik temellere dayanmalıdır. "
    "Çözümlerin her zaman kısa, öz ve cerrahi çözümler olmalıdır; onun dışında farklı çözümler bulmamalısın. "
    "Çözüm metnini kişiye hitaben yazman gerekiyor. Ayrıca çözüm metninde kendini bir kişi olarak betimlemelisin; sen Estetik International şirketini temsil etmektesin. "
    "Çözüm metinlerinde tavsiye ettiğin cerrahi çözümleri Estetik International bünyesinde yaptırmaları gerektiğini belirterek betimlemelisin. "
    "Örnek olarak 'saç ekim hizmetimizden faydalanmalısınız' gibi. "
    "Sorun metni yazarken cümleye her zaman 'profil resminizde analiz ettiğimiz kadarıyla' cümlesi ile başlamalısın."
)

# Resimleri base64 formatına çeviren fonksiyon
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# GPT-4 Turbo ile saç tarzı analizi yapan fonksiyon
def call_gpt4_model_for_analysis(image_base64: str, prompt: str):
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=messages,
        max_tokens=1500
    )

    return response['choices'][0]['message']['content']

# Sonuç metnini sözlüğe dönüştüren fonksiyon
def parse_result_to_dict(result,filename):
    base_name, _ = os.path.splitext(os.path.basename(filename))
    result_dict = {}
    for line in result.split('\n'):
        result_dict['index'] = base_name
        if line.startswith('Sorun:'):
            result_dict['Sorun'] = line[len('Sorun:'):].strip()
        elif line.startswith('Çözüm:'):
            result_dict['Çözüm'] = line[len('Çözüm:'):].strip()

    return result_dict

# Bir dizindeki tüm resimleri işleyen ve sonuçları döndüren fonksiyon
def process_images_in_directory(directory, sorun):
    prompt = (
        f"Profil resminizde analiz ettiğimiz kadarıyla, saçınızda özellikle tepe bölgesinde incelme ve dökülme görülüyor. "
        f"Bu, genetik faktörlerin yanı sıra yaşam tarzı ve diyet gibi çeşitli sebeplerden kaynaklanıyor olabilir. "
        f"Merhaba, benim adım {sorun} alanında sağlıksal bir sorun yaşamaktayım. "
        f"Resim üzerindeki sorunu teşhis ederek estetik alanındaki çözümü bana önerir misiniz?\n\n"
        "Sonuç şu formatta olmalıdır:\n"
        "Sorun: [Sorun açıklaması]\n"
        "Çözüm: [Çözüm önerisi]"
    )
    all_results = []
    for filename in os.listdir(directory):
        if allowed_file(filename):
            file_path = os.path.join(directory, filename)

            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
                tmp_file.write(open(file_path, 'rb').read())
                temp_filename = tmp_file.name

            base64_image = encode_image(temp_filename)
            result = call_gpt4_model_for_analysis(base64_image, prompt)

            # Temp dosyasını sil
            os.unlink(temp_filename)

            # Sonucu sözlüğe dönüştür
            result_dict = parse_result_to_dict(result, filename)
            all_results.append(result_dict)

    return all_results



# Dosya türü kontrol fonksiyonu
def allowed_file(filename):
    allowed_extensions = {'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Ana program
if __name__ == "__main__":
    # Resimlerin bulunduğu dizin
    image_directory = "data"  # Örneğin: "/Users/erdem/Desktop/images"

    # Kullanıcı bilgileri
    sorun = "saç dökülmesi"

    process_images_in_directory(image_directory, sorun)
