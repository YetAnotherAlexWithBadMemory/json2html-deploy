import logging
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.getLogger().setLevel(logging.INFO)
    logging.warning("=== DIAG: Функция вызвана ===")

    try:
        raw_body = req.get_body().decode(errors="replace")
        logging.info(f"=== RAW BODY START ===\n{raw_body[:500]}\n=== RAW BODY END ===")
    except Exception as e:
        logging.error(f"Ошибка при получении тела запроса: {e}")
        return func.HttpResponse("Ошибка при чтении тела запроса", status_code=400)

    return func.HttpResponse("Функция вызвана успешно", status_code=200)