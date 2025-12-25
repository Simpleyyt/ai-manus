"""
Enhanced File Processing Utilities for Excel, CSV, and PDF files.
Provides data analysis capabilities using pandas and PDF text extraction with pdfplumber.
"""

from typing import Dict, Any, Optional, List
import io
import logging

logger = logging.getLogger(__name__)


class DataFileProcessor:
    """Processor for Excel and CSV files with pandas-powered analysis"""
    
    @staticmethod
    def process_excel_csv(
        file_content: bytes,
        file_extension: str,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process Excel or CSV file and optionally execute analysis queries.
        
        Args:
            file_content: Raw file bytes
            file_extension: '.xlsx', '.xls', or '.csv'
            query: Optional analysis query (e.g., "summarize column C", "calculate average")
            
        Returns:
            Dict with data summary and query results
        """
        try:
            import pandas as pd
            
            # Read file based on extension
            file_io = io.BytesIO(file_content)
            
            if file_extension.lower() in ['.xlsx', '.xls']:
                # Read Excel file
                df = pd.read_excel(file_io)
            elif file_extension.lower() == '.csv':
                # Read CSV file
                df = pd.read_csv(file_io)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file extension: {file_extension}"
                }
            
            result = {
                "success": True,
                "summary": {
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": df.columns.tolist(),
                    "dtypes": df.dtypes.astype(str).to_dict(),
                },
                "preview": df.head(10).to_dict(orient='records'),
                "statistics": {}
            }
            
            # Add statistics for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                stats_df = df[numeric_cols].describe()
                result["statistics"] = stats_df.to_dict()
            
            # Execute query if provided
            if query:
                result["query_result"] = DataFileProcessor._execute_pandas_query(df, query)
            
            return result
            
        except ImportError:
            return {
                "success": False,
                "error": "pandas library not installed. Install with: pip install pandas openpyxl"
            }
        except Exception as e:
            logger.error(f"Failed to process Excel/CSV file: {e}")
            return {
                "success": False,
                "error": f"Failed to process file: {str(e)}"
            }
    
    @staticmethod
    def _execute_pandas_query(df, query: str) -> Dict[str, Any]:
        """
        Execute natural language-style queries on DataFrame.
        
        Args:
            df: pandas DataFrame
            query: Query string
            
        Returns:
            Query results
        """
        import pandas as pd
        
        query_lower = query.lower()
        result = {"query": query, "result": None, "error": None}
        
        try:
            # Handle common query patterns
            if "average" in query_lower or "mean" in query_lower:
                # Extract column name - use longest match to avoid substring ambiguity
                matched_col = None
                max_length = 0
                for col in df.columns:
                    if col.lower() in query_lower and len(col) > max_length:
                        matched_col = col
                        max_length = len(col)
                
                if matched_col:
                    if pd.api.types.is_numeric_dtype(df[matched_col]):
                        result["result"] = f"Average of '{matched_col}': {df[matched_col].mean():.2f}"
                    else:
                        result["error"] = f"Column '{matched_col}' is not numeric"
                else:
                    result["error"] = "No matching column found in the query"
                        
            elif "sum" in query_lower or "total" in query_lower:
                # Extract column name - use longest match to avoid substring ambiguity
                matched_col = None
                max_length = 0
                for col in df.columns:
                    if col.lower() in query_lower and len(col) > max_length:
                        matched_col = col
                        max_length = len(col)
                
                if matched_col:
                    if pd.api.types.is_numeric_dtype(df[matched_col]):
                        result["result"] = f"Sum of '{matched_col}': {df[matched_col].sum():.2f}"
                    else:
                        result["error"] = f"Column '{matched_col}' is not numeric"
                else:
                    result["error"] = "No matching column found in the query"
                        
            elif "count" in query_lower:
                # Extract column name - use longest match to avoid substring ambiguity
                matched_col = None
                max_length = 0
                for col in df.columns:
                    if col.lower() in query_lower and len(col) > max_length:
                        matched_col = col
                        max_length = len(col)
                
                if matched_col:
                    result["result"] = f"Count of '{matched_col}': {df[matched_col].count()}"
                else:
                    result["error"] = "No matching column found in the query"
                        
            elif "max" in query_lower or "maximum" in query_lower:
                # Extract column name - use longest match to avoid substring ambiguity
                matched_col = None
                max_length = 0
                for col in df.columns:
                    if col.lower() in query_lower and len(col) > max_length:
                        matched_col = col
                        max_length = len(col)
                
                if matched_col:
                    if pd.api.types.is_numeric_dtype(df[matched_col]):
                        result["result"] = f"Maximum of '{matched_col}': {df[matched_col].max():.2f}"
                    else:
                        result["error"] = f"Column '{matched_col}' is not numeric"
                else:
                    result["error"] = "No matching column found in the query"
                        
            elif "min" in query_lower or "minimum" in query_lower:
                # Extract column name - use longest match to avoid substring ambiguity
                matched_col = None
                max_length = 0
                for col in df.columns:
                    if col.lower() in query_lower and len(col) > max_length:
                        matched_col = col
                        max_length = len(col)
                
                if matched_col:
                    if pd.api.types.is_numeric_dtype(df[matched_col]):
                        result["result"] = f"Minimum of '{matched_col}': {df[matched_col].min():.2f}"
                    else:
                        result["error"] = f"Column '{matched_col}' is not numeric"
                else:
                    result["error"] = "No matching column found in the query"
                        
            elif "unique" in query_lower or "distinct" in query_lower:
                # Extract column name - use longest match to avoid substring ambiguity
                matched_col = None
                max_length = 0
                for col in df.columns:
                    if col.lower() in query_lower and len(col) > max_length:
                        matched_col = col
                        max_length = len(col)
                
                if matched_col:
                    unique_values = df[matched_col].unique().tolist()
                    result["result"] = f"Unique values in '{matched_col}': {unique_values[:20]}"  # Limit to 20
                else:
                    result["error"] = "No matching column found in the query"
                        
            else:
                result["error"] = "Query pattern not recognized. Supported: average, sum, count, max, min, unique"
                
        except Exception as e:
            result["error"] = f"Query execution failed: {str(e)}"
        
        return result


class PDFProcessor:
    """Processor for PDF files with text and table extraction"""
    
    @staticmethod
    def process_pdf(
        file_content: bytes,
        extract_tables: bool = True,
        page_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Extract text and tables from PDF file.
        
        Args:
            file_content: Raw PDF file bytes
            extract_tables: Whether to extract tables
            page_range: Optional tuple (start_page, end_page) for partial extraction
            
        Returns:
            Dict with extracted text and tables
        """
        try:
            import pdfplumber
            
            file_io = io.BytesIO(file_content)
            
            result = {
                "success": True,
                "pages": [],
                "total_pages": 0,
                "text": "",
                "tables": []
            }
            
            with pdfplumber.open(file_io) as pdf:
                result["total_pages"] = len(pdf.pages)
                
                # Determine page range
                # Handle partial page_range: (start, None) or (start, end)
                if page_range:
                    start_page = page_range[0] if page_range[0] is not None else 0
                    end_page = page_range[1] if page_range[1] is not None else len(pdf.pages)
                else:
                    start_page = 0
                    end_page = len(pdf.pages)
                
                end_page = min(end_page, len(pdf.pages))
                
                for page_num in range(start_page, end_page):
                    page = pdf.pages[page_num]
                    
                    page_data = {
                        "page_number": page_num + 1,
                        "text": "",
                        "tables": []
                    }
                    
                    # Extract text
                    text = page.extract_text()
                    if text:
                        page_data["text"] = text
                        result["text"] += f"\n\n--- Page {page_num + 1} ---\n\n{text}"
                    
                    # Extract tables if requested
                    if extract_tables:
                        tables = page.extract_tables()
                        if tables:
                            for table_idx, table in enumerate(tables):
                                page_data["tables"].append({
                                    "table_index": table_idx + 1,
                                    "rows": len(table),
                                    "columns": len(table[0]) if table else 0,
                                    "data": table
                                })
                                result["tables"].append({
                                    "page": page_num + 1,
                                    "table_index": table_idx + 1,
                                    "data": table
                                })
                    
                    result["pages"].append(page_data)
            
            return result
            
        except ImportError:
            return {
                "success": False,
                "error": "pdfplumber library not installed. Install with: pip install pdfplumber"
            }
        except Exception as e:
            logger.error(f"Failed to process PDF file: {e}")
            return {
                "success": False,
                "error": f"Failed to process PDF: {str(e)}"
            }
