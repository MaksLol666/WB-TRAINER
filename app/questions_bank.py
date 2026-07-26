import random
import re
from dataclasses import dataclass
from pathlib import Path

QUESTION_FILE = Path(__file__).resolve().parent.parent / "voprosi_wb.txt"
DEFAULT_CATEGORY = "Общая работа ПВЗ"
DEFAULT_DIFFICULTY = 1
DEFAULT_TYPE = "Один правильный ответ"
FULL_TEST_LIMIT = 20
CATEGORY_TEST_LIMIT = 20

CATEGORIES = [
    "Общая работа ПВЗ",
    "Приёмка товара",
    "Размещение товара",
    "Выдача заказов",
    "Примерка",
    "Возвраты",
    "Брак",
    "Клиенты",
    "Штрафы",
    "Программа WB",
    "Нестандартные ситуации",
]

DIFFICULTY_MAP = {"легкая": 1, "лёгкая": 1, "средняя": 2, "сложная": 3}


@dataclass(frozen=True)
class Question:
    id: str
    category: str
    difficulty: int
    type: str
    text: str
    answers: list[str]
    correct_indexes: list[int]
    explanation: str

    @property
    def is_multiple(self) -> bool:
        return len(self.correct_indexes) > 1 or "множе" in self.type.lower()


def _after_label(block: str, labels: tuple[str, ...], stop_labels: tuple[str, ...]) -> str:
    pattern = rf"(?:^|\n)(?:{'|'.join(map(re.escape, labels))})\s*:?\s*\n?"
    match = re.search(pattern, block, re.IGNORECASE)
    if not match:
        return ""
    rest = block[match.end():]
    stop_pattern = rf"\n(?:{'|'.join(map(re.escape, stop_labels))})\s*:?\s*\n?"
    stop = re.search(stop_pattern, rest, re.IGNORECASE)
    return rest[:stop.start()].strip() if stop else rest.strip()


def _extract_inline(block: str, label: str) -> str:
    match = re.search(rf"^\s*{re.escape(label)}\s*:\s*(.+)$", block, re.MULTILINE | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _parse_answers(block: str) -> list[str]:
    source = _after_label(block, ("Варианты",), ("Правильный ответ", "Правильные ответы", "Ответ", "Объяснение")) or block
    pairs = re.findall(r"(?:^|\n)\s*([A-D])\.\s*(.+?)(?=\n\s*[A-D]\.\s|\n\s*(?:Правильный ответ|Правильные ответы|Ответ|Объяснение)\b|\Z)", source, re.S)
    return [re.sub(r"\s+", " ", text).strip() for _, text in pairs]


def _parse_correct(block: str, answers: list[str]) -> list[int]:
    raw = _after_label(block, ("Правильный ответ", "Правильные ответы", "Ответ"), ("Объяснение",))
    raw_upper = raw.upper()
    if "ВСЕ" in raw_upper:
        return list(range(len(answers)))
    letters = re.findall(r"\b([A-D])\b", raw_upper)
    indexes = sorted({ord(letter) - ord("A") for letter in letters if ord(letter) - ord("A") < len(answers)})
    return indexes[:1] if indexes else []


def _parse_question(block: str, fallback_category: str) -> Question | None:
    qid_match = re.search(r"\bWB-\d{4}\b", block)
    if not qid_match:
        return None
    qid = qid_match.group(0)
    category = _extract_inline(block, "Категория") or fallback_category or DEFAULT_CATEGORY
    difficulty_raw = (_extract_inline(block, "Сложность") or "").lower()
    difficulty = DIFFICULTY_MAP.get(difficulty_raw, DEFAULT_DIFFICULTY)
    qtype = _extract_inline(block, "Тип") or DEFAULT_TYPE
    text = _after_label(block, ("Вопрос",), ("Варианты", "Правильный ответ", "Правильные ответы", "Ответ", "Объяснение"))
    answers = _parse_answers(block)
    correct_indexes = _parse_correct(block, answers)
    explanation = _after_label(block, ("Объяснение",), tuple()) or "Разберите этот вопрос с наставником, чтобы закрепить правильный порядок действий."
    if not text or len(answers) < 2 or not correct_indexes:
        return None
    return Question(qid, category, difficulty, qtype, re.sub(r"\s+", " ", text).strip(), answers, correct_indexes, re.sub(r"\s+", " ", explanation).strip())


def load_questions() -> list[Question]:
    if not QUESTION_FILE.exists():
        return []
    content = QUESTION_FILE.read_text(encoding="utf-8")
    starts = [m.start() for m in re.finditer(r"(?m)^WB-\d{4}\s*$", content)]
    questions: list[Question] = []
    category = DEFAULT_CATEGORY
    for i, start in enumerate(starts):
        block = content[start: starts[i + 1] if i + 1 < len(starts) else len(content)]
        parsed = _parse_question(block, category)
        if parsed:
            category = parsed.category
            questions.append(parsed)
    return questions


def get_categories() -> list[str]:
    available = {question.category for question in load_questions()}
    return [category for category in CATEGORIES if category in available] + sorted(available - set(CATEGORIES))


def build_test(category: str | None = None) -> list[Question]:
    questions = [q for q in load_questions() if category is None or q.category == category]
    random.shuffle(questions)
    limit = CATEGORY_TEST_LIMIT if category else FULL_TEST_LIMIT
    return questions[:limit]
