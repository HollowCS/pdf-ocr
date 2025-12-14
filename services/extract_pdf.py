
from unstructured.partition.pdf import partition_pdf
import json


file_path = r"C:\Users\madhu\Downloads\Accord\130 - 4.pdf"
elements = partition_pdf(
    filename= file_path,
    strategy="hi_res",
    infer_table_structure= True,
    infer_column_structure= True,
    infer_row_structure= True,


)

all_text = []
for element in elements:
    text = element.text
    text_dict = text
    all_text.append(text_dict)

json.dump(all_text, open("all_text.json","w"))
print(all_text)