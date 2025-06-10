import logging
import azure.functions as func
import base64
import re
import urllib.parse
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        eml_content = req_body.get("eml_content", "")
        filenames = req_body.get("filenames", [])

        if not eml_content or not filenames:
            return func.HttpResponse("Missing eml_content or filenames", status_code=400)

        boundary_match = re.search(r'boundary="([^"]+)"', eml_content)
        if not boundary_match:
            return func.HttpResponse("[ERROR] No boundary found.", status_code=400)

        boundary = boundary_match.group(1)
        parts = eml_content.split("--" + boundary)

        found = {}
        for part in parts:
            header_match = re.search(r"Name\\*?=(?:utf-8''|\"?)([^\n\r;\"]+)", part, re.IGNORECASE)
            if not header_match:
                continue

            raw_filename = header_match.group(1).strip().strip('"').strip()
            decoded_filename = urllib.parse.unquote(raw_filename)

            body_split = re.split(r'\r?\n\r?\n', part, maxsplit=1)
            if len(body_split) < 2:
                continue

            base64_data = body_split[1].strip().replace("\n", "")
            found[decoded_filename] = base64_data

        result = []
        for target in filenames:
            if target in found:
                result.append(found[target])
            else:
                result.append("")  # Return empty string if not found

        return func.HttpResponse(json.dumps(result), mimetype="application/json")

    except Exception as e:
        logging.exception("Unexpected error")
        return func.HttpResponse(f"Unexpected error: {str(e)}", status_code=500)

from email.header import decode_header
from email.message import Message
from urllib.parse import unquote
import re

def extract_attachment_name(part: Message) -> str:
    # 1. Попробовать Name*= (RFC 5987)
    content_type = part.get("Content-Type", "")
    matches = re.findall(r'(?i)\\bname\\*\\s*=\\s*([^;\\n]+)', content_type)
    if matches:
        value = matches[0].strip()
        if value.lower().startswith("utf-8''"):
            return unquote(value[7:])
        else:
            return unquote(value)

    # 2. Попробовать обычное Name=
    matches = re.findall(r'(?i)\\bname\\s*=\\s*"?([^";\\n]+)"?', content_type)
    if matches:
        return matches[0].strip()

    # 3. Попробовать filename*= (RFC 5987)
    content_disposition = part.get("Content-Disposition", "")
    matches = re.findall(r'(?i)\\bfilename\\*\\s*=\\s*([^;\\n]+)', content_disposition)
    if matches:
        value = matches[0].strip()
        if value.lower().startswith("utf-8''"):
            return unquote(value[7:])
        else:
            return unquote(value)

    # 4. Попробовать обычное filename=
    matches = re.findall(r'(?i)\\bfilename\\s*=\\s*"?([^";\\n]+)"?', content_disposition)
    if matches:
        return matches[0].strip()

    # 5. Попробовать MIME-закодированные заголовки
    raw_filename = part.get_filename()
    if raw_filename:
        decoded = decode_header(raw_filename)
        return ''.join([
            frag.decode(enc or 'utf-8') if isinstance(frag, bytes) else frag
            for frag, enc in decoded
        ])

    return None
