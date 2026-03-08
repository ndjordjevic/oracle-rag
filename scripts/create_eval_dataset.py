"""Create the oracle-rag golden evaluation dataset in LangSmith.

Run once to create the dataset:
    uv run python scripts/create_eval_dataset.py

The dataset contains ~30 Q/A examples from "Bare-metal Amiga programming 2021_ocr.pdf",
ordered easy → medium → hard across all 12 chapters + appendices.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

DATASET_NAME = "oracle-rag-golden"
DATASET_DESCRIPTION = (
    "Golden evaluation dataset for oracle-rag. "
    "~30 Q/A pairs from 'Bare-metal Amiga programming 2021_ocr.pdf' "
    "covering all 12 chapters, ordered easy → hard."
)

# For expected_document_ids in outputs (evaluator source_in_expected_docs).
# No document_id/tag in inputs — evaluation runs unfiltered retrieval.
DOCUMENT_ID = "Bare-metal Amiga programming 2021_ocr.pdf"

# ── Examples ─────────────────────────────────────────────────────────────
# Each tuple: (question, reference_answer, expected_pages, difficulty)
# difficulty is metadata only — not used by evaluators, but useful for analysis.

EXAMPLES: list[tuple[str, str, list[int], str]] = [
    # ─── EASY: direct factual lookups ─────────────────────────────────────

    # Ch 0 – Introduction
    (
        "Who is the author of the Bare-metal Amiga programming book?",
        "The author is Ing. Edwin Th. van den Oosterkamp from Worcester, UK.",
        [1],
        "easy",
    ),
    (
        "What assembler notation format does this book use for hexadecimal numbers?",
        "The book uses Motorola assembly format where hexadecimal numbers start with a '$' sign and binary numbers start with a '%' sign.",
        [5],
        "easy",
    ),

    # Ch 1 – Overview
    (
        "How wide is the MC68000 external data bus?",
        "The MC68000 has a 16-bit external data bus.",
        [7],
        "easy",
    ),
    (
        "What is the base address of the Amiga custom chip registers?",
        "The custom chip registers are located at base address $DFF000.",
        [13],
        "easy",
    ),
    (
        "What is the difference between chip memory and fast memory on the Amiga?",
        "Chip memory can be accessed by both the custom chips and the processor, while fast memory can only be accessed by the processor. Fast memory is faster because the processor never has to wait for the custom chips to finish their access.",
        [7, 8],
        "easy",
    ),

    # Ch 2 – Audio
    (
        "How many audio channels does the Amiga have?",
        "The Amiga has 4 audio channels (named channel 0 through 3).",
        [23],
        "easy",
    ),
    (
        "What is the maximum sample rate for Amiga audio playback in PAL mode?",
        "The maximum sample rate in PAL mode is approximately 28,867 samples per second, determined by the minimum period register value of 123 system clock cycles (3,546,895 Hz / 123 ≈ 28,837 Hz).",
        [26],
        "easy",
    ),

    # Ch 3 – Colour palette
    (
        "How many colour registers does the OCS/ECS Amiga chipset have?",
        "The OCS/ECS chipset has 32 colour registers (COLOR00 through COLOR31).",
        [45],
        "easy",
    ),

    # Ch 4 – Copper (easy)
    (
        "What is the Copper on the Amiga?",
        "The Copper (co-processor) is a simple programmable processor built into the Agnus chip that runs in parallel with the main 68000 CPU. It can write values to custom chip registers and wait for specific beam positions, allowing mid-screen changes to display parameters like colours, scroll positions, and display modes.",
        [51],
        "easy",
    ),

    # Ch 6 – Sprites (easy)
    (
        "How wide is an Amiga hardware sprite in low resolution mode (in pixels or bits)?",
        "In low resolution mode an Amiga hardware sprite is 16 bits wide, i.e. 16 pixels (one bit per pixel). Each sprite data word is 16 bits.",
        [109],
        "easy",
    ),

    # ─── MEDIUM: understanding concepts and specifics ─────────────────────

    # Ch 1 – Overview (medium)
    (
        "What are the three custom chips (Agnus, Denise, Paula) in the original Amiga and what is each responsible for?",
        "Agnus controls memory access (DMA) and the Copper/Blitter. Denise handles video output and sprites. Paula handles audio, disk I/O, and interrupts.",
        [12],
        "medium",
    ),
    (
        "What are the main differences between OCS, ECS, and AGA chipsets?",
        "OCS is the original chipset. ECS added features like wider Blitter operations (beyond 1024 pixels), new display modes, and productivity modes. AGA significantly expanded the palette from 4,096 to 16.8 million colours (24-bit), increased colour registers from 32 to 256, supported HAM8 mode, wider data fetching, and sprite scan doubling.",
        [12, 13],
        "medium",
    ),

    # Ch 2 – Audio (medium)
    (
        "How does the Amiga low-pass audio filter work and how is it controlled?",
        "The Amiga has a low-pass filter in the audio output path that attenuates high frequencies. It is controlled via bit 1 of CIA-A Port A register (at $BFE001). Setting the bit to 0 enables the filter, while setting it to 1 disables it. On Amiga 500/2000 the LED brightness also indicates the filter state.",
        [30, 31],
        "medium",
    ),

    # Ch 3 – Colour palette (medium)
    (
        "How does the AGA chipset store 24-bit colours using the same 32-bit colour registers?",
        "AGA uses a two-write scheme. Each colour register is written twice: the first write stores the upper 4 bits of each RGB component (like OCS/ECS), and the second write (with the LOCT bit set in BPLCON3) stores the lower 4 bits. This gives 8 bits per component for a total of 24-bit colour depth.",
        [46],
        "medium",
    ),

    # Ch 4 – Copper
    (
        "What are the three Copper instructions and what does each one do?",
        "The three Copper instructions are: MOVE (writes a value to a custom chip register), WAIT (pauses Copper execution until the video beam reaches a specified position), and SKIP (skips the next instruction if the beam has passed a specified position).",
        [51],
        "medium",
    ),
    (
        "What is the CDANG (Copper Danger) bit and why is it important?",
        "The CDANG bit (bit 1 of COPCON register at $DFF02E) controls Copper access to lower custom chip registers. On OCS: the Copper can always access registers at offset $80 and above; setting CDANG extends access down to $40–$7E, but registers below $40 are never accessible. On ECS/AGA: the Copper can access registers $40+ by default; setting CDANG allows access to all registers including those below $40.",
        [57],
        "medium",
    ),

    # Ch 5 – Playfields
    (
        "What is a bitplane and how do multiple bitplanes create colours?",
        "A bitplane is a single plane of pixel data where each bit represents one pixel. Multiple bitplanes are combined per pixel position to form a colour index. For example, 5 bitplanes give a 5-bit index (0–31) into the colour palette, supporting 32 simultaneous colours. Each bitplane adds one bit to the pixel value.",
        [67, 68],
        "medium",
    ),
    (
        "What is dual playfield mode on the Amiga?",
        "Dual playfield mode allows two independent playfields to be displayed simultaneously, each with its own scroll position. Odd-numbered bitplanes (1, 3, 5) form one playfield and even-numbered bitplanes (2, 4, 6) form the other. Where the front playfield pixel is colour 0 (transparent), the back playfield shows through. Each playfield can have up to 8 colours (3 bitplanes each).",
        [75, 76],
        "medium",
    ),

    # Ch 6 – Sprites
    (
        "How many hardware sprites does the Amiga support and what are their basic characteristics?",
        "The Amiga supports 8 hardware sprites (numbered 0–7). Each sprite is 16 pixels wide in low resolution (OCS/ECS). Sprites are organised into pairs and can be attached together to create wider, more colourful combined sprites. Each sprite DMA channel is only active on the scan lines where the sprite is visible, so software can reuse channels for multiple objects per frame.",
        [109, 110],
        "medium",
    ),

    # ─── HARD: synthesis, cross-chapter, deep technical ───────────────────

    # Ch 7 – Blitter
    (
        "Explain how the Blitter's logic function works and how the minterms in BLTCON0 define it.",
        "The Blitter can combine up to 3 source channels (A, B, C) using a boolean logic function before writing the result to destination D. BLTCON0 bits 0–7 define 8 minterms, one for each possible combination of A, B, C inputs (like a truth table). For example, to copy source A: set minterms to $F0 (1111 0000), which means D=A regardless of B and C. For A AND B: set $C0. For A OR B: set $FC. The cookie-cut operation (place a shaped object over background) uses minterms $CA which gives D = (A AND B) OR (NOT A AND C).",
        [148, 149],
        "hard",
    ),
    (
        "How does the Blitter perform line drawing?",
        "The Blitter draws lines using a Bresenham-style algorithm. The LINE bit in BLTCON1 enables line-draw mode; BLTCON1 also specifies the octant (direction via SUD/SUL/AUL bits), sign of the error accumulator, and optional pattern. Source A provides a pixel mask (a single bit set), source C and destination D point to the same bitplane. BLTAPT holds the initial error accumulator value, BLTBDAT provides the line pattern, and BLTCPT/BLTDPT point to the starting word in the bitplane. BLTSIZE starts the operation with height = line length and width = 2 (fixed for line mode).",
        [152, 153],
        "hard",
    ),

    # Ch 5 – Playfields (hard)
    (
        "How does HAM (Hold-And-Modify) mode work and what are its limitations?",
        "HAM6 uses 6 bitplanes. The top 2 bits of each pixel's 6-bit value select a mode: 00 = use palette colour (from the lower 4 bits, addressing 16 palette entries), 01 = hold previous pixel colour but modify blue, 10 = modify red, 11 = modify green. This allows displaying all 4,096 OCS colours on screen simultaneously, but with the limitation that each pixel depends on its left neighbour, causing colour fringing on sharp edges. HAM8 on AGA uses 8 bitplanes but reverses the control bits to the two lowest bitplanes (1 and 2); the upper 6 bitplanes provide a 6-bit value, addressing 64 palette entries in set mode or providing 6-bit component modification.",
        [82, 83],
        "hard",
    ),

    # Ch 8 – DMA
    (
        "How does DMA contention work on the Amiga and what is its impact on the processor?",
        "All DMA channels and the processor share the same chip memory bus. The custom chips have priority: Agnus schedules fixed DMA slots for display, sprites, audio, etc. each scan line. The processor can only access chip memory in cycles not used by DMA. In the worst case (all bitplanes + sprites active), the processor can be almost completely locked out of chip memory for the visible portion of each scan line. Only during horizontal and vertical blanking does the processor get uncontested access. Fast memory is not affected by DMA contention since only the processor accesses it.",
        [178, 179],
        "hard",
    ),

    # Ch 9 – Interrupts
    (
        "How does the Amiga interrupt system map custom chip interrupts to 68000 interrupt levels?",
        "The Amiga maps its 14 chipset interrupt sources to 68000 interrupt levels 1-6 using autovectors. The 14 interrupt sources include: TBE (serial transmit buffer empty), DSKBLK (disk block complete), SOFTINT (software interrupt), PORTS (CIA-A and I/O ports), COPER (Copper), VERTB (vertical blank), BLIT (Blitter finished), AUD0-AUD3 (audio channels), RBF (serial receive buffer full), DSKSYNC (disk sync pattern matched), and EXTER (CIA-B and external). The interrupt handler must check INTREQR to identify which specific source triggered the interrupt, then acknowledge it by writing to INTREQ. Higher-priority levels can preempt lower ones.",
        [187, 190, 191],
        "hard",
    ),

    # Ch 10 – CIAs
    (
        "What are the two CIA chips on the Amiga and what are their base addresses and main functions?",
        "The Amiga has two 8520 CIA chips. CIAA (base address $BFE001) handles the keyboard interface (KDAT/KCLK on SP/CNT pins), game port buttons (joystick/mouse fire buttons), the parallel port data lines (all 8 bits of PRB), and the audio filter control. CIAB (base address $BFD000) handles the serial port handshake lines (via PRA) and all disk drive control signals (motor, drive select, direction, step, side select via PRB). Each CIA provides two interval timers (A and B), a TOD counter, and two 8-bit GPIO ports (PRA and PRB) with programmable direction.",
        [100, 103, 104],
        "hard",
    ),

    # Ch 11 – Disk controller
    (
        "How does MFM encoding work and why is it used for Amiga disk storage?",
        "MFM (Modified Frequency Modulation) encoding ensures that no two consecutive 1-bits appear in the encoded bitstream, preventing unreliable flux transitions on the disk surface. Each data bit is preceded by a clock bit. The clock bit is 1 only if both the current data bit and the previous data bit are 0. This means every data byte becomes 16 bits when encoded. A raw Amiga track contains 11 sectors, each with a header (format type, track number, sector number, sectors-till-end, header checksum, data checksum) followed by 512 bytes of MFM-encoded user data.",
        [207, 208, 209],
        "hard",
    ),

    # Ch 12 – Interfacing
    (
        "How does the Amiga keyboard protocol work?",
        "The keyboard communicates with CIA-A via a synchronous serial protocol. The keyboard sends an 8-bit keycode serially through the KDAT line, with each bit clocked by the KCLK line. The byte is rotated one position to the left before transmission (bit order: 6-5-4-3-2-1-0-7), placing the key transition flag (bit 7) last. After receiving 8 bits, the Amiga must acknowledge by pulling KDAT low for at least 85 microseconds, then releasing it. The keyboard waits for this handshake before sending the next keycode. Key press codes have bit 7 clear; key release codes have bit 7 set.",
        [223, 224],
        "hard",
    ),

    # ─── EDGE CASES: cross-chapter, tricky, or out-of-scope ──────────────

    # Cross-chapter synthesis
    (
        "How do the Copper and the Blitter interact, and what caveat exists when using both?",
        "There is a chipset bug when the CPU accesses a COPJMPx register while the Blitter is active: whichever Blitter DMA channel happens to be active in the next cycle will use the coplist address instead of its originally programmed address, corrupting the blit. The Copper itself does not have this problem — it can safely strobe COPJMPx while the Blitter runs. The workaround is to either let the Copper (not the CPU) trigger coplist jumps, or disable Blitter DMA before the CPU writes to COPJMPx.",
        [56, 57],
        "hard",
    ),

    # Out-of-scope question (answer should not be found)
    (
        "How do you install AmigaOS 3.2 on a Compact Flash card?",
        "This information is not covered in the book. The book is about bare-metal hardware programming, not operating system installation.",
        [],
        "edge-case",
    ),

    # Display modes – cross-chapter retrieval
    (
        "What is Extra Half-Brite (EHB) mode on the Amiga and how does it achieve 64 simultaneous colours?",
        "EHB (Extra Half-Brite) is an OCS/ECS display mode enabled by setting the EHF bit in BPLCON0. It uses 6 bitplanes. The first 5 bitplanes (2^5 = 32) index into the 32 colour registers normally. When bitplane 6 is set for a pixel, the hardware automatically halves the brightness of the colour selected by the lower 5 bitplanes, effectively creating 32 extra half-brightness entries. This doubles the on-screen palette from 32 to 64 simultaneous colours without needing additional colour registers.",
        [43, 44],
        "hard",
    ),
]

assert len(EXAMPLES) == 30, f"Expected 30 examples, got {len(EXAMPLES)}"


def main() -> None:
    if not os.environ.get("LANGSMITH_API_KEY"):
        raise RuntimeError("LANGSMITH_API_KEY not set. Check .env")

    client = Client()

    if client.has_dataset(dataset_name=DATASET_NAME):
        print(f"Dataset '{DATASET_NAME}' already exists. Delete it first if you want to recreate.")
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
