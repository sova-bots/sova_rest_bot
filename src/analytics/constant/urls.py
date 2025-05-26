# key - report:type, value - url.group
all_report_urls = {
    "revenue": ["revenue"],
    "analysis.revenue": ["guests-checks", "avg-check", "revenue.department", "revenue.store", "revenue.dish", "revenue.time", "revenue.price_segments", "revenue.date_of_week", "revenue.waiter", "check-depth"],
    "losses": ["losses.product"],
    "loss-forecast": ["loss-forecast.product"],
    "food-cost": ["food-cost"],
    "analysis.food-cost": ["food-cost", "food-cost.dish"],
    "turnover": ["turnover.store"],
    "analysis.turnover": ["turnover.store", "turnover.product"],
    "write-off": ["write-off.account"],
    "inventory": ["inventory.store"],
    "markup": ["markup.store"],
    "analysis.markup": ["markup.store", "markup.dish"]
}