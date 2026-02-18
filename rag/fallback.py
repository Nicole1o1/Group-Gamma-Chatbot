from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class OfficeMatch:
    name: str
    keywords: Tuple[str, ...]


OFFICES: List[OfficeMatch] = [
    OfficeMatch("Admissions Office", ("admission", "apply", "application", "entry")),
    OfficeMatch("Registrar's Office", ("registration", "transcript", "graduation", "academic")),
    OfficeMatch("Finance Office", ("fees", "tuition", "payment", "invoice", "bursary")),
    OfficeMatch("Library", ("library", "books", "borrowing", "lending")),
    OfficeMatch("ICT Helpdesk", ("portal", "password", "wifi", "email", "lms")),
    OfficeMatch("Health Centre", ("health", "clinic", "medical", "sick")),
    OfficeMatch("Student Affairs", ("hostel", "housing", "accommodation", "discipline")),
]


def find_relevant_office(question: str) -> str | None:
    question_lower = question.lower()
    for office in OFFICES:
        if any(keyword in question_lower for keyword in office.keywords):
            return office.name
    return None


def build_fallback_response(question: str) -> str:
    office = find_relevant_office(question)
    if office:
        return (
            "I'm not fully confident in the answer based on the available documents. "
            f"Please reach out to the {office} for the most accurate information."
        )
    return (
        "I'm not fully confident in the answer based on the available documents. "
        "Please reach out to the relevant university office for the most accurate information."
    )
