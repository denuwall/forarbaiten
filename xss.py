import streamlit as st
from PIL import Image, ImageOps
from docx import Document
import os
import base64
import zipfile
import io
import tempfile

# Функция для изменения размера изображения
def resize_image(image, width, height):
    resized_image = image.resize((width, height))
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

    menu = ["Изменение размера фото", "Замена слова в документе Word", "Очистка метаданных с фото"]
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

    elif choice == "Замена слова в документе Word":
        st.header("Замена слова в документе Word")
        replacement = st.text_input("Введите новое слово для замены", "aboba")
        if st.button("Заменить слово"):
            temp_file_path = replace_word_in_docx(replacement)
            st.success("Слово успешно заменено в документе")
            st.markdown(get_binary_file_downloader_html(temp_file_path, file_label="Скачать измененный документ", file_name="ready.docx"), unsafe_allow_html=True)
            os.remove(temp_file_path)

    elif choice == "Очистка метаданных с фото":
        st.header("Очистка метаданных с фото")
        uploaded_files = st.file_uploader("Загрузите изображения", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        if uploaded_files:
            if st.button("Очистить метаданные"):
                zip_buffer_images = io.BytesIO()
                with zipfile.ZipFile(zip_buffer_images, 'a') as zip_file:
                    for idx, uploaded_file in enumerate(uploaded_files):
                        with st.spinner(f"Обработка изображения {idx+1}..."):
                            image = Image.open(uploaded_file)
                            image_without_exif = clear_metadata(image)
                            save_path = f"image_without_exif_{idx+1}.png"
                            image_without_exif.save(save_path)
                            zip_file.write(save_path)
                            os.remove(save_path)
                            st.success(f"Изображение {idx+1} успешно обработано")
                zip_buffer_images.seek(0)
                st.markdown(f"### [Скачать все изображения без метаданных](data:application/zip;base64,{base64.b64encode(zip_buffer_images.read()).decode()})", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
