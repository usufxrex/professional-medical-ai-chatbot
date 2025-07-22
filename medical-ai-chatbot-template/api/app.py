from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import csv
import json
import requests
from werkzeug.utils import secure_filename
from pathlib import Path
import uuid
from datetime import datetime

app = Flask(__name__, 
            template_folder='../ui/templates',
            static_folder='../ui/static')

app.config['SECRET_KEY'] = 'mediai-professional-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

CORS(app)

# Create upload directory
os.makedirs('uploads', exist_ok=True)

# Get API key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Global storage for chat sessions and documents
chat_sessions = {}
uploaded_documents = {}
lung_cancer_dataset = []

# Load dataset
def load_dataset():
    global lung_cancer_dataset
    try:
        data_path = Path('diseases/lung_cancer/data.csv')
        if data_path.exists():
            with open(data_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                lung_cancer_dataset = list(reader)
            print(f"✅ Loaded {len(lung_cancer_dataset)} medical records")
        else:
            print("❌ Dataset not found - using sample data")
            lung_cancer_dataset = []
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        lung_cancer_dataset = []

# Load dataset on startup
load_dataset()

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        import PyPDF2
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except ImportError:
        return "PDF processing requires PyPDF2. Install with: pip install PyPDF2"
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def read_text_file(file_path):
    """Read plain text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def call_gemini_ai(prompt, max_tokens=1500):
    """Enhanced Gemini AI call with better error handling"""
    if not GEMINI_API_KEY:
        return None
    
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        headers = {
            'Content-Type': 'application/json',
            'x-goog-api-key': GEMINI_API_KEY
        }
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": max_tokens,
                "topP": 0.8,
                "topK": 40
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
            ]
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                candidate = data['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    return candidate['content']['parts'][0]['text']
        else:
            print(f"Gemini API error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"AI API error: {e}")
    
    return None

def analyze_dataset_query(query):
    """Analyze query against the medical dataset"""
    if not lung_cancer_dataset:
        return "Medical dataset not available. Please ensure the dataset is properly loaded."
    
    query_lower = query.lower()
    total_records = len(lung_cancer_dataset)
    
    try:
        # Smoking analysis
        if 'smoking' in query_lower or 'smoke' in query_lower:
            smokers = sum(1 for row in lung_cancer_dataset if row.get('SMOKING') == '1')
            cancer_cases = [row for row in lung_cancer_dataset if row.get('LUNG_CANCER') == 'YES']
            smokers_with_cancer = sum(1 for row in cancer_cases if row.get('SMOKING') == '1')
            total_cancer = len(cancer_cases)
            
            result = f"""**SMOKING ANALYSIS FROM MEDICAL DATASET**

📊 **Dataset Overview:**
• Total patients analyzed: {total_records:,}
• Patients with smoking history: {smokers:,} ({(smokers/total_records*100):.1f}%)
• Patients without smoking history: {total_records-smokers:,}

🎯 **Cancer Correlation:**
• Total cancer cases: {total_cancer:,}
• Cancer cases with smoking history: {smokers_with_cancer:,}
• **{(smokers_with_cancer/total_cancer*100):.1f}% of cancer patients have smoking history**

💡 **Key Insight:** Smoking appears in {(smokers_with_cancer/total_cancer*100):.1f}% of cancer cases in our dataset."""
            
            return result
        
        # Age analysis
        elif 'age' in query_lower:
            ages = [int(row.get('AGE', 0)) for row in lung_cancer_dataset if row.get('AGE', '').isdigit()]
            cancer_ages = [int(row.get('AGE', 0)) for row in lung_cancer_dataset if row.get('LUNG_CANCER') == 'YES' and row.get('AGE', '').isdigit()]
            
            if ages and cancer_ages:
                avg_age = sum(ages) / len(ages)
                avg_cancer_age = sum(cancer_ages) / len(cancer_ages)
                
                return f"""**AGE ANALYSIS FROM MEDICAL DATASET**

📊 **Age Demographics:**
• Average age of all patients: {avg_age:.1f} years
• Age range: {min(ages)} - {max(ages)} years
• Median age: {sorted(ages)[len(ages)//2]} years

🎯 **Cancer Age Analysis:**
• Average age of cancer patients: {avg_cancer_age:.1f} years
• Cancer cases analyzed: {len(cancer_ages):,}

💡 **Key Insight:** Cancer patients are on average {abs(avg_cancer_age-avg_age):.1f} years {'older' if avg_cancer_age > avg_age else 'younger'} than the general patient population."""
        
        # Statistics
        elif 'statistic' in query_lower or 'overview' in query_lower or 'summary' in query_lower:
            cancer_cases = sum(1 for row in lung_cancer_dataset if row.get('LUNG_CANCER') == 'YES')
            male_count = sum(1 for row in lung_cancer_dataset if row.get('GENDER') == 'M')
            female_count = sum(1 for row in lung_cancer_dataset if row.get('GENDER') == 'F')
            
            return f"""**MEDICAL DATASET STATISTICS**

📊 **Dataset Overview:**
• Total medical records: {total_records:,}
• Cancer cases: {cancer_cases:,} ({(cancer_cases/total_records*100):.1f}%)
• Non-cancer cases: {total_records-cancer_cases:,} ({((total_records-cancer_cases)/total_records*100):.1f}%)

👥 **Demographics:**
• Male patients: {male_count:,} ({(male_count/total_records*100):.1f}%)
• Female patients: {female_count:,} ({(female_count/total_records*100):.1f}%)

🔬 **Data Quality:**
• Complete records analyzed
• Multiple clinical features tracked
• Comprehensive symptom data available"""
        
        else:
            # General dataset info
            cancer_cases = sum(1 for row in lung_cancer_dataset if row.get('LUNG_CANCER') == 'YES')
            return f"""**MEDICAL DATASET AVAILABLE**

📊 I have access to {total_records:,} medical records including {cancer_cases:,} cancer cases.

🔍 **You can ask me about:**
• Smoking patterns and cancer correlation
• Age demographics and cancer risk
• Gender distribution in cancer cases
• Symptom prevalence and analysis
• Statistical overviews and insights

💡 **Try asking:** "How does smoking affect cancer risk?" or "What are the age patterns in cancer patients?\""""
    
    except Exception as e:
        return f"Error analyzing dataset: {str(e)}"

def get_chat_session(chat_id):
    """Get or create chat session"""
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = {
            'id': chat_id,
            'created': datetime.now().isoformat(),
            'documents': [],
            'message_count': 0
        }
    return chat_sessions[chat_id]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        chat_id = data.get('chat_id')
        uploaded_docs = data.get('uploaded_documents', [])
        
        if not user_message:
            return jsonify({'error': 'Message required'}), 400
        
        # Get chat session
        session = get_chat_session(chat_id) if chat_id else {'documents': []}
        session['message_count'] = session.get('message_count', 0) + 1
        
        # Determine if this is a document-specific query
        doc_keywords = ['document', 'pdf', 'file', 'uploaded', 'summarize', 'summary', 
                       'mr.', 'patient', 'diagnosis', 'lab', 'result', 'report', 'findings']
        
        is_document_query = any(keyword in user_message.lower() for keyword in doc_keywords)
        
        # Check if we have uploaded documents in this session
        available_documents = []
        for doc_id in session.get('documents', []):
            if doc_id in uploaded_documents:
                available_documents.append(uploaded_documents[doc_id])
        
        # Also check for documents passed in request
        for doc in uploaded_docs:
            if doc.get('content'):
                available_documents.append(doc)
        
        response_text = ""
        
        if is_document_query and available_documents:
            # Document-specific query
            if len(available_documents) == 1:
                doc = available_documents[0]
                prompt = f"""You are a professional medical AI assistant analyzing a medical document.

DOCUMENT DETAILS:
- File: {doc.get('name', 'Medical Document')}
- Type: {doc.get('type', 'Unknown')}
- Upload Time: {doc.get('uploadTime', 'Recent')}

DOCUMENT CONTENT:
{doc.get('content', '')[:3000]}

USER QUESTION: {user_message}

INSTRUCTIONS:
1. Provide a professional medical analysis
2. Focus specifically on what the user asked
3. Extract relevant medical information from the document
4. If asked for summary, provide comprehensive overview
5. If asked about specific findings, focus on those
6. Always recommend consulting healthcare professionals for interpretation
7. Use clear, professional medical language
8. Structure your response with clear headings and bullet points

Provide a detailed, professional response:"""
            
            else:
                # Multiple documents
                docs_content = ""
                for i, doc in enumerate(available_documents, 1):
                    docs_content += f"\n--- DOCUMENT {i}: {doc.get('name', f'Document {i}')} ---\n"
                    docs_content += doc.get('content', '')[:1500] + "\n"
                
                prompt = f"""You are a professional medical AI assistant analyzing multiple medical documents.

AVAILABLE DOCUMENTS ({len(available_documents)} files):
{docs_content}

USER QUESTION: {user_message}

INSTRUCTIONS:
1. Analyze all relevant documents
2. Cross-reference information when applicable
3. Provide comprehensive analysis
4. If asked about specific document, focus on that one
5. If general question, synthesize information from all documents
6. Use professional medical language
7. Structure response clearly

Provide a detailed analysis:"""
            
            ai_response = call_gemini_ai(prompt, max_tokens=2000)
            
            if ai_response:
                response_text = ai_response
            else:
                response_text = f"""**Document Analysis**

I've processed your uploaded document(s) but AI analysis is currently unavailable.

**Available Documents:**
{chr(10).join([f"• {doc.get('name', 'Document')} ({doc.get('type', 'Unknown type')})" for doc in available_documents])}

Please ensure your API configuration is correct for full AI-powered analysis."""
        
        else:
            # Dataset query or general medical question
            dataset_analysis = analyze_dataset_query(user_message)
            
            if GEMINI_API_KEY:
                prompt = f"""You are a professional medical AI assistant with access to comprehensive medical datasets.

MEDICAL DATASET ANALYSIS:
{dataset_analysis}

USER QUESTION: {user_message}

INSTRUCTIONS:
1. Provide evidence-based medical information using the dataset insights
2. Use professional medical language
3. Structure your response clearly with headings and bullet points
4. Include relevant statistics from the dataset
5. Always recommend consulting healthcare professionals
6. Be thorough but concise
7. Focus on the specific question asked

Provide a comprehensive medical response:"""

                ai_response = call_gemini_ai(prompt)
                response_text = ai_response if ai_response else dataset_analysis
            else:
                response_text = dataset_analysis
        
        return jsonify({
            'ai_response': response_text,
            'metadata': {
                'dataset_records': len(lung_cancer_dataset),
                'documents_available': len(available_documents),
                'message_count': session.get('message_count', 0),
                'ai_model': 'Gemini 1.5 Flash' if GEMINI_API_KEY else 'Dataset Analysis'
            }
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            'ai_response': 'I apologize, but I encountered an error processing your request. Please try again.',
            'metadata': {'error': True, 'error_details': str(e)}
        }), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'error': f'File type not supported. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{filename}")
        file.save(file_path)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        file_ext = filename.rsplit('.', 1)[1].lower()
        
        # Extract text based on file type
        extracted_text = ""
        
        try:
            if file_ext == 'pdf':
                extracted_text = extract_text_from_pdf(file_path)
            elif file_ext == 'txt':
                extracted_text = read_text_file(file_path)
            elif file_ext in ['png', 'jpg', 'jpeg', 'gif']:
                extracted_text = f"Image file uploaded: {filename}. Text extraction from images requires OCR processing."
            elif file_ext == 'csv':
                extracted_text = f"CSV dataset uploaded: {filename}. This appears to be a medical dataset file."
            else:
                extracted_text = f"File uploaded: {filename}. Content extraction not available for this file type."
            
            # Store document
            doc_data = {
                'id': file_id,
                'name': filename,
                'content': extracted_text,
                'type': file_ext.upper(),
                'size': f"{file_size / 1024:.1f} KB",
                'uploadTime': datetime.now().isoformat(),
                'processed': True
            }
            
            uploaded_documents[file_id] = doc_data
            
            # Generate analysis
            analysis_text = "Document uploaded and processed successfully."
            
            if 'patient' in extracted_text.lower():
                analysis_text += " This appears to be a patient medical document."
            if 'diagnosis' in extracted_text.lower():
                analysis_text += " The document contains diagnostic information."
            if 'test' in extracted_text.lower() or 'result' in extracted_text.lower():
                analysis_text += " Test results are present in the document."
            
        except Exception as e:
            extracted_text = f"Error processing file: {str(e)}"
            analysis_text = "File uploaded but processing encountered an error."
        
        finally:
            # Clean up uploaded file
            try:
                os.remove(file_path)
            except:
                pass
        
        return jsonify({
            'success': True,
            'file_info': {
                'id': file_id,
                'filename': filename,
                'size': f"{file_size / 1024:.1f} KB",
                'type': file_ext.upper()
            },
            'extracted_text': extracted_text,
            'analysis': {
                'document_analysis': analysis_text
            }
        })
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'total_records': len(lung_cancer_dataset),
        'ai_available': bool(GEMINI_API_KEY),
        'upload_enabled': True,
        'active_sessions': len(chat_sessions),
        'uploaded_documents': len(uploaded_documents),
        'supported_formats': list(ALLOWED_EXTENSIONS)
    })

@app.route('/api/system/status')
def system_status():
    return jsonify({
        'dataset': {
            'loaded': bool(lung_cancer_dataset),
            'records': len(lung_cancer_dataset),
            'source': 'diseases/lung_cancer/data.csv'
        },
        'ai': {
            'available': bool(GEMINI_API_KEY),
            'provider': 'Google Gemini',
            'model': 'gemini-1.5-flash'
        },
        'storage': {
            'active_chats': len(chat_sessions),
            'documents': len(uploaded_documents)
        }
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🏥 PROFESSIONAL MEDICAL AI CHATBOT")
    print("="*60)
    print(f"🌐 URL: http://localhost:5000")
    print(f"📊 Medical Records: {len(lung_cancer_dataset):,} loaded")
    print(f"🤖 AI Status: {'✅ Available (Gemini)' if GEMINI_API_KEY else '❌ No API Key'}")
    print(f"📁 File Upload: ✅ Multiple formats supported")
    print(f"💬 Chat System: ✅ Multi-session with history")
    print(f"📄 Document Analysis: ✅ AI-powered processing")
    print("="*60)
    print("Features: Professional UI, Document Management, Dataset Analysis")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)