import azure.functions as func
import json
import logging

DEFAULT_SCALE_X = 10
DEFAULT_SCALE_Y = 10

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing OCR JSON to HTML...")

    try:
        raw_body = req.get_body().decode("utf-8-sig")
        data = json.loads(raw_body)
    except Exception:
        return func.HttpResponse("Invalid JSON", status_code=400)

    try:
        scale_x = float(req.params.get("scale_x", DEFAULT_SCALE_X))
    except (ValueError, TypeError):
        scale_x = DEFAULT_SCALE_X

    try:
        scale_y = float(req.params.get("scale_y", DEFAULT_SCALE_Y))
    except (ValueError, TypeError):
        scale_y = DEFAULT_SCALE_Y

    html_lines = [
        "<html><head><meta charset='utf-8'>",
        "<style>body { position: relative; } .block { position: absolute; }</style>",
        "</head><body>"
    ]

    for block in data.get("from", []):
        coords = block.get("boundingBox", [])
        x = coords[0] if len(coords) >= 1 else 0
        y = coords[1] if len(coords) >= 2 else 0
        text = block.get("text", "")
        html_lines.append(
            f"<div class='block' style='left:{x * scale_x}em; top:{y * scale_y}em;'>{text}</div>"
        )

    html_lines.append("</body></html>")
    result = "\n".join(html_lines)

    return func.HttpResponse(result, mimetype="text/html", status_code=200)
