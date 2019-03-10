from __future__ import annotations
from typing import Dict, List
import tcod
from tcodplus.canvas import Canvas


class LogEntry:
    def __init__(self, short: str, title: str = "", text: str = "") -> None:
        self.short = short
        self.title = title
        self.text = text

    @property
    def description(self) -> Dict[str, str]:
        return dict(title=self.title, text=self.text)


class Log:
    def __init__(self):
        self.entries: List[LogEntry] = []

    def append(self, entry: LogEntry) -> None:
        self.entries.append(entry)


# class LogEntryWidget(BoxFocusable):
#     def __init__(self, *args, **kwargs) -> None:
#         super().__init__(*args, **kwargs)
        # self.entry = LogEntry()


class LogScreen(Canvas):
    def __init__(self, *args, log: Log = Log(), **kwargs):
        super().__init__(*args, **kwargs)

        self.log = Log()

    def append(self, s: str) -> None:
        self.log.append(s)
        self.force_redraw = True

    def base_drawing(self):
        super().base_drawing()
        content_width, content_height = self.geometry[6:]
        max_height = min(30, content_height)

        s = "> " + \
            "\n> ".join(entry.short for entry in self.log.entries[-max_height:])
        height = tcod.console.get_height_rect(content_width, s)
        y = content_height - height

        dummy = tcod.console.Console(content_width, height)
        dummy.clear(bg=self.style.bg_color, fg=self.style.fg_color)
        dummy.print_box(0, 0, content_width, height, s)
        dummy.blit(self.console, 0, y)
