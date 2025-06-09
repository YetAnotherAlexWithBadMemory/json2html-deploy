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
