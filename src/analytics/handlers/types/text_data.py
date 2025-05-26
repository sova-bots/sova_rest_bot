from dataclasses import dataclass


@dataclass
class TextData:
    reports: list
    period: str
    department: str
    only_negative: bool = False