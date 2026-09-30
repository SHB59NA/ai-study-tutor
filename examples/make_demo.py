"""Generate a small text PDF with pypdf; no download, key, or font file needed."""
from io import BytesIO
from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

PAGES = [
    ("Account access", [
        "Cedar Training Center - FICTIONAL example for software testing.",
        "Staff reset forgotten passwords using the self-service portal.",
        "The service desk verifies identity before restoring account access.",
        "Multifactor authentication requires a second factor at sign-in.",
        "Never share passwords or verification codes with another person.",
        "New user accounts are created after supervisor approval.",
    ]),
    ("Service desk workflow", [
        "This policy is fictional, not a real institution's instructions.",
        "An incident is an unplanned interruption to a service.",
        "A service request is a request for standard access or information.",
        "Priority P1 incidents affect the whole training center.",
        "Priority P2 incidents affect one classroom.",
        "Priority P3 incidents affect a single workstation.",
        "Network incidents are assigned to the infrastructure team.",
        "Account access incidents are assigned to the identity team.",
    ]),
    ("Relational data", [
        "A relational database organizes data into tables of rows and columns.",
        "A primary key uniquely identifies each row in a table.",
        "A foreign key links a row to a referenced row in another table.",
        "Referential integrity prevents references to nonexistent records.",
        "A backup copy supports recovery after accidental data loss.",
        "A scheduled restore test checks that a backup can be recovered.",
    ]),
    ("Source-grounded learning", [
        "A tutor retrieves relevant passages before preparing an explanation.",
        "A citation identifies the PDF page used as source evidence.",
        "A page citation alone does not prove that a claim is correct.",
        "Learners should compare the answer with the displayed passage.",
        "If the source lacks an answer, the tutor should acknowledge the gap.",
        "An automatically generated quiz score is not an official assessment.",
    ]),
]


def make_demo_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_metadata({"/Title": "Fictional IT Handbook", "/Author": "AI Study Tutor demo fixture"})
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"),
                             NameObject("/Subtype"): NameObject("/Type1"),
                             NameObject("/BaseFont"): NameObject("/Helvetica")})
    for number, (title, lines) in enumerate(PAGES, 1):
        page = writer.add_blank_page(width=612, height=792)
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})})
        def escape(value: str) -> str:
            return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content = ["BT /F1 18 Tf 48 730 Td", f"({escape(title)}) Tj", "/F1 11 Tf 0 -36 Td"]
        for line in lines:
            content += [f"({escape(line)}) Tj", "0 -22 Td"]
        content += [f"0 -36 Td (Fictional teaching sample - PDF page {number}) Tj ET"]
        stream = DecodedStreamObject()
        stream.set_data("\n".join(content).encode("ascii"))
        page[NameObject("/Contents")] = stream
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


if __name__ == "__main__":
    output = Path(__file__).with_name("fictional_handbook.pdf")
    output.write_bytes(make_demo_pdf())
    print(output)
