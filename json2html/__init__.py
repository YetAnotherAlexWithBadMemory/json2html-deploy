import azure.functions as func
from .blueprint import blueprint

app = func.FunctionApp()
app.register_functions(blueprint)
