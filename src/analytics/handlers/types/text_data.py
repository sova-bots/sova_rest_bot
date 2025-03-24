from dataclasses import dataclass


@dataclass
class TextData:
    reports: list
    period: str
    only_negative: bool = False