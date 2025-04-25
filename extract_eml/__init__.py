import logging
import base64
import json
from email import policy
from email.parser import BytesParser
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        eml_bytes = req.get_body()
        msg = BytesParser(policy=policy.default).parsebytes(eml_bytes)

        attachments = []
        for part in msg.iter_attachments():
            fname = part.get_filename()
            if not fname or fname.lower().startswith("image00"):
                continue
            data = part.get_payload(decode=True)
            attachments.append({
                "filename": fname,
                "contentBytes": base64.b64encode(data).decode()
            })

        return func.HttpResponse(
            body=json.dumps(attachments, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.exception("Error processing EML")
        return func.HttpResponse(
            f"Error: {str(e)}",
            status_code=500
        )
