import time

class Statistics:
    def __init__(self):
        self._durations = {}
        self._start_at = {}

    def update(self, event_type: str, data: dict):
        fname = data.get('filename')
        if not fname:
            return
        if event_type == 'active_start':
            self._start_at[fname] = time.time()
        elif event_type == 'active_stop':
            start = self._start_at.get(fname)
            if start:
                elapsed = time.time() - start
                self._durations[fname] = self._durations.get(fname, 0) + elapsed
                self._start_at.pop(fname, None)
        elif event_type == 'close':
            self._durations.pop(fname, None)
            self._start_at.pop(fname, None)

    def get_duration_str(self, filename: str) -> str:
        total = self._durations.get(filename, 0)
        if filename in self._start_at:
            total += time.time() - self._start_at[filename]
        seconds = int(total)
        if seconds < 60:
            return f"{seconds}秒"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}分钟"
        hours = minutes // 60
        minutes = minutes % 60
        if hours < 24:
            return f"{hours}小时{minutes}分钟"
        days = hours // 24
        hours = hours % 24
        return f"{days}天{hours}小时"

