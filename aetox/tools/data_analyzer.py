import os
import pandas as pd
from pypdf import PdfReader
from typing import Dict, Any, Optional

class DataAnalyzerTool:
    """
    Tools for analyzing documents (PDF) and structured data (CSV, Excel).
    """
    def __init__(self, allowed_paths: Optional[list] = None):
        self.allowed_paths = allowed_paths or []

    def read_pdf(self, path: str) -> str:
        """Extracts text from a PDF file."""
        if not os.path.exists(path):
            return f"Error: File {path} not found."
        
        try:
            reader = PdfReader(path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            if not text.strip():
                return "Warning: PDF seems to be empty or contains only images."
            
            return text[:5000] # Limit to first 5000 chars for LLM context
        except Exception as e:
            return f"Error reading PDF: {str(e)}"

    def analyze_table(self, path: str) -> str:
        """Analyzes CSV or Excel files and provides a summary."""
        if not os.path.exists(path):
            return f"Error: File {path} not found."
        
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".csv":
                df = pd.read_csv(path)
            elif ext in [".xlsx", ".xls"]:
                df = pd.read_excel(path)
            else:
                return f"Error: Unsupported file format {ext}"

            summary = f"File: {os.path.basename(path)}\n"
            summary += f"Rows: {len(df)}, Columns: {len(df.columns)}\n"
            summary += f"Columns: {', '.join(df.columns.tolist())}\n\n"
            summary += "Data Preview (First 3 rows):\n"
            summary += df.head(3).to_string()
            
            return summary
        except Exception as e:
            return f"Error analyzing table: {str(e)}"

    def get_column_stats(self, path: str, column_name: str) -> str:
        """Provides statistics for a specific column in a table."""
        try:
            ext = os.path.splitext(path)[1].lower()
            df = pd.read_csv(path) if ext == ".csv" else pd.read_excel(path)
            
            if column_name not in df.columns:
                return f"Error: Column '{column_name}' not found."
            
            stats = df[column_name].describe()
            return f"Stats for {column_name}:\n{stats.to_string()}"
        except Exception as e:
            return f"Error: {str(e)}"
