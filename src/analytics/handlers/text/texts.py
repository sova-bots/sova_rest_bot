from .revenue_texts import revenue_text, revenue_analysis_text
from .losses_texts import losses_text
from .loss_forecast_texts import forecast_text
from .foodcost_texts import foodcost_text, foodcost_analysis_text
from .turnover_texts import turnover_text, product_turnover_text

from ..types.text_data import TextData



# text functions
def text_func_example(text_data: TextData) -> str:
    report = text_data.reports
    return f"{report=}"


# key - report:type, value - make_text_func
text_functions = {
    "revenue": lambda text_data: revenue_text(text_data.reports, text_data.only_negative),
    "analysis.revenue": lambda text_data: revenue_analysis_text(text_data.reports),
    "losses": lambda text_data: losses_text(text_data.reports, text_data.period, text_data.only_negative), 
    "loss-forecast": forecast_text,
    "food-cost": lambda text_data: foodcost_text(text_data),
    "analysis.food-cost": lambda text_data: foodcost_analysis_text(text_data),
    "turnover": turnover_text,
    "analysis.turnover": product_turnover_text,
}





