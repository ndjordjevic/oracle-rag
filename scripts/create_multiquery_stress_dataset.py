"""Create the pinrag multi-query stress evaluation dataset in LangSmith.

Run once to create the dataset:
    uv run python scripts/create_multiquery_stress_dataset.py

The dataset contains terse, incomplete, or jargon-heavy questions (like real MCP chat)
from "Bare-metal Amiga programming 2021_ocr.pdf". Same schema as pinrag-golden.
Designed so single-query retrieval fails on most questions, and multi-query expansion
(which adds semantic rephrasing) recovers the correct pages.

Key design principle: questions must have enough semantic content for query variants to
help — multi-phrase or partial-sentence queries work better than bare 1-2 word acronyms.

Polishing history:
  - "cookie cut blitter operation" → "Blitter BOB over background minterm value"
    (corpus uses "cookie cutter" once; actual indexed phrasing is "BOB", "minterm $CA", "D=AB+/AC")
  - "HAM mode colour fringing artifact" → "HAM hold-and-modify dependence on previous pixel"
    ("fringing" absent from corpus; book says "previous pixel (the pixel to the left of this one)")
  - "blitter line draw error accumulator register" → "Blitter line draw BLTAPTL initial value formula"
    ("error accumulator" absent from corpus; book gives BLTAPTL formula with d_min / d_max)
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DATASET_NAME = "pinrag-multiquery-stress"
DATASET_DESCRIPTION = (
    "Multi-query stress dataset for pinrag. "
    "Terse/keyword-style questions from 'Bare-metal Amiga programming 2021_ocr.pdf'. "
    "Designed to be hard for single-query retrieval (no rerank) and easier with query expansion."
)

DOCUMENT_ID = "Bare-metal Amiga programming 2021_ocr.pdf"

# Each tuple: (terse_question, reference_answer, expected_pages, difficulty)
# Questions are terse or incomplete phrases, NOT bare 2-word acronyms.
# They must have enough semantic content for multi-query expansion to rephrase usefully
# while still being too terse / incomplete for single-query to reliably retrieve the right pages.
EXAMPLES: list[tuple[str, str, list[int], str]] = [
    # --- GROUP 1: Terse phrase queries (single-query misses; multi-query expansion helps) ---

    # "BOB over background" is the actual corpus phrasing; "cookie cutter" appears only once.
    # Expansion to "blitter object mask background minterm" helps retrieval of p148-149.
    (
        "Blitter BOB over background minterm value",
        "Placing a BOB (blitter object) over a background uses source A as a mask, source B as the BOB graphic, and source C as the background. The required minterm is $CA, which implements the logic function D = AB + /AC (use B where A is set, use C where A is clear). In code: OR.W #$0FCA, d0 with USEA, B, C and D bits set, then MOVE.W d0, BLTCON0.",
        [148, 149],
        "terse-phrase",
    ),
    # Query preprocessing: boilerplate prefix is stripped before retrieval so retrieval sees "Copper danger bit lower registers".
    (
        "User question: Copper danger bit lower registers",
        "The CDANG bit (bit 1 of COPCON register at $DFF02E) controls Copper access to lower custom chip registers. On OCS: the Copper can always access registers at offset $80 and above; setting CDANG extends access down to $40–$7E, but registers below $40 are never accessible. On ECS/AGA: the Copper can access registers $40+ by default; setting CDANG allows access to all registers including those below $40.",
        [57],
        "preprocess-boilerplate",
    ),
    # "fringing" never appears in the corpus; the actual phrasing is "previous pixel" / "pixel to the left".
    # Expansion to "hold-and-modify colour depends on previous pixel" retrieves p82-83.
    (
        "HAM hold-and-modify dependence on previous pixel",
        "In HAM (hold-and-modify) mode each pixel depends on the previous pixel to its left. The hold-and-modify mechanism takes the three colour components of the previous pixel, holds two components at the same value, and modifies only the third. Because each colour is derived from its left neighbour rather than a palette register, HAM mode is less suitable for displaying windows and text with sharp colour transitions.",
        [82, 83],
        "terse-phrase",
    ),
    # Copper danger bit: CDANG is obscure; expansion to "Copper can access low registers"
    # or "COPCON danger bit" helps find p57
    (
        "Copper danger bit lower registers",
        "The CDANG bit (bit 1 of COPCON register at $DFF02E) controls Copper access to lower custom chip registers. On OCS: the Copper can always access registers at offset $80 and above; setting CDANG extends access down to $40–$7E, but registers below $40 are never accessible. On ECS/AGA: the Copper can access registers $40+ by default; setting CDANG allows access to all registers including those below $40.",
        [57],
        "terse-phrase",
    ),
    # Blitter boolean logic: "minterm" is technical; expansion to "blitter logic function"
    # or "boolean combination source channels" retrieves p148-149
    (
        "blitter minterm logic channels",
        "The Blitter can combine up to 3 source channels (A, B, C) using a boolean logic function before writing the result to destination D. BLTCON0 bits 0–7 define 8 minterms, one for each possible combination of A, B, C inputs (like a truth table). For example, to copy source A: set minterms to $F0 (1111 0000), which means D=A regardless of B and C.",
        [148, 149],
        "terse-phrase",
    ),
    # CIA chip keyboard and ports: expansion from partial phrase to "CIA chip functions keyboard"
    # or "8520 chip game port joystick" helps retrieve p100-104
    (
        "CIA chip keyboard joystick ports",
        "The Amiga has two 8520 CIA chips. CIAA (base address $BFE001) handles the keyboard interface (KDAT/KCLK on SP/CNT pins), game port buttons (joystick/mouse fire buttons), the parallel port data lines (all 8 bits of PRB), and the audio filter control.",
        [100, 103, 104],
        "terse-phrase",
    ),
    # DMA bus contention: expansion from "DMA priority" to "chip memory bus conflict processor"
    # helps retrieve p178-179
    (
        "DMA bus priority chip memory",
        "All DMA channels and the processor share the same chip memory bus. The custom chips have priority: Agnus schedules fixed DMA slots for display, sprites, audio, etc. each scan line. The processor can only access chip memory in cycles not used by DMA.",
        [178, 179],
        "terse-phrase",
    ),

    # --- GROUP 2: Incomplete sentence queries (missing noun/verb; multi-query completes them) ---

    # "error accumulator" never appears in the corpus; actual register is BLTAPTL with a formula.
    # Expansion to "BLTAPTL initial value line draw delta formula" finds p152-153.
    (
        "Blitter line draw BLTAPTL initial value formula",
        "For Blitter line drawing, BLTAPTL is initialised with the formula BLTAPTL = (4 × d_min) - (2 × d_max), where d_min and d_max are the normalised minimum and maximum deltas. If the result is negative the SIGN bit of BLTCON1 must be set. The normalised deltas are also stored into BLTAMOD and BLTBMOD. Source channel A provides a single pixel mask (BLTADAT = $8000), while source C and destination D both point to the same bitplane being drawn into.",
        [152, 153],
        "incomplete",
    ),
    # AGA 24-bit colour two writes: expansion from "AGA low colour bits" to
    # "24-bit colour depth second write lower nibble" finds p46
    (
        "AGA 24-bit colour two write scheme",
        "AGA uses a two-write scheme for 24-bit colour. The second write (with the LOCT bit set in BPLCON3) stores the lower 4 bits of each RGB component, giving 8 bits per component for a total of 24-bit colour depth.",
        [46],
        "incomplete",
    ),
    # Blitter octant direction flags: expansion from "blitter direction ascending" to
    # "line drawing octant control bits BLTCON1" finds p152-153
    (
        "blitter line octant direction flags",
        "BLTCON1 specifies the octant for line drawing via the SUD (sign of delta-x vs delta-y), SUL (direction horizontal or vertical), and AUL (ascending or descending) bits.",
        [152, 153],
        "incomplete",
    ),
    # Disk sync interrupt: expansion from "disk sync interrupt source" to
    # "DSKSYNC pattern matched interrupt handler INTREQR" finds p187-191
    (
        "disk sync pattern interrupt source",
        "DSKSYNC (disk sync pattern matched) is one of the 14 Amiga chipset interrupt sources. The interrupt handler must check INTREQR to identify the specific source.",
        [187, 190, 191],
        "incomplete",
    ),
    # Amiga raw track layout: expansion from "raw track layout sectors" to
    # "MFM track format sector header fields number" finds p207-209
    (
        "Amiga raw track MFM sector layout",
        "A raw Amiga track contains 11 sectors, each with a header (format type, track number, sector number, sectors-till-end, header checksum, data checksum) followed by 512 bytes of MFM-encoded user data.",
        [207, 208, 209],
        "incomplete",
    ),
    # Keyboard acknowledgement pulse: expansion from "keyboard acknowledge pulse timing"
    # to "KDAT low microseconds handshake protocol" finds p223-224
    (
        "keyboard acknowledge pulse timing microseconds",
        "After receiving 8 bits from the keyboard, the Amiga must acknowledge by pulling KDAT low for at least 85 microseconds, then releasing it. The keyboard waits for this handshake before sending the next keycode.",
        [223, 224],
        "incomplete",
    ),
    # CIAB disk motor signals: expansion from "CIAB floppy drive control" to
    # "CIA chip B disk drive motor step signals PRB" finds p100-104
    (
        "CIAB floppy drive motor signals",
        "CIAB (base address $BFD000) handles all disk drive control signals via PRB: motor, drive select, direction, step, and side select.",
        [100, 103, 104],
        "incomplete",
    ),
    # CIA timer and TOD: expansion from "CIA timer time of day" to
    # "CIA interval timer TOD counter GPIO ports" finds p100-104
    (
        "CIA interval timer time of day counter",
        "Each CIA chip provides two interval timers (A and B) and a TOD (Time Of Day) counter, in addition to two 8-bit GPIO ports (PRA and PRB) with programmable direction.",
        [100, 103, 104],
        "incomplete",
    ),
    # Sprite DMA and display window: expansion from "sprite DMA fetch priority" to
    # "Agnus sprite DMA slots scan line" finds p178-179 or sprite DMA pages
    (
        "sprite DMA fetch scan line slots",
        "The Amiga hardware automatically fetches sprite data from chip memory during scan lines using fixed DMA slots allocated by Agnus each horizontal line. Sprites cannot be positioned above the first fetch line.",
        [178, 179],
        "incomplete",
    ),
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create pinrag multi-query stress dataset in LangSmith."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete existing dataset and recreate (default: skip if exists).",
    )
    args = parser.parse_args()

    if not os.environ.get("LANGSMITH_API_KEY"):
        raise RuntimeError("LANGSMITH_API_KEY not set. Check .env")

    client = Client()

    if client.has_dataset(dataset_name=DATASET_NAME):
        if args.force:
            ds = client.read_dataset(dataset_name=DATASET_NAME)
            client.delete_dataset(dataset_id=ds.id)
            print(f"Deleted existing dataset '{DATASET_NAME}'.")
        else:
            print(f"Dataset '{DATASET_NAME}' already exists. Use --force to delete and recreate.")
            return

    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description=DATASET_DESCRIPTION,
    )
    print(f"Created dataset: {dataset.name} (id={dataset.id})")

    examples = []
    for question, answer, pages, difficulty in EXAMPLES:
        examples.append(
            {
                "inputs": {"question": question},
                "outputs": {
                    "answer": answer,
                    "expected_document_ids": [DOCUMENT_ID],
                    "expected_pages": pages,
                },
                "metadata": {
                    "difficulty": difficulty,
                },
            }
        )

    client.create_examples(dataset_id=dataset.id, examples=examples)
    print(f"Uploaded {len(examples)} examples to '{DATASET_NAME}'")


if __name__ == "__main__":
    main()
