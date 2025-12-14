from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title
import json
from langchain_community import

class ExtractPDF:
    def __init__(self, pdf_bytes: str = None):
        self.pdf_bytes = pdf_bytes

    def get_elements(self):

        try:
            print("-----------------------")
            elements = partition_pdf(
                filename=self.pdf_bytes,
                strategy="hi_res",
                infer_table_structure=True,
                chunking_strategy="by_title",
                include_page_breaks=True,
                add_metadata=True,
                extract_image_block_types=["table"],
                ocr_languages= "eng"
            )
            return elements


            # content = {
            #     "text": [],
            #     "tables": [],
            #     "metadata": []
            # }

            # for element in elements:
            #     element_dict = element.to_dict()
            #     element_type = element_dict.get("type", "")
            #     text = element_dict.get("text", "")
            #
            #     # Categorize by element type
            #     if element_type == "Table":
            #         content["tables"].append({
            #             "text": text,
            #             "metadata": element_dict.get("metadata", {})
            #         })
            #     elif text.strip():  # Only add non-empty text
            #         content["text"].append({
            #             "type": element_type,
            #             "text": text,
            #             "metadata": element_dict.get("metadata", {})
            #         })
            #
            #     # Combine all text into a single string
            # full_text = "\n\n".join([item["text"] for item in content["text"]])
            # return {
            #     "full_text": full_text,
            #     "structured_content": content,
            #     "total_elements": len(elements)
            # }

        except Exception as e:
            print(f"Error extracting PDF content: {str(e)}")
            return None

    def save_to_json(self, content = None):
        """Save extracted content to JSON file"""
        with open("extracted_json.json", 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)

    def chunking_elements(self, elements = None):
        if elements is None:
            elements = self.get_elements()
        chunks = chunk_by_title(
            elements=elements,
            max_characters=1500,
            new_after_n_chars=1000,
            combine_text_under_n_chars=300,
            multipage_sections=True
        )

        for i, chunk in enumerate(chunks):
            print(chunk)

if __name__ == "__main__":
    extractor = ExtractPDF(pdf_bytes=r"C:\Users\madhu\Downloads\Accord\130 - 1.pdf")
    extractor.chunking_elements()
