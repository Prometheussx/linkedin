import os
import pandas as pd
from dotenv import load_dotenv
from inference_sdk import InferenceHTTPClient

# .env dosyasını yükle
load_dotenv()

# Çevresel değişkenleri al
api_url = os.getenv("API_URL")
api_key = os.getenv("API_KEY")

# İnferans istemcisini başlat
CLIENT = InferenceHTTPClient(
    api_url=api_url,
    api_key=api_key
)


def get_images_from_folder(folder_path):
    """
    Verilen klasördeki tüm resim dosyalarını döndürür.

    Args:
        folder_path (str): Resimlerin bulunduğu klasör yolu.

    Returns:
        list: Resim dosyalarının tam yolları.
    """
    images = []
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(folder_path, filename)
            images.append(image_path)
    return images


def infer_images(image_path):
    """
    Verilen resim dosyasını model üzerinden tahmin eder ve sonuçları döndürür.

    Args:
        image_path (str): Resim dosyasının tam yolu.

    Returns:
        dict: Resim tahmin sonuçları.
    """
    result = CLIENT.infer(image_path, model_id="bald-rflsm/1")
    return result


def process_predictions(image_path, result):
    """
    Tahmin sonuçlarını işler ve sınıf değerini döndürür.

    Args:
        image_path (str): Resim dosyasının tam yolu.
        result (dict): Tahmin sonuçları.

    Returns:
        dict: Dosya adından alınan index ve tahmin sınıfı.
    """
    base_name, _ = os.path.splitext(os.path.basename(image_path))  # Dosya adını uzantı olmadan alır
    pred = result.get("predictions", [])

    if pred:
        first_prediction = pred[0]
        class_label = first_prediction.get('class', 'Unknown')
        index = int(base_name)  # Dosya adından index çıkar
        return {'index': index, 'class': class_label}
    return {}


def delete_image_if_not_bald(image_path, class_label):
    """
    'not_bald' etiketiyle etiketlenen resmi siler.

    Args:
        image_path (str): Silinecek resmin tam yolu.
        class_label (str): Resim üzerindeki tahmin sınıfı.
    """
    if class_label == 'not_bald':
        print(f"Deleting image: {image_path}")
        os.remove(image_path)


def save_results_to_excel(results, excel_file):
    """
    Tahmin sonuçlarını verilen Excel dosyasına yazar.

    Args:
        results (list): Tahmin sonuçlarının olduğu liste.
        excel_file (str): Yazılacak Excel dosyasının yolu.
    """
    df_results = pd.DataFrame(results)

    if os.path.exists(excel_file):
        df_existing = pd.read_excel(excel_file)
        df_existing['index'] = df_existing.index
    else:
        df_existing = pd.DataFrame(columns=['class'])
        df_existing['index'] = pd.Series(dtype='int')

    # Birleştirilmiş veri çerçevesini oluştur
    df_combined = pd.merge(df_existing, df_results, on='index', how='right')
    df_combined = df_combined.set_index('index')

    # 'not_bald' etiketine sahip satırları çıkar
    df_combined = df_combined[df_combined['class'] != 'not_bald']

    # Excel dosyasına yaz
    df_combined.to_excel(excel_file)

    print(f"Results have been written to {excel_file}.")


def main(data_folder, excel_file):
    """
    Resim klasöründeki dosyaları işleyip tahmin sonuçlarını Excel dosyasına yazar.

    Args:
        data_folder (str): Resimlerin bulunduğu klasör yolu.
        excel_file (str): Yazılacak Excel dosyasının yolu.
    """
    images = get_images_from_folder(data_folder)
    results = []

    for image_path in images:
        print(f"Processing image: {image_path}")
        result = infer_images(image_path)
        processed_result = process_predictions(image_path, result)

        if processed_result:
            results.append(processed_result)
            delete_image_if_not_bald(image_path, processed_result['class'])

    save_results_to_excel(results, excel_file)


# Ana program
if __name__ == "__main__":
    # Resimlerin bulunduğu klasör yolu
    data_folder = 'data'

    # Excel dosyasının adı
    excel_file = 'linkedin_profiles.xlsx'

    main(data_folder, excel_file)
