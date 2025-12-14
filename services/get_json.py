import json
import os
import re
from typing import Any, Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
REQUIRED_FIELDS = [
    "applicant_name",
    "federal_employer_id_number",
    "mailing_address",
    "locations",
    "proposed_eff_date",
    "proposed_exp_date",
    "email_address",
    "contact_information",
    "individuals_included_excluded",
    "entity_type",
    "state_rating_worksheet",
    "agency_name_and_address",
    "nature_of_business",
    "website_url",
    "producer_name",
    "cs_representative_name",
    "employers_liability",
]

SYSTEM_PROMPT = """
You are an information extraction engine.
Your job is to read noisy OCR text from ACORD Commercial Insurance Application (ACORD 125) and extract specific fields into clean structured JSON.

Input format

You will receive the document as a Python-style list of lists of strings.

Example: [[ "…page 1 text…", "…more text…" ], [ "…page 2 text…" ]]

Each inner list roughly corresponds to a page or a chunk of text.

The text can be:
- Repeated across pages
- Out of order
- With OCR errors, missing spaces, or broken lines

Your task
From this messy input, extract the following fields if present.
If a field cannot be confidently found, set it to null (do not invent or guess).

The output must be a single JSON object with these keys:

applicant_name
- The full name of the applicant / first named insured.
- Often near labels like: "NAME (First Named Insured)" or "APPLICANT INFORMATION".

federal_employer_id_number
- FEIN / Federal Employer ID Number.
- Often near "FEIN OR SOC SEC # " or similar.

mailing_address
- The full mailing address of the APPLICANT (street, city, state, ZIP+4).
- Prefer the address associated with the FIRST NAMED INSURED.
- Do NOT use the agency/producer address here.

locations
- Main location address(es) for the applicant.
- If no separate locations are given, set this to the same value as mailing_address and clearly indicate that it is the same.
- If nothing can be found, set to null.

proposed_eff_date
- Proposed effective date of the policy, from "PROPOSED EFF DATE".
- Return in ISO format: YYYY-MM-DD when possible; otherwise keep as found.

proposed_exp_date
- Proposed expiration date of the policy, from "PROPOSED EXP DATE".
- Return in ISO format: YYYY-MM-DD when possible; otherwise keep as found.

email_address
- IMPORTANT: This must be the applicant/client’s email address, NOT the agency/producer’s.
- If an email clearly belongs to the agency/producer (for example, its domain matches the agency/producer name like "powersinsurance.com"), ignore it for this field.
- If there is NO applicant/client email address available, set email_address to null.

contact_information
- This should describe the APPLICANT/CLIENT’S contact person, not the agency/producer staff.
- Return as a JSON object with as many of these as you can find:
    - contact_name
    - phone
    - fax
    - contact_role (e.g., "Owner", "Officer", "Applicant contact")
    - any other clearly relevant contact details
- If multiple contacts exist, prefer the main APPLICANT contact.
- If there is NO applicant/client contact but only producer/agency contacts, set contact_information to null.

individuals_included_excluded
- Any information about individuals included or excluded (commonly in Workers Compensation / officers / partners sections).
- If structured, you may return an array of objects; otherwise, return the raw text string summarizing the section.
- If nothing is present, set to null.

entity_type
- Business entity type such as:
  "CORPORATION", "INDIVIDUAL", "JOINT VENTURE", "NOT FOR PROFIT ORG",
  "SUBCHAPTER \"S\" CORPORATION", "LLC", "PARTNERSHIP", "TRUST", "OTHER".
- Use the checkmarks / indicators from the form if visible.
- If the entity type is not explicitly checked, you may infer it based on the nature of business or the name.
- Example rule: if the nature_of_business or other text clearly indicates "law practice" and no other entity type is specified, you may infer "LLC" as entity_type (unless the form explicitly shows a different entity type).

state_rating_worksheet
- Any reference, text, or indicator about a "State Rating Worksheet" if present.
- If only referenced as an attachment, return a short string like "Attached" or the surrounding line of text.
- If nothing is present, set to null.

agency_name_and_address
- Name and address of the AGENCY/PRODUCER, usually at the top of the form.
- Example: "Powers Insurance & Risk Management, 6825 Clayton Avenue, St. Louis, MO 63139".

nature_of_business
- Description of operations / nature of business / type of business of the APPLICANT.
- Look for labels like "NATURE OF BUSINESS", "DESCRIBE OPERATIONS", "TYPE OF BUSINESS".
- Return the short descriptive text exactly or cleanly, for example: "Law practice".
- This is about WHAT THE APPLICANT DOES, not about the agency.
- Do NOT set this to null if such a description (e.g. "law practice") is clearly present anywhere under the applicant section.

website_url
- Website of the APPLICANT/CLIENT only (e.g., "www.frankelrubin.com" or "https://…").
- If a URL clearly belongs to the agency/producer (for example, its domain matches the agency/producer name or address), ignore it for this field.
- If multiple URLs appear, choose the one most likely associated with the applicant.
- If no applicant website exists, set to null.

producer_name
- Name of the producer (agency or agent) responsible.
- Often near "PRODUCER" at the top.
- For example: "Carrie Barber".

cs_representative_name
- Name of the Customer Service Representative / CS Representative / CSR if present.
- If not found, set to null.

employers_liability
- Employers liability limits (often part of Workers Compensation section).
- Return as a structured object if possible, e.g.:
  {
    "each_accident": "1000000",
    "disease_policy_limit": "1000000",
    "disease_each_employee": "1000000"
  }
- If not available in a structured form, return the raw text string.
- If no information is present, set to null.

General rules
- Use the entire input, not just the first chunk or first page.
- Prefer APPLICANT/CLIENT data over agency/producer data whenever there is ambiguity (for email, website, contact info, etc.).
- Clean up line breaks, extra spaces, and obvious OCR noise.
- Never invent data that is not clearly implied by the text.
- If a value is truly missing or unreadable, set that field to null.

Output format
- Respond with only a JSON object, no explanation, no Markdown, no extra text.
"""

# -------------------------------------------------------
# Helper Functions
# -------------------------------------------------------

def gather_text(data: Dict[str, Any]) -> str:
    """Combine all text from any field."""
    parts = []

    if isinstance(data.get("full_text"), str):
        parts.append(data["full_text"])

    if isinstance(data.get("text"), list):
        for t in data["text"]:
            if isinstance(t, dict) and "text" in t:
                parts.append(t["text"])
            elif isinstance(t, str):
                parts.append(t)

    sc = data.get("structured_content") or {}
    if isinstance(sc, dict):
        if isinstance(sc.get("text"), list):
            for t in sc["text"]:
                if isinstance(t, dict) and "text" in t:
                    parts.append(t["text"])
                elif isinstance(t, str):
                    parts.append(t)

        if isinstance(sc.get("tables"), list):
            for tbl in sc["tables"]:
                if isinstance(tbl, dict):
                    if tbl.get("text"):
                        parts.append(tbl["text"])
                    elif tbl.get("cells"):
                        parts.append("\n".join(["\t".join(row) for row in tbl["cells"]]))

    text = "\n".join(parts)
    return re.sub(r"\s+", " ", text).strip()


def safe_json_parse(s: str):
    """Attempts to extract JSON from model output."""
    if "```json" in s:
        s = s.split("```json")[1].split("```")[0].strip()
    elif "```" in s:
        s = s.split("```")[1].split("```")[0].strip()

    match = re.search(r"\{[\s\S]*\}", s)
    if match:
        return json.loads(match.group(0))
    return None


def dedup_list_of_dicts(items: List[Dict], keys: List[str]):
    seen = set()
    out = []
    for item in items:
        key = tuple(item.get(k) for k in keys)
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


# -------------------------------------------------------
# Main Function – Call This One
# -------------------------------------------------------

def extract_and_dedup(json_file_path: str, model="gpt-4") -> Dict[str, Any]:
    # 1. Load source file
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2. Build text blob for model
    full_text = gather_text(data)

    # 4. Call OpenAI
    user_prompt = f"""
Extract ALL requested fields below strictly into JSON.

DOCUMENT CONTENT:
{full_text}
"""

    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
    )

    model_text = response.choices[0].message.content

    parsed = safe_json_parse(model_text) or {}

    # 5. Build final result ensuring all keys exist
    result = {k: parsed.get(k, None) for k in REQUIRED_FIELDS}

    # 6. Deduplicate contacts
    if isinstance(result.get("contact_information"), list):
        result["contact_information"] = dedup_list_of_dicts(
            result["contact_information"], ["name", "email", "phone"]
        )

    # 7. Deduplicate locations
    if isinstance(result.get("locations"), list):
        result["locations"] = dedup_list_of_dicts(
            result["locations"], ["street", "city", "state", "zip"]
        )

    # 8. Deduplicate state rating rows
    if isinstance(result.get("state_rating_worksheet"), list):
        result["state_rating_worksheet"] = dedup_list_of_dicts(
            result["state_rating_worksheet"], ["class_code"]
        )

    return result


# -------------------------------------------------------
# Optional Helper: Save Result
# -------------------------------------------------------

def save_result(data: Dict[str, Any], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


result = extract_and_dedup(r"C:\Users\madhu\PycharmProjects\pdf-ocr\extracted_content.json")
print(result)
