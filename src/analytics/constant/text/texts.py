from dataclasses import dataclass

from .revenue_texts import revenue_text, revenue_analysis_text
from .losses_texts import losses_text


@dataclass
class TextData:
    reports: list
    period: str
    only_negative: bool = False


# text functions
def text_func_example(text_data: TextData) -> str:
    report = text_data.reports
    return f"{report=}"


# key - report:type, value - make_text_func
text_functions = {
    "revenue": lambda text_data: revenue_text(text_data.reports, text_data.only_negative),
    "analysis-revenue": lambda text_data: revenue_analysis_text(text_data.reports),
    "losses": lambda text_data: losses_text(text_data.reports, text_data.period, text_data.only_negative), 
    "loss-forecast": text_func_example,
}





