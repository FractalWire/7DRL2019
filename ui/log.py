from __future__ import annotations
from typing import Dict, Any
import tcod
import common.topics as topics
from tcodplus.canvas import Canvas
from log import Log


class LogUI(Canvas):
    def __init__(self, *args, mylog: Log = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.log = mylog or Log()
        topics.log.subscribe(self._ev_writelog)

    def _ev_writelog(self, args: Dict[str, Any] = None) -> None:
        self.force_redraw = True

    def base_drawing(self):
        super().base_drawing()
        content_width, content_height = self.geometry[6:]
        max_height = min(30, content_height)

        s = "> " + "\n> ".join(entry['short']
                               for entry in self.log.entries[-max_height:])
        height = tcod.console.get_height_rect(content_width, s)
        y = content_height - height

        dummy = tcod.console.Console(content_width, height)
        dummy.clear(bg=self.style.bg_color, fg=self.style.fg_color)
        dummy.print_box(0, 0, content_width, height, s)
        dummy.blit(self.console, 0, y)


def main():
    LogUI()


if __name__ == '__main__':
    main()
