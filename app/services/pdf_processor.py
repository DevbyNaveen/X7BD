"""
PDF Processing Service with OCR and AI Categorization

Production-grade PDF extraction, OCR, and intelligent categorization.
"""

from typing import List, Dict, Any, Optional, BinaryIO
from datetime import datetime
import os
import io
import base64

import PyPDF2
import pdfplumber
from PIL import Image
import pytesseract
from openai import OpenAI

import logging

logger = logging.getLogger(__name__)


class PDFProcessorService:
    """
    Production-grade PDF processing service
    
    Features:
    - Text extraction from PDFs
    - OCR for scanned documents
    - Image extraction
    - AI-powered categorization
    - Menu item detection
    - Price extraction
    """
    
    def __init__(self):
        """Initialize PDF processor"""
        self.openai_client = None
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self._initialized = False
    
    def initialize(self):
        """Initialize OpenAI client"""
        if self._initialized:
            return
        
        try:
            if self.openai_api_key:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                logger.info("PDF processor initialized with OpenAI")
            else:
                logger.warning("OpenAI API key not set, AI categorization disabled")
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize PDF processor: {e}")
            raise
    
    async def process_pdf(
        self,
        file_path: str,
        business_id: str,
        extract_images: bool = True,
        use_ocr: bool = True
    ) -> Dict[str, Any]:
        """
        Process PDF file completely
        
        Args:
            file_path: Path to PDF file
            business_id: Business identifier
            extract_images: Whether to extract images
            use_ocr: Whether to use OCR for scanned pages
            
        Returns:
            Dictionary with extracted content and metadata
        """
        if not self._initialized:
            self.initialize()
        
        try:
            logger.info(f"Processing PDF: {file_path}")
            
            # Extract text
            text_content = await self.extract_text(file_path, use_ocr)
            
            # Extract images
            images = []
            if extract_images:
                images = await self.extract_images(file_path)
            
            # Categorize content using AI
            categorization = await self.categorize_content(text_content, business_id)
            
            # Extract menu items if it's a menu
            menu_items = []
            if categorization.get("category") == "menu":
                menu_items = await self.extract_menu_items(text_content)
            
            return {
                "file_path": file_path,
                "business_id": business_id,
                "text_content": text_content,
                "images": images,
                "categorization": categorization,
                "menu_items": menu_items,
                "processed_at": datetime.utcnow().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}", exc_info=True)
            return {
                "file_path": file_path,
                "status": "error",
                "error": str(e)
            }
    
    async def extract_text(
        self,
        file_path: str,
        use_ocr: bool = True
    ) -> str:
        """
        Extract text from PDF
        
        Uses PyPDF2 for text-based PDFs and OCR for scanned documents
        """
        try:
            text_content = []
            
            # Try pdfplumber first (better text extraction)
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    
                    if page_text and page_text.strip():
                        text_content.append(f"--- Page {page_num + 1} ---\n{page_text}")
                    elif use_ocr:
                        # If no text found, try OCR
                        logger.info(f"Using OCR for page {page_num + 1}")
                        ocr_text = await self.ocr_page(page)
                        if ocr_text:
                            text_content.append(f"--- Page {page_num + 1} (OCR) ---\n{ocr_text}")
            
            return "\n\n".join(text_content)
            
        except Exception as e:
            logger.error(f"Error extracting text: {e}", exc_info=True)
            raise
    
    async def ocr_page(self, page) -> str:
        """
        Perform OCR on a PDF page
        
        Args:
            page: pdfplumber page object
            
        Returns:
            Extracted text from OCR
        """
        try:
            # Convert page to image
            img = page.to_image(resolution=300)
            pil_img = img.original
            
            # Perform OCR
            text = pytesseract.image_to_string(pil_img)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error performing OCR: {e}")
            return ""
    
    async def extract_images(
        self,
        file_path: str
    ) -> List[Dict[str, Any]]:
        """
        Extract images from PDF
        
        Returns:
            List of images with metadata
        """
        try:
            images = []
            
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract images from page
                    if hasattr(page, 'images'):
                        for img_idx, img in enumerate(page.images):
                            images.append({
                                "page": page_num + 1,
                                "index": img_idx,
                                "x0": img.get("x0"),
                                "y0": img.get("y0"),
                                "width": img.get("width"),
                                "height": img.get("height"),
                                "metadata": {
                                    "extracted_at": datetime.utcnow().isoformat()
                                }
                            })
            
            logger.info(f"Extracted {len(images)} images from PDF")
            return images
            
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            return []
    
    async def categorize_content(
        self,
        text_content: str,
        business_id: str
    ) -> Dict[str, Any]:
        """
        Categorize PDF content using AI
        
        Determines if it's a menu, invoice, report, etc.
        """
        if not self.openai_client:
            return {
                "category": "unknown",
                "confidence": 0.0,
                "message": "AI categorization not available"
            }
        
        try:
            logger.info("Categorizing content with AI")
            
            prompt = f"""
            Analyze the following document content and categorize it.
            
            Possible categories:
            - menu: Restaurant/cafe menu with food items and prices
            - invoice: Bill or invoice
            - report: Business report or analytics
            - marketing: Marketing material or flyer
            - other: Other document type
            
            Also extract key information like:
            - Document title
            - Main sections
            - Any prices or monetary values
            
            Content:
            {text_content[:2000]}
            
            Respond in JSON format:
            {{
                "category": "menu|invoice|report|marketing|other",
                "confidence": 0.0-1.0,
                "title": "Document title",
                "sections": ["section1", "section2"],
                "has_prices": true/false,
                "summary": "Brief summary"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a document analysis expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            logger.info(f"Categorization result: {result.get('category')} (confidence: {result.get('confidence')})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error categorizing content: {e}", exc_info=True)
            return {
                "category": "unknown",
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def extract_menu_items(
        self,
        text_content: str
    ) -> List[Dict[str, Any]]:
        """
        Extract menu items from text using AI
        
        Identifies item names, descriptions, and prices
        """
        if not self.openai_client:
            return []
        
        try:
            logger.info("Extracting menu items with AI")
            
            prompt = f"""
            Extract menu items from the following menu content.
            
            For each item, extract:
            - name: Item name
            - description: Item description (if available)
            - price: Price (if available)
            - category: Category (appetizer, main, dessert, beverage, etc.)
            
            Content:
            {text_content[:3000]}
            
            Respond in JSON format:
            {{
                "items": [
                    {{
                        "name": "Item name",
                        "description": "Description",
                        "price": 12.99,
                        "category": "main"
                    }}
                ]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a menu extraction expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            items = result.get("items", [])
            logger.info(f"Extracted {len(items)} menu items")
            
            return items
            
        except Exception as e:
            logger.error(f"Error extracting menu items: {e}", exc_info=True)
            return []
    
    async def process_menu_pdf(
        self,
        file_path: str,
        business_id: str
    ) -> Dict[str, Any]:
        """
        Specialized processing for menu PDFs
        
        Extracts menu structure, categories, items, and prices
        """
        try:
            logger.info(f"Processing menu PDF for business {business_id}")
            
            # Extract text
            text_content = await self.extract_text(file_path)
            
            # Extract menu items
            menu_items = await self.extract_menu_items(text_content)
            
            # Group items by category
            categories = {}
            for item in menu_items:
                category = item.get("category", "other")
                if category not in categories:
                    categories[category] = []
                categories[category].append(item)
            
            return {
                "business_id": business_id,
                "total_items": len(menu_items),
                "categories": categories,
                "menu_items": menu_items,
                "processed_at": datetime.utcnow().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error processing menu PDF: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }


# Global PDF processor instance
pdf_processor = PDFProcessorService()
