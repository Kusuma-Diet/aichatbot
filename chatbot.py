import os
from dotenv import load_dotenv
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch
from groq import Groq
from flask import Flask, request, jsonify, render_template
import os
from werkzeug.utils import secure_filename
import PyPDF2

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}


# FACTS_FILE = "facts.txt"
# if not os.path.exists(FACTS_FILE):
#     with open(FACTS_FILE, "w") as f:
#         f.write("AI stands for Artificial Intelligence.\nGroq accelerates LLMs.\nPDFs store structured documents.\n")

# with open(FACTS_FILE, "r") as f:
#     FACTS = f.readlines()



# Groq client
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=groq_api_key)

# def retrieve_context(query):
#     query = query.lower()
#     relevant_facts = [fact.strip() for fact in FACTS if any(word in fact.lower() for word in query.split())]
#     return " ".join(relevant_facts)

# Dummy knowledge base for RAG
rag_knowledge_base = {
    "ai": "Artificial Intelligence (AI) is the simulation of human intelligence processes by machines.",
    "rag": "Retrieval-Augmented Generation (RAG) enhances LLMs by incorporating retrieved context.",
    "image captioning": "Image captioning is the process of generating text to describe an image using models like BLIP.",
    "groq": "Groq provides high-speed inference for open-source LLMs like LLaMA-3 using their GroqCloud APIs.",
    "pdf": "PDF summarization allows extraction of main points from lengthy documents using LLMs."
}

def retrieve_context(query):
    query = query.lower()
    for key, context in rag_knowledge_base.items():
        if key in query:
            return context
    return ""

def process_text_query(query):
    try:
        context = retrieve_context(query)
        prompt = f"{context}\n\nUser: {query}" if context else query
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful and concise chatbot. Use any context provided to answer queries."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=250,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: Could not process text query. {str(e)}"

def describe_image(image_path):
    try:
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        image = Image.open(image_path).convert("RGB")
        inputs = processor(images=image, return_tensors="pt")
        with torch.no_grad():
            outputs = model.generate(**inputs)
        caption = processor.decode(outputs[0], skip_special_tokens=True)
        return f"Image Description: {caption}"
    except Exception as e:
        return f"Error: Could not process image. {str(e)}"

def summarize_pdf(file_path):
    try:
        reader = PyPDF2.PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        if not text.strip():
            return "Error: No readable text found in the PDF."
        trimmed = text[:2000]  # limit length to fit into prompt
        prompt = f"Please summarize the following document content:\n\n{trimmed}"
        return process_text_query(prompt)
    except Exception as e:
        return f"Error: Failed to read PDF. {str(e)}"

# Route
@app.route('/')
def index():
    return render_template('index.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        if 'file' in request.files and request.files['file'].filename:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                ext = filename.rsplit('.', 1)[1].lower()
                if ext in ['jpg', 'jpeg', 'png']:
                    response = describe_image(file_path)
                elif ext == 'pdf':
                    response = summarize_pdf(file_path)
                else:
                    response = "Unsupported file format."

                os.remove(file_path)  # clean up
                return jsonify({'response': response})
            else:
                return jsonify({'response': 'Error: Invalid file format. Use JPG, PNG, or PDF.'})
        elif 'query' in request.form and request.form['query'].strip():
            query = request.form['query'].strip()
            response = process_text_query(query)
            return jsonify({'response': response})
        else:
            return jsonify({'response': 'Error: No query or valid file provided.'})
    except Exception as e:
        return jsonify({'response': f'Error: {str(e)}'})

if __name__ == "__main__":
    app.run(debug=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
