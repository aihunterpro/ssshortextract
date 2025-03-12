import os
import re
import time
import base64
import io
import pandas as pd
import streamlit as st
from zipfile import ZipFile
from mistralai import Mistral

# Function to process each image using Mistral API
def process_image_with_mistral(image_path, client, model, prompt):
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": f"data:image/png;base64,{encoded_image}"}
            ]
        }
    ]

    chat_response = client.chat.complete(model=model, messages=messages)
    phone_numbers_text = chat_response.choices[0].message.content
    return phone_numbers_text

# Function to extract phone numbers from bracketed list
def extract_phone_numbers_from_brackets(text):
    match = re.search(r'\[(.*?)\]', text)
    if match:
        phone_numbers = match.group(1).split(',')
        return [num.strip() for num in phone_numbers if num.strip()]
    return []

# Streamlit app title
st.title("Phone Number Extractor from Images")

# Choose the upload option: ZIP file or Single Image
upload_option = st.radio("Select upload option", ["ZIP File", "Single Image"])

# Mistral API setup (ideally use secure secrets for API keys)
api_key = "09gjXAzqfQLcMxBvGra3Ew4BA32w8bju"
model = "pixtral-12b-2409"
client = Mistral(api_key=api_key)

# Detailed prompt for extracting phone numbers
prompt = (
    "Extract all phone numbers from the provided image and return them as a comma-separated list "
    "within square brackets, like [phone1, phone2, phone3, ...]. If no phone numbers are found, return an empty list []."
)

# List to store results
results = []

if upload_option == "ZIP File":
    uploaded_zip = st.file_uploader("Upload a ZIP file containing images", type=["zip"])
    if uploaded_zip:
        zip_path = "uploaded.zip"
        with open(zip_path, "wb") as f:
            f.write(uploaded_zip.getbuffer())

        extracted_folder = 'extracted_images'
        with ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extracted_folder)

        for image_name in os.listdir(extracted_folder):
            if image_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.join(extracted_folder, image_name)
                st.write(f"Processing {image_name}...")
                phone_numbers_text = process_image_with_mistral(image_path, client, model, prompt)
                phone_numbers = extract_phone_numbers_from_brackets(phone_numbers_text)
                for number in phone_numbers:
                    results.append({'Phone Number': number})
                time.sleep(10)  # Sleep to avoid API rate limits

elif upload_option == "Single Image":
    uploaded_image = st.file_uploader("Upload an image file", type=["png", "jpg", "jpeg"])
    if uploaded_image:
        image_path = f"temp_{uploaded_image.name}"
        with open(image_path, "wb") as f:
            f.write(uploaded_image.getbuffer())

        st.write(f"Processing {uploaded_image.name}...")
        phone_numbers_text = process_image_with_mistral(image_path, client, model, prompt)
        phone_numbers = extract_phone_numbers_from_brackets(phone_numbers_text)
        for number in phone_numbers:
            results.append({'Phone Number': number})
        time.sleep(10)  # Sleep to avoid API rate limits

# Save results to Excel if any phone numbers were extracted
if results:
    output_excel = 'extracted_phone_numbers.xlsx'
    if os.path.exists(output_excel):
        df = pd.read_excel(output_excel)
    else:
        df = pd.DataFrame(columns=['Phone Number'])

    new_entries = pd.DataFrame(results)
    df = pd.concat([df, new_entries], ignore_index=True)
    df.to_excel(output_excel, index=False)

    st.success(f"Phone numbers extracted and saved to {output_excel}")
    st.dataframe(df)

    # Enable file download
    with open(output_excel, "rb") as file:
        btn = st.download_button(
            label="Download Excel File",
            data=file,
            file_name=output_excel,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
