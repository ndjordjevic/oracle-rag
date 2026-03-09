"""Tests for structure-aware chunking heuristics."""

from __future__ import annotations

from langchain_core.documents import Document

from oracle_rag.chunking.splitter import chunk_documents


def _mkdoc(text: str) -> Document:
    return Document(
        page_content=text,
        metadata={
            "source": "/tmp/sample.pdf",
            "file_name": "sample.pdf",
            "page": 1,
            "total_pages": 1,
        },
    )


def test_c_code_block_kept_together() -> None:
    text = (
        "Blinky using the onboard LED\n"
        "Create blinky.c containing:\n"
        "#include \"pico/stdlib.h\"\n"
        "\n"
        "int main() {\n"
        "    gpio_init(25);\n"
        "    gpio_set_dir(25, GPIO_OUT);\n"
        "    while (true) {\n"
        "        gpio_put(25, 1);\n"
        "        sleep_ms(500);\n"
        "        gpio_put(25, 0);\n"
        "        sleep_ms(500);\n"
        "    }\n"
        "}\n"
        "This flashes the LED every half second.\n"
    )
    chunks = chunk_documents([_mkdoc(text)], chunk_size=420, chunk_overlap=0)

    code_chunks = [c.page_content for c in chunks if "int main()" in c.page_content]
    assert len(code_chunks) == 1
    assert "gpio_put(25, 0);" in code_chunks[0]
    assert "sleep_ms(500);" in code_chunks[0]
    assert "}" in code_chunks[0]


def test_spi_table_not_split_mid_table() -> None:
    text = (
        "All combinations of these two possibilities gives the four modes:\n"
        "SPI         Clock Polarity       Clock Phase                Characteristics\n"
        "Mode*              CPOL               CPHA\n"
        "0                 0                   0         Clock active high\n"
        "1                 0                   1         Clock active high\n"
        "2                 1                   0         Clock active low\n"
        "3                 1                   1         Clock active low\n"
        "The way SPI modes are labeled is common but not universal.\n"
    )
    chunks = chunk_documents([_mkdoc(text)], chunk_size=520, chunk_overlap=0)

    table_chunks = [
        c.page_content for c in chunks if "Clock Polarity" in c.page_content or "Mode*" in c.page_content
    ]
    assert len(table_chunks) == 1
    assert "0                 0                   0" in table_chunks[0]
    assert "3                 1                   1" in table_chunks[0]


def test_register_table_not_split() -> None:
    text = (
        "COPCON Copper control W $02E\n"
        "Bit |Name Function\n"
        "15-2 Unused, set to zero\n"
        "1 CDANG When set, allow Copper to access dangerous registers\n"
        "0 COPEN Enable Copper DMA\n"
        "The CDANG bit controls lower-register access.\n"
    )
    chunks = chunk_documents([_mkdoc(text)], chunk_size=280, chunk_overlap=0)

    reg_chunks = [c.page_content for c in chunks if "Bit |Name Function" in c.page_content]
    assert len(reg_chunks) == 1
    assert "1 CDANG" in reg_chunks[0]
    assert "0 COPEN" in reg_chunks[0]


def test_asm_block_kept_together() -> None:
    text = (
        "Now set up the blitter registers:\n"
        "MOVE.W #$00F0, $DFF182 ; Red to COLOR01\n"
        "MOVE.W #$0B5A, BLTCON0(a5) ; USEA, C and D\n"
        "ADD.L d1, a0\n"
        "BNE.B .loop\n"
        "This sequence configures and iterates until complete.\n"
    )
    chunks = chunk_documents([_mkdoc(text)], chunk_size=160, chunk_overlap=0)

    asm_chunks = [c.page_content for c in chunks if "MOVE.W #$00F0" in c.page_content]
    assert len(asm_chunks) == 1
    assert "BNE.B .loop" in asm_chunks[0]
    assert "BLTCON0(a5)" in asm_chunks[0]


def test_regular_prose_not_treated_as_code() -> None:
    text = (
        "Summary\n"
        "You can get a long way with only a small understanding of electronics.\n"
        "The maximum current from any GPIO line should be less than 12mA.\n"
    )
    chunks = chunk_documents([_mkdoc(text)], chunk_size=1000, chunk_overlap=0)
    assert len(chunks) == 1
    assert chunks[0].page_content.strip().startswith("Summary")
