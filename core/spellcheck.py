from typing import List, Tuple, Dict, Optional, Callable
import json
import urllib.request
import urllib.parse

class BaseSpellChecker:
    def check_text(self, lines: List[str]) -> List[Tuple[int, int, str, str]]:
        raise NotImplementedError

    def check_xml_texts(self, elements_with_text: List[Tuple[str, str]]) -> List[Tuple[str, str, str]]:
        raise NotImplementedError


class SimpleSpellChecker(BaseSpellChecker):
    def __init__(self):
        self.dict: Dict[str, str] = {
            "recieve": "receive",
            "occured": "occurred",
            "Itallian": "Italian",
            "Rowlling": "Rowling",
        }

    def check_text(self, lines: List[str]) -> List[Tuple[int, int, str, str]]:
        results: List[Tuple[int, int, str, str]] = []
        for i, line in enumerate(lines, start=1):
            for wrong, right in self.dict.items():
                start = 0
                while True:
                    idx = line.find(wrong, start)
                    if idx == -1:
                        break
                    results.append((i, idx + 1, wrong, right))
                    start = idx + len(wrong)
        return results

    def check_xml_texts(self, elements_with_text: List[Tuple[str, str]]) -> List[Tuple[str, str, str]]:
        results: List[Tuple[str, str, str]] = []
        for elem_id, text in elements_with_text:
            if not text:
                continue
            for wrong, right in self.dict.items():
                if wrong in text:
                    results.append((elem_id, wrong, right))
        return results


class LanguageToolHTTPSpellChecker(BaseSpellChecker):
    def __init__(self, endpoint: str = "https://api.languagetool.org/v2/check", language: str = "en-US", force_offline: bool = False, request_fn: Optional[Callable[[str, str], dict]] = None):
        self.endpoint = endpoint
        self.language = language
        self.force_offline = force_offline
        self.fallback = SimpleSpellChecker()
        self.request_fn = request_fn

    def _http_check(self, text: str) -> List[Tuple[int, int, str]]:
        if self.request_fn is not None:
            obj = self.request_fn(text, self.language)
        else:
            data = urllib.parse.urlencode({"text": text, "language": self.language}).encode("utf-8")
            req = urllib.request.Request(self.endpoint, data=data)
            with urllib.request.urlopen(req, timeout=5) as resp:
                raw = resp.read().decode("utf-8")
            obj = json.loads(raw)
        out: List[Tuple[int, int, str]] = []
        for m in obj.get("matches", []):
            off = int(m.get("offset", 0))
            length = int(m.get("length", 0))
            repls = m.get("replacements", [])
            sug = repls[0].get("value") if repls else ""
            out.append((off, length, sug))
        return out

    def check_text(self, lines: List[str]) -> List[Tuple[int, int, str, str]]:
        if self.force_offline:
            return self.fallback.check_text(lines)
        text = "\n".join(lines)
        try:
            matches = self._http_check(text)
            starts: List[int] = []
            acc = 0
            for line in lines:
                starts.append(acc)
                acc += len(line) + 1
            results: List[Tuple[int, int, str, str]] = []
            for off, length, sug in matches:
                li = 0
                for i in range(len(starts)):
                    if starts[i] <= off < (starts[i] + len(lines[i]) + 1):
                        li = i
                        break
                col = off - starts[li] + 1
                wrong = lines[li][col - 1: col - 1 + length] if length > 0 else ""
                if wrong and sug:
                    results.append((li + 1, col, wrong, sug))
            return results if results else self.fallback.check_text(lines)
        except Exception:
            return self.fallback.check_text(lines)

    def check_xml_texts(self, elements_with_text: List[Tuple[str, str]]) -> List[Tuple[str, str, str]]:
        if self.force_offline:
            return self.fallback.check_xml_texts(elements_with_text)
        results: List[Tuple[str, str, str]] = []
        for elem_id, text in elements_with_text:
            if not text:
                continue
            try:
                matches = self._http_check(text)
                for off, length, sug in matches:
                    wrong = text[off: off + length] if length > 0 else ""
                    if wrong and sug:
                        results.append((elem_id, wrong, sug))
            except Exception:
                pass
        if not results:
            return self.fallback.check_xml_texts(elements_with_text)
        return results
