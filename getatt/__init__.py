import logging
import base64
import json
import re
from urllib.parse import unquote
from email import message_from_string
from email.header import decode_header
from email.message import Message
import azure.functions as func

logging.getLogger().setLevel(logging.INFO)

def extract_attachment_name(part: Message) -> str:
    content_type = part.get("Content-Type", "")
    matches = re.findall(r'(?i)\bname\*\s*=\s*([^;\n]+)', content_type)
    if matches:
        value = matches[0].strip()
        if value.lower().startswith("utf-8''"):
            return unquote(value[7:])
        else:
            return unquote(value)

    matches = re.findall(r'(?i)\bname\s*=\s*"?([^";\n]+)"?', content_type)
    if matches:
        return matches[0].strip()

    content_disposition = part.get("Content-Disposition", "")
    matches = re.findall(r'(?i)\bfilename\*\s*=\s*([^;\n]+)', content_disposition)
    if matches:
        value = matches[0].strip()
        if value.lower().startswith("utf-8''"):
            return unquote(value[7:])
        else:
            return unquote(value)

    matches = re.findall(r'(?i)\bfilename\s*=\s*"?([^";\n]+)"?', content_disposition)
    if matches:
        return matches[0].strip()

    raw_filename = part.get_filename()
    if raw_filename:
        decoded = decode_header(raw_filename)
        return ''.join([
            frag.decode(enc or 'utf-8') if isinstance(frag, bytes) else frag
            for frag, enc in decoded
        ])

    return None

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("== START getatt ==")

    try:
        data = req.get_json()
        eml_content = data.get("eml_content", "")
        expected_filenames = data.get("filenames", [])

        msg = message_from_string(eml_content)
        found = {}

        for part in msg.walk():
            filename = extract_attachment_name(part)
            if not filename:
                continue
            for target in expected_filenames:
                if filename == target:
                    payload = part.get_payload(decode=True)
                    if payload:
                        found[target] = base64.b64encode(payload).decode("utf-8")
                    else:
                        found[target] = ""
                    break

        result = []
        for name in expected_filenames:
            result.append(found.get(name, ""))

        logging.info("== DONE getatt ==")
        return func.HttpResponse(json.dumps(result, indent=2, ensure_ascii=False), mimetype="application/json")

    except Exception as e:
        logging.exception("Ошибка в getatt")
        return func.HttpResponse(f"Unexpected error: {e}", status_code=500)