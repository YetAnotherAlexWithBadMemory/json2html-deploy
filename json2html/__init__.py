import azure.functions as func
import json
import logging

app = func.FunctionApp()

@app.function_name(name="json2html")
@app.route(route="json2html", auth_level=func.AuthLevel.FUNCTION)
def json2html(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing OCR JSON to HTML...")

    try:
        raw_body = req.get_body().decode("utf-8-sig")
        data = json.loads(raw_body)
    except Exception:
        return func.HttpResponse("Invalid JSON", status_code=400)

    blocks = data.get("from", [])

    # Вычисление максимальных координат
    max_x = max((b.get("boundingBox", [0])[0] for b in blocks), default=1)
    max_y = max((b.get("boundingBox", [0, 0])[1] for b in blocks), default=1)

    # Целевой размер
    target_width_em = 100
    target_height_em = 100

    scale_x = target_width_em / max_x if max_x else 1
    scale_y = target_height_em / max_y if max_y else 1

    html_lines = [
        "<html><head><meta charset='utf-8'>",
        "<style>body { position: relative; } .block { position: absolute; }</style>",
        "</head><body>"
    ]

    for block in blocks:
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
