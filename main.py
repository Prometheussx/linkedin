import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from scrap import login, main as scrap_main, img_download, close_driver
from model import main as model_main
from llm import process_images_in_directory
import shutil  # Klasörleri silmek için
import urllib.parse  # URL encode için

# nv dosyasını yükle
load_dotenv()


def clear_data_folder_and_excel():
    """
    'data' klasörünü ve 'linkedin_profiles.xlsx' dosyasını temizler.
    """
    data_folder = 'data'
    excel_file = 'linkedin_profiles.xlsx'

    # 'data' klasörünü sil
    if os.path.exists(data_folder):
        shutil.rmtree(data_folder)
        st.info(f"{data_folder} klasörü temizlendi.")

    # 'linkedin_profiles.xlsx' dosyasını sil
    if os.path.exists(excel_file):
        os.remove(excel_file)
        st.info(f"{excel_file} dosyası silindi.")


def scrape_linkedin_profiles(search_query, page_nos):
    """
    LinkedIn'den profilleri tarayıp Excel dosyasına kaydeder.
    """
    all_profiles_data = []

    # WebDriver'ı başlat ve LinkedIn'e giriş yap
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        login()
        st.session_state.logged_in = True  # İlk çalıştırmada giriş yapıldı

    # Profilleri tarama
    for i in range(page_nos):
        profiles_data = scrap_main(search_query=search_query, page_no=i + 1)
        all_profiles_data.extend(profiles_data)

    # Verileri Excel dosyasına yazma
    df = pd.DataFrame(all_profiles_data)
    df.to_excel('linkedin_profiles.xlsx', index=False)

    # Görselleri indirme
    img_download(df)

    st.success("LinkedIn profilleri tarandı ve görseller indirildi.")

    return 'linkedin_profiles.xlsx'


def analyze_images():
    """
    Görselleri model ile analiz eder ve sonuçları Excel'e yazar.
    """
    data_folder = 'data'
    excel_file = 'linkedin_profiles.xlsx'

    # Model ile analiz işlemi
    model_main(data_folder, excel_file)
    st.success(f"Resim analizi tamamlandı ve {excel_file} dosyasına yazıldı.")


def llm_analysis(sorun):
    """
    Görseller üzerinde LLM ile saç sorunu analizi yapar.
    """
    image_directory = "data"
    yorum = process_images_in_directory(image_directory, sorun)
    return yorum


# Streamlit uygulaması
st.title("LinkedIn Profil Analiz ve Saç Sorunu Raporu")

# Kullanıcıdan girdi alma
search_query = st.text_input("Aranacak Meslek")
page_nos = st.number_input("Taranacak Sayfa Sayısı", min_value=1, step=1)

if st.button("Profil Tarama ve Görsel Analizi Yap"):
    if search_query and page_nos:
        # Verileri temizle
        clear_data_folder_and_excel()

        # LinkedIn profilleri ve görselleri tarama ve analiz yapma
        excel_file = scrape_linkedin_profiles(search_query, page_nos)
        analyze_images()

        # LLM ile analiz yapma
        sorun = "saç dökülmesi"
        yorum = llm_analysis(sorun)

        # Excel dosyasını yükleme
        df_profiles = pd.read_excel(excel_file)

        # Eşleme ve tablo oluşturma
        result_data = []
        for i, row in df_profiles.iterrows():
            result_data.append({
                'Index': row['index'],
                'Name': row['Name'],
                'Sorun': yorum[i]['Sorun'],
                'Çözüm': yorum[i]['Çözüm'],
                'Profile Link': row['Profile Link']
            })

        df_results = pd.DataFrame(result_data)

        # Tablonun yanında buton ekleme
        st.write("LinkedIn Profil Analizi Sonuçları:")
        for index, row in df_results.iterrows():
            cols = st.columns([1, 2, 2, 10])  # Kolon genişlikleri ayarlandı
            with cols[0]:
                st.write(row['Index'])
            with cols[1]:
                st.write(row['Name'])
            with cols[2]:
                # Profil Linki Butonu
                profile_link_html = f'''
                    <a href="{row['Profile Link']}" target="_blank" style="text-decoration:none;">
                        <button style="
                            background-color: #4CAF50;
                            border: none;
                            color: white;
                            padding: 8px 16px;
                            text-align: center;
                            text-decoration: none;
                            display: inline-block;
                            font-size: 12px;
                            margin: 4px 2px;
                            cursor: pointer;
                            border-radius: 4px;
                            ">
                            Git
                        </button>
                    </a>
                '''
                st.markdown(profile_link_html, unsafe_allow_html=True)
            with cols[3]:
                # Kopyalanacak metni textarea içinde gösterme
                message = f"""
Merhaba,

Ben Estetik International Kliniği'nin estetik danışmanıyım. Estetik International olarak, sizlere en yüksek kalitede hizmet sunmak ve sorunlarınızı çözmek için buradayız.

Estetik International Hakkında Bilgi:

Estetik International, estetik ve sağlık alanında geniş bir uzmanlık yelpazesi sunarak, müşterilerine kişiselleştirilmiş ve etkili çözümler sunmayı hedefleyen bir lider kliniktir. Kaliteli hizmet anlayışımız ve deneyimli kadromuz ile estetik ihtiyaçlarınıza en iyi şekilde yanıt veriyoruz.

Belirlenen Sorun:

{row['Sorun']}

Oluşturulan Çözüm:

{row['Çözüm']}

Bu süreçte sizlere en iyi danışmanlık hizmetini sunmak ve ihtiyaçlarınıza yönelik etkili çözümler sağlamak için buradayız. Estetik International'ın sunduğu hizmetlerden faydalanmak ve sorularınızı iletmek için aşağıdaki iletişim kanallarımızdan bize ulaşabilirsiniz:

Web Sitesi: [Web sitesi URL'si]
Telefon Numarası: [Telefon numarası]
Sizlere yardımcı olabilmek için sabırsızlanıyoruz. Bizimle iletişime geçmekten çekinmeyin.

Saygılarımızla,

Estetik Danışmanı
Estetik International Kliniği
                """
                st.text_area(f"Mesaj {row['Index']}", value=message, height=5, disabled=False)

    else:
        st.warning("Lütfen meslek ve sayfa sayısı bilgilerini girin.")
