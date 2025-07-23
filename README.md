**SENTIMENTAL ANALYSIS DASHBOARD**

A user-friendly web app for analyzing the sentiment of text data using natural language processing (NLP) and visual insights — built with **Streamlit**, **TextBlob**, **Matplotlib**, and **FPDF**.

---

Features

Analyze direct input text or uploaded `.txt` files  
Detect **Positive**, **Negative**, or **Neutral** sentiment per sentence  
Show **confidence scores** and **subjectivity**  
Generate:
- Pie charts for sentiment distribution  
- Polarity histograms and line graphs  
- Word clouds  
Extract sentiment-bearing **keywords**  
Highlight top 3 most positive & negative sentences
Export results as `.CSV`, `.JSON`, or professional `.PDF` reports  
Compare multiple texts visually and statistically  

---

Live Demo
  
`https://your-streamlit-app-link`

---

Installation

1. **Clone the repo:**

```
git clone https://github.com/yourusername/sentiment-analysis-dashboard.git
cd sentiment-analysis-dashboard
Create virtual environment (optional but recommended):


python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:


pip install -r requirements.txt
Run the Streamlit app:


streamlit run app.py

Dependencies
streamlit

textblob

pandas

matplotlib

wordcloud

fpdf

Install them all with:


pip install -r requirements.txt
You may also need to download NLTK corpora for TextBlob (first-time use only):


python -m textblob.download_corpora

Project Structure

sentiment-analysis-dashboard/
│
├── app.py                   # Main Streamlit app
├── README.md                # Project documentation
├── requirements.txt         # All dependencies
└── sample_texts/            # (Optional) Folder to store sample .txt files

Example Use Case
Upload multiple .txt files or paste text into the sidebar.

The app will analyze each sentence.

Get summary stats, charts, trends, and sentiment keywords.

Export your results to CSV, JSON, or PDF.

To-Do / Enhancements
 Support for more advanced NLP (e.g. spaCy, Vader)

 Theme customization

 Add dashboard login or session-saving

Authors

Ondela Citywayo
Sinesipho Sibulo
Segai Mampshika
Vhuvwhano Mawela Masalesa
Mthunzi Malebadi

Built with using Python + Streamlit

License
This project is licensed under the MIT License — feel free to use, share, and build upon it!



---
