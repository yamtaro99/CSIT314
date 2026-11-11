from dataclasses import dataclass


@dataclass(frozen=True)
class WeeklyInterest:
    week_start: str
    label: str
    views: int
    shortlist_adds: int


class WeeklyChart:
    def __init__(self, weeks, key, title):
        self.title = title
        self.weeks = weeks
        self.values = [getattr(week, key) for week in weeks]
        self.max_value = max([1, *self.values])
        self.axis_top = max(4, self.max_value)
        self.total = sum(self.values)
        self.points = []
        for index, week in enumerate(weeks):
            x = round(54 + index * 680 / max(len(weeks) - 1, 1), 1)
            y = round(207 - self.values[index] * 160 / self.axis_top, 1)
            self.points.append({"x": x, "y": y, "value": self.values[index],
                                "label": week.label})
        self.polyline = " ".join(f"{p['x']},{p['y']}" for p in self.points)
        self.grid_lines = [
            {"y": round(207 - part * 160 / 4, 1),
             "value": round(self.axis_top * part / 4)}
            for part in range(5)
        ]


@dataclass(frozen=True)
class WeeklyInterestReport:
    weeks: list[WeeklyInterest]
    views_chart: WeeklyChart
    shortlists_chart: WeeklyChart
    is_partial_week: bool = True
