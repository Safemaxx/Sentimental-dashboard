import streamlit as st
from textblob import TextBlob
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import json
from fpdf import FPDF
import io

# ---- PAGE CONFIG ----
st.set_page_config(page_title="AURA Sentiment Analysis Dashboard", layout="wide")

# ---- TITLE ----
st.title("AURA Sentiment Analysis Dashboard")
st.markdown("Analyze the sentiment of your text data (Positive, Negative, Neutral)")

# ---- FUNCTIONS ----
def analyze_sentiment(text):
    """
    Analyzes the sentiment of a given text using TextBlob.
    Returns polarity, sentiment label, confidence (absolute polarity), and subjectivity.
    """
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity

    if polarity > 0:
        sentiment = 'Positive'
    elif polarity < 0:
        sentiment = 'Negative'
    else:
        sentiment = 'Neutral'

    # Confidence can be seen as the absolute value of polarity: closer to 1 or -1 means higher confidence.
    confidence = abs(polarity)
    return polarity, sentiment, confidence, subjectivity

def generate_wordcloud(text):
    """Generates a word cloud from the given text."""
    # Ensure text is not empty before generating word cloud
    if not text.strip():
        return None
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    return fig

def get_sentiment_keywords(text):
    """
    A basic function to extract potential sentiment-bearing keywords.
    This is a simplified approach, focusing on adjectives and nouns with some polarity.
    """
    blob = TextBlob(text)
    keywords = []
    for word, tag in blob.tags:
        # Consider adjectives (JJ), nouns (NN), verbs (VB) as potential keywords
        if tag.startswith('JJ') or tag.startswith('NN') or tag.startswith('VB'):
            word_blob = TextBlob(word)
            # Only include words that have some polarity or are significant nouns/verbs
            if abs(word_blob.sentiment.polarity) > 0.1 or tag.startswith('NN') or tag.startswith('VB'):
                keywords.append(f"{word} (Polarity: {word_blob.sentiment.polarity:.2f})")
    return list(set(keywords)) # Return unique keywords

def create_pdf_report(df, overall_summary, text_content):
    """Creates a PDF report from the sentiment analysis results."""
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Sentiment Analysis Report", 0, 1, "C")
    pdf.ln(10)

    # Overall Summary
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Overall Sentiment Summary:", 0, 1)
    pdf.set_font("Arial", "", 10)
    for key, value in overall_summary.items():
        pdf.cell(0, 7, f"{key}: {value}", 0, 1)
    pdf.ln(5)

    # Detailed Sentences
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Detailed Sentence Analysis:", 0, 1)
    pdf.set_font("Arial", "", 8) # Smaller font for detailed table

    # Table Header
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(100, 7, "Sentence", 1, 0, 'C', 1)
    pdf.cell(25, 7, "Polarity", 1, 0, 'C', 1)
    pdf.cell(25, 7, "Sentiment", 1, 0, 'C', 1)
    pdf.cell(25, 7, "Confidence", 1, 1, 'C', 1)

    # Table Rows
    for index, row in df.iterrows():
        # Store initial Y position for the row
        start_y = pdf.get_y()

        # Render the sentence multi_cell
        # The last argument (False) means it won't print the border, we'll draw it manually later
        # We also don't need to capture the return value as it's not a string to split
        pdf.multi_cell(100, 5, row['Sentence'], 0, 'L', False)

        # Calculate the height of the multi_cell
        end_y = pdf.get_y()
        cell_height = end_y - start_y

        # Draw borders for the sentence cell
        pdf.rect(pdf.get_x() - 100, start_y, 100, cell_height)

        # Move back to the right of the sentence cell to draw other cells in the same row
        pdf.set_xy(pdf.get_x() + 0, start_y) # Adjust X to be at the start of the next column

        # Render other cells in the row with the calculated height
        pdf.cell(25, cell_height, f"{row['Polarity']:.2f}", 1, 0, 'C')
        pdf.cell(25, cell_height, row['Sentiment'], 1, 0, 'C')
        pdf.cell(25, cell_height, f"{row['Confidence']:.2f}", 1, 1, 'C') # 1 for new line

    pdf.ln(10)

    # Original Text (Optional, for reference)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Original Text Analyzed:", 0, 1)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 5, text_content)

    return pdf.output(dest='S').encode('latin1') # Return as bytes

# ---- SIDEBAR INPUT ----
st.sidebar.header("Enter your text or upload a file(s):")
input_option = st.sidebar.radio("Choose input method:", ("Direct Text Entry", "Upload Text File(s)"))

all_texts_to_analyze = []
text_names = []

if input_option == "Direct Text Entry":
    user_input = st.sidebar.text_area("Text Input", height=200, key="direct_text_input")
    if user_input:
        all_texts_to_analyze.append(user_input)
        text_names.append("Direct Entry Text")
else:
    uploaded_files = st.sidebar.file_uploader("Upload .txt file(s)", type=["txt"], accept_multiple_files=True)
    if uploaded_files:
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                uploaded_file_content = uploaded_file.read().decode("utf-8")
                all_texts_to_analyze.append(uploaded_file_content)
                text_names.append(uploaded_file.name)
            except Exception as e:
                st.sidebar.error(f"Error reading {uploaded_file.name}: {e}")

# ---- MAIN LOGIC ----
if not all_texts_to_analyze:
    st.info("Enter some text or upload a file(s) in the sidebar to begin sentiment analysis.")
else:
    all_dfs = []
    overall_summaries = []

    for i, current_text_content in enumerate(all_texts_to_analyze):
        current_text_name = text_names[i]
        st.header(f"Analysis for: {current_text_name}")

        if not current_text_content.strip():
            st.warning(f"No content found in '{current_text_name}'. Skipping analysis for this input.")
            continue

        # Split text into sentences for finer analysis
        sentences = current_text_content.split(".")
        results = []
        for sentence in sentences:
            if sentence.strip():
                polarity, sentiment, confidence, subjectivity = analyze_sentiment(sentence)
                results.append({
                    "Sentence": sentence.strip(),
                    "Polarity": polarity,
                    "Sentiment": sentiment,
                    "Confidence": confidence,
                    "Subjectivity": subjectivity # Add subjectivity per sentence
                })

        df = pd.DataFrame(results)
        all_dfs.append(df)

        # ---- METRICS ----
        st.subheader("Sentiment Summary")
        positive_count = (df['Sentiment'] == 'Positive').sum()
        negative_count = (df['Sentiment'] == 'Negative').sum()
        neutral_count = (df['Sentiment'] == 'Neutral').sum()
        avg_polarity = df['Polarity'].mean() if not df.empty else 0
        avg_subjectivity = df['Subjectivity'].mean() if not df.empty else 0

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Positive", f"{positive_count}")
        col2.metric("Negative", f"{negative_count}")
        col3.metric("Neutral", f"{neutral_count}")
        col4.metric("Avg. Polarity", f"{avg_polarity:.2f}")
        col5.metric("Avg. Subjectivity", f"{avg_subjectivity:.2f}")

        current_overall_summary = {
            "Text Name": current_text_name,
            "Positive Sentences": positive_count,
            "Negative Sentences": negative_count,
            "Neutral Sentences": neutral_count,
            "Average Polarity": f"{avg_polarity:.2f}",
            "Average Subjectivity": f"{avg_subjectivity:.2f}"
        }
        overall_summaries.append(current_overall_summary)

        # ---- PIE CHART ----
        st.subheader("Sentiment Distribution")
        sentiment_counts = df['Sentiment'].value_counts()
        if not sentiment_counts.empty:
            fig1, ax1 = plt.subplots()
            sentiment_counts.plot.pie(autopct='%1.1f%%', colors=['green', 'red', 'gray'], ax=ax1)
            ax1.axis('equal')
            st.pyplot(fig1)
        else:
            st.info("No sentiment data to display for the pie chart.")

        # ---- POLARITY HISTOGRAM ----
        st.subheader("Polarity Score Distribution")
        if not df.empty:
            fig2, ax2 = plt.subplots()
            df['Polarity'].hist(ax=ax2, bins=20, edgecolor='black')
            ax2.set_title("Distribution of Polarity Scores")
            ax2.set_xlabel("Polarity (-1 to 1)")
            ax2.set_ylabel("Frequency")
            st.pyplot(fig2)
        else:
            st.info("No polarity data to display for the histogram.")

        # ---- POLARITY LINE GRAPH (NEW) ----
        st.subheader("Sentiment Polarity Across Sentences")
        if not df.empty:
            fig_line, ax_line = plt.subplots(figsize=(10, 4))
            ax_line.plot(df.index, df['Polarity'], marker='o', linestyle='-', color='skyblue')
            ax_line.axhline(0, color='grey', linestyle='--', linewidth=0.8, label='Neutral Line')
            ax_line.set_title("Polarity Trend Across Sentences")
            ax_line.set_xlabel("Sentence Index")
            ax_line.set_ylabel("Polarity Score")
            ax_line.set_ylim(-1, 1) # Polarity ranges from -1 to 1
            ax_line.legend()
            st.pyplot(fig_line)
        else:
            st.info("No sentence data to display for the polarity trend.")


        # ---- WORDCLOUD ----
        st.subheader("Word Cloud")
        wordcloud_fig = generate_wordcloud(current_text_content)
        if wordcloud_fig:
            st.pyplot(wordcloud_fig)
        else:
            st.info("Not enough text to generate a word cloud.")

        # ---- KEYWORD EXTRACTION ----
        st.subheader("Potential Sentiment Keywords")
        keywords = get_sentiment_keywords(current_text_content)
        if keywords:
            st.write(", ".join(keywords))
            st.caption("Note: This is a basic keyword extraction based on TextBlob's internal scoring and part-of-speech tagging. For advanced keyword extraction, consider dedicated NLP libraries.")
        else:
            st.info("No significant keywords found or text is too short.")

        # ---- EXPLANATION FEATURES (Simple) ----
        st.subheader("Sentiment Rationale (Simple Explanation)")
        st.write(f"Overall Polarity: **{avg_polarity:.2f}** (Closer to 1 is positive, -1 is negative, 0 is neutral)")
        st.write(f"Overall Subjectivity: **{avg_subjectivity:.2f}** (Closer to 1 is subjective, 0 is objective)")

        # Highlight most positive/negative sentences
        if not df.empty:
            most_positive_sentences = df.nlargest(3, 'Polarity')
            most_negative_sentences = df.nsmallest(3, 'Polarity')

            st.markdown("---")
            st.markdown("**Top 3 Most Positive Sentences:**")
            for idx, row in most_positive_sentences.iterrows():
                st.write(f"- \"{row['Sentence']}\" (Polarity: {row['Polarity']:.2f})")

            st.markdown("**Top 3 Most Negative Sentences:**")
            for idx, row in most_negative_sentences.iterrows():
                st.write(f"- \"{row['Sentence']}\" (Polarity: {row['Polarity']:.2f})")
            st.markdown("---")


        # ---- RAW DATA ----
        st.subheader("Detailed Sentences & Sentiment")
        st.dataframe(df.reset_index(drop=True))

        # ---- EXPORT OPTIONS ----
        st.subheader("Export Results")
        col_csv, col_json, col_pdf = st.columns(3)

        # Export to CSV
        csv_data = df.to_csv(index=False).encode('utf-8')
        col_csv.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"{current_text_name.replace(' ', '_')}_sentiment.csv",
            mime="text/csv",
            key=f"csv_download_{i}"
        )

        # Export to JSON
        json_data = df.to_json(orient="records", indent=4)
        col_json.download_button(
            label="Download JSON",
            data=json_data,
            file_name=f"{current_text_name.replace(' ', '_')}_sentiment.json",
            mime="application/json",
            key=f"json_download_{i}"
        )

        # Export to PDF
        pdf_output = create_pdf_report(df, current_overall_summary, current_text_content)
        col_pdf.download_button(
            label="Download PDF",
            data=pdf_output,
            file_name=f"{current_text_name.replace(' ', '_')}_sentiment_report.pdf",
            mime="application/pdf",
            key=f"pdf_download_{i}"
        )
        st.markdown("---") # Separator for multiple analyses

    # ---- COMPARATIVE ANALYSIS (if multiple texts) ----
    if len(all_texts_to_analyze) > 1:
        st.header("Comparative Analysis Across Texts")
        comp_df = pd.DataFrame(overall_summaries)
        st.dataframe(comp_df.set_index("Text Name"))

        st.subheader("Sentiment Count Comparison")
        fig_comp, ax_comp = plt.subplots(figsize=(10, 6))
        comp_df.set_index("Text Name")[['Positive Sentences', 'Negative Sentences', 'Neutral Sentences']].plot(
            kind='bar', stacked=True, ax=ax_comp, color=['green', 'red', 'gray']
        )
        ax_comp.set_title("Sentiment Count Comparison Across Texts")
        ax_comp.set_ylabel("Number of Sentences")
        ax_comp.set_xlabel("Text Source")
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig_comp)

        st.subheader("Average Polarity Comparison")
        fig_avg_pol, ax_avg_pol = plt.subplots(figsize=(10, 4))
        comp_df.set_index("Text Name")['Average Polarity'].astype(float).plot(
            kind='bar', ax=ax_avg_pol, color='skyblue'
        )
        ax_avg_pol.axhline(0, color='grey', linestyle='--', linewidth=0.8) # Neutral line
        ax_avg_pol.set_title("Average Polarity Comparison Across Texts")
        ax_avg_pol.set_ylabel("Average Polarity")
        ax_avg_pol.set_xlabel("Text Source")
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig_avg_pol)
