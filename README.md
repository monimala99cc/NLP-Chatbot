# 🍔 Online Food Delivery NLP Chatbot

An **end-to-end NLP-powered chatbot** for online food delivery.  
The chatbot allows users to seamlessly **place new orders**, **remove food items**, and **track existing orders**.  

---

## 🚀 Features
- 🆕 **Place New Orders** – add food items with quantities to your order.  
- ❌ **Remove Food Items** – update or remove items from the order.  
- 📦 **Track Orders** – check the status of your order using an order ID.  

---

## 🛠️ Tech Stack
- **Frontend (NLP Interface)** 
- **Backend (API Layer)**  
- **Database (Persistence)** 

---

## Exposing FastAPI to Dialogflow (ngrok)
Dialogflow requires a public **HTTPS endpoint** for webhook calls.  
During development, we used [ngrok](https://ngrok.com/) to expose the FastAPI backend securely:

```bash
ngrok http 8000

---

## 📂 Project Structure
┣📂 backend # FastAPI backend code
┣ 📂 dialogflow_assets # Dialogflow agent training texts
┣ 📂 db # MySQL scripts (schema, sample data)
┣ 📜 README.md # Project documentatio
