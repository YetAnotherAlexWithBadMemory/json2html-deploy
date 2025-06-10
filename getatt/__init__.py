import logging
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.getLogger().setLevel(logging.INFO)
    logging.warning("=== DIAG: Функция вызвана ===")

    return func.HttpResponse("Функция вызвана успешно", status_code=200)