import streamlit as st
from PIL import Image, ImageOps
from docx import Document
import os
import base64
import zipfile
import io
import tempfile
import json
import time
import requests

class Text2ImageAPI:

    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    def get_model(self):
        response = requests.get(self.URL + 'key/api/v1/models', headers=self.AUTH_HEADERS)
        data = response.json()
        return data[0]['id']

    def generate(self, prompt, model, images=1, width=1024, height=1024):
        params = {
            "type": "GENERATE",
            "numImages": images,
            "width": width,
            "height": height,
            "generateParams": {
                "query": f"{prompt}"
            }
        }

        data = {
            'model_id': (None, model),
            'params': (None, json.dumps(params), 'application/json')
        }
        response = requests.post(self.URL + 'key/api/v1/text2image/run', headers=self.AUTH_HEADERS, files=data)
        data = response.json()
        return data['uuid']

    def check_generation(self, request_id, attempts=10, delay=10):
        while attempts > 0:
            response = requests.get(self.URL + 'key/api/v1/text2image/status/' + request_id, headers=self.AUTH_HEADERS)
            data = response.json()
            if data['status'] == 'DONE':
                return data['images']

            attempts -= 1
            time.sleep(delay)

# Функция для изменения размера изображения
def resize_image(image, width, height):
    resized_image = ImageOps.fit(image, (width, height), Image.ANTIALIAS)
    return resized_image

# Функция для очистки метаданных с фотографии
def clear_metadata(image):
    data = list(image.getdata())
    image_without_exif = Image.new(image.mode, image.size)
    image_without_exif.putdata(data)
    return image_without_exif

# Функция для замены слова "Namecompany" в документе Word
def replace_word_in_docx(replacement):
    with open("EULA.docx", "rb") as f:
        docx_bytes = io.BytesIO(f.read())

    doc = Document(docx_bytes)
    for paragraph in doc.paragraphs:
        paragraph.text = paragraph.text.replace("Namecompany", replacement)

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        doc.save(temp_file.name)
        temp_file.close()
        return temp_file.name

# Функция для создания ссылки на скачивание файла
def get_binary_file_downloader_html(bin_file, file_label='File', file_name='file.docx'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{file_name}">{file_label}</a>'
    return href

def main():
    st.title("Меню")

    menu = ["Изменение размера фото", "Создание EULA", "Очистка метаданных с фото", "Текст в изображение"]
    choice = st.sidebar.selectbox("Выберите функцию", menu)

    if choice == "Изменение размера фото":
        st.header("Изменение размера фото")
        uploaded_files = st.file_uploader("Загрузите изображения", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        if uploaded_files:
            width = st.number_input("Ширина", value=1242)
            height = st.number_input("Высота", value=2208)
            if st.button("Изменить размер"):
                zipped_images = io.BytesIO()
                with zipfile.ZipFile(zipped_images, 'a') as zip_file:
                    for idx, uploaded_file in enumerate(uploaded_files):
                        image = Image.open(uploaded_file)
                        st.image(image, caption=f"Оригинальное изображение {idx+1}", use_column_width=True)
                        resized_image = resize_image(image, width, height)
                        st.image(resized_image, caption=f"Измененное изображение {idx+1}", use_column_width=True)
                        save_path = f"resized_image_{idx+1}.png"
                        resized_image.save(save_path)
                        zip_file.write(save_path)
                        os.remove(save_path)
                zipped_images.seek(0)
                st.markdown(f"### [Скачать все изображения архивом](data:application/zip;base64,{base64.b64encode(zipped_images.read()).decode()})", unsafe_allow_html=True)

    elif choice == "Создание EULA":
        st.header("Создание EULA")
        replacement = st.text_input("Введите название приложения", "aboba")
        if st.button("Создать"):
            temp_file_path = replace_word_in_docx(replacement)
            st.success("EULA успешно создан")
            st.markdown(get_binary_file_downloader_html(temp_file_path, file_label="Скачать EULA", file_name="ready.docx"), unsafe_allow_html=True)
            os.remove(temp_file_path)

    elif choice == "Очистка метаданных с фото":
        st.header("Очистка метаданных с фото")
        uploaded_files_images = st.file_uploader("Выберите фотографии", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        if uploaded_files_images:
            zipped_images = io.BytesIO()
            with zipfile.ZipFile(zipped_images, 'a') as zip_file:
                for idx, uploaded_file in enumerate(uploaded_files_images):
                    image = Image.open(uploaded_file)
                    st.image(image, caption=f"Оригинальное изображение {idx+1}", use_column_width=True)
                    image_without_exif = clear_metadata(image)
                    st.image(image_without_exif, caption=f"Изображение без метаданных {idx+1}", use_column_width=True)
                    save_path = f"image_without_exif_{idx+1}.png"
                    image_without_exif.save(save_path)
                    zip_file.write(save_path)
                    os.remove(save_path)
            zipped_images.seek(0)
            st.markdown(f"### [Скачать все изображения без метаданных](data:application/zip;base64,{base64.b64encode(zipped_images.read()).decode()})", unsafe_allow_html=True)

    elif choice == "Текст в изображение":
        st.title("Текст в изображение")
        api = Text2ImageAPI('https://api-key.fusionbrain.ai/', 'D4223B015F11F96F5F216A3EAFD936FA', '29B91ECF5F8B9A8E1B7DBE89AA595D74')
        model_id = api.get_model()

        prompt = st.text_input("Введите текст для генерации изображения", "Sun in sky")
        num_images = st.number_input("Количество изображений для генерации", value=1)
        width = st.number_input("Ширина изображения", value=1024)
        height = st.number_input("Высота изображения", value=1024)

        if st.button("Сгенерировать изображение"):
            uuid = api.generate(prompt, model_id, images=num_images, width=width, height=height)
            st.info("Идет генерация изображения...")
            images = api.check_generation(uuid)
            st.success("Генерация завершена!")

            if isinstance(images, list):
                st.markdown("### Результаты:")
                for idx, image_base64 in enumerate(images):
                    # Декодируем строку base64 в бинарные данные
                    image_data = base64.b64decode(image_base64)
                    # Открываем файл для записи бинарных данных изображения
                    with open(f"generated_image_{idx+1}.jpg", "wb") as file:
                        file.write(image_data)
                    image = Image.open(io.BytesIO(image_data))
                    st.image(image, caption=f"Изображение {idx+1}", use_column_width=True)
            else:
                st.error("При генерации изображения произошла ошибка. Попробуйте еще раз.")

if __name__ == "__main__":
    main()
