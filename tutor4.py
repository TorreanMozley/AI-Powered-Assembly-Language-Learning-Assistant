import os
import random
import threading
import customtkinter as ctk

from tkinter import messagebox
from google import genai
from google.genai import types


# ============================================================
# APP APPEARANCE
# ============================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ============================================================
# GEMINI TUTOR INSTRUCTIONS
# ============================================================

SYSTEM_INSTRUCTIONS = """
You are an intelligent, beginner-friendly college tutor.

You can answer general academic, programming, computer science, and
mathematics questions. Your main specialty is MIPS assembly language.

For MIPS questions, assume classic 32-bit MIPS used in the MARS simulator
unless the student specifies another environment.

Your MIPS abilities include:

- Translating arithmetic expressions into MIPS assembly
- Translating MIPS assembly into arithmetic expressions
- Translating MIPS assembly into pseudocode
- Writing complete MIPS programs
- Debugging incorrect MIPS programs
- Tracing register values
- Explaining instructions
- Explaining memory, stacks, procedures, syscalls, and registers
- Explaining binary, hexadecimal, and two's complement
- Generating practice questions
- Checking student answers

Follow these rules carefully:

1. Never treat variable names such as a, b, x, y, m, n, or f as actual
   MIPS register names.

2. When variables are used, always provide a register mapping.

3. Preserve mathematical parentheses and operator precedence.

4. Use temporary registers such as $t0 through $t9 for intermediate
   calculations.

5. For multiplication, explain mult, HI, LO, and mflo when those
   instructions are used.

6. For division, explain that LO contains the quotient and HI contains
   the remainder.

7. Warn about division by zero when relevant.

8. Distinguish real MIPS instructions from pseudoinstructions.

9. Check MIPS syntax, register usage, arithmetic order, data flow,
   overflow, and logic before saying code is correct.

10. Explain answers step by step in language a student can understand.

11. When a question does not provide enough information, clearly state
    your assumptions.

12. When writing a complete MARS program, include appropriate .data and
    .text sections, main, syscalls, comments, and an exit syscall.

For arithmetic-expression-to-MIPS questions, organize the response as:

MIPS code:
Line-by-line explanation:

Keep the response concise.
Do not include the expression, assumptions, register mapping, equivalent pseudocode,
or important notes as separate sections.
Keep the line-by-line explanation brief and easy to understand.

For MIPS-to-expression questions, organize the response as:

MIPS code analyzed:
Register effects:
Equivalent expression or pseudocode:
Step-by-step explanation:
Possible problems:

For executing-instruction questions, organize the response as:

Starting values:
MIPS code:
Executing each statement:
Final values:

When executing MIPS code:
- Execute instructions in order, one at a time.
- Show how each affected variable/register changes after every instruction.
- Use a clear table with one row per instruction.
- Put the instruction in the first column and relevant variables/registers in the remaining columns.
- Show unchanged values as their current values and use — when a value has not been assigned yet.
- Briefly explain what each instruction does.
- Clearly state the final variable/register values at the end.
- Keep the explanation concise and beginner-friendly.

Do not only provide an answer. Teach the student how the answer works.
"""


# ============================================================
# LOCAL LEARNING CONTENT
# ============================================================

FLASHCARDS = [
    {
        "front": "add $d, $s, $t",
        "back": "Adds two signed register values and stores the result in $d. "
                "It traps on signed overflow."
    },
    {
        "front": "addu $d, $s, $t",
        "back": "Adds two register values without trapping on overflow."
    },
    {
        "front": "addi $t, $s, immediate",
        "back": "Adds a sign-extended immediate value to $s and stores the result "
                "in $t. It traps on signed overflow."
    },
    {
        "front": "sub $d, $s, $t",
        "back": "Subtracts $t from $s and stores the result in $d."
    },
    {
        "front": "mult $s, $t",
        "back": "Multiplies two signed 32-bit values. The 64-bit product is stored "
                "in HI and LO."
    },
    {
        "front": "div $s, $t",
        "back": "Divides $s by $t. The quotient goes to LO and the remainder goes "
                "to HI."
    },
    {
        "front": "mflo $d",
        "back": "Moves the value from the special LO register into $d."
    },
    {
        "front": "mfhi $d",
        "back": "Moves the value from the special HI register into $d."
    },
    {
        "front": "lw $t, offset($s)",
        "back": "Loads a 32-bit word from memory address $s + offset into $t."
    },
    {
        "front": "sw $t, offset($s)",
        "back": "Stores the 32-bit value in $t at memory address $s + offset."
    },
    {
        "front": "beq $s, $t, label",
        "back": "Branches to label when $s and $t contain equal values."
    },
    {
        "front": "bne $s, $t, label",
        "back": "Branches to label when $s and $t contain different values."
    },
    {
        "front": "$zero",
        "back": "Register that always contains the value 0."
    },
    {
        "front": "$sp",
        "back": "Stack pointer. It points to the current top of the runtime stack."
    },
    {
        "front": "$ra",
        "back": "Return-address register used by procedure calls."
    },
]

PRACTICE_PROBLEMS = [
    {
        "level": "Easy",
        "question": (
            "Translate this expression into MIPS:\n\n"
            "f = a + b\n\n"
            "Assume a is in $s0, b is in $s1, and store f in $s2."
        ),
        "answer": "add $s2, $s0, $s1",
        "keywords": ["add", "$s2", "$s0", "$s1"],
        "explanation": "The add instruction directly computes $s0 + $s1 and stores it in $s2."
    },
    {
        "level": "Easy",
        "question": (
            "What value is stored in $t0?\n\n"
            "li $t1, 9\n"
            "li $t2, 4\n"
            "sub $t0, $t1, $t2"
        ),
        "answer": "5",
        "keywords": ["5"],
        "explanation": "$t0 receives 9 - 4, so the result is 5."
    },
    {
        "level": "Easy",
        "question": "Which instruction loads a 32-bit word from memory?",
        "answer": "lw",
        "keywords": ["lw"],
        "explanation": "lw means load word."
    },
    {
        "level": "Medium",
        "question": (
            "Translate this expression into MIPS:\n\n"
            "f = (a + b) - c\n\n"
            "Assume a → $s0, b → $s1, c → $s2, and f → $s3."
        ),
        "answer": "add $t0, $s0, $s1\nsub $s3, $t0, $s2",
        "keywords": ["add", "sub", "$t0", "$s0", "$s1", "$s2", "$s3"],
        "explanation": "First calculate a + b in a temporary register. Then subtract c."
    },
    {
        "level": "Medium",
        "question": (
            "After this code runs, where are the quotient and remainder?\n\n"
            "div $s0, $s1"
        ),
        "answer": "Quotient in LO; remainder in HI.",
        "keywords": ["lo", "hi", "quotient", "remainder"],
        "explanation": "MIPS div places the quotient in LO and the remainder in HI."
    },
    {
        "level": "Medium",
        "question": (
            "What value is stored in $t0?\n\n"
            "li $t1, 6\n"
            "sll $t0, $t1, 2"
        ),
        "answer": "24",
        "keywords": ["24"],
        "explanation": "A left shift by 2 multiplies 6 by 2², so 6 × 4 = 24."
    },
    {
        "level": "Hard",
        "question": (
            "Translate this expression into MIPS:\n\n"
            "f = (a * b) + (c / d)\n\n"
            "Assume a → $s0, b → $s1, c → $s2, d → $s3, and f → $s4."
        ),
        "answer": (
            "mult $s0, $s1\n"
            "mflo $t0\n"
            "div $s2, $s3\n"
            "mflo $t1\n"
            "add $s4, $t0, $t1"
        ),
        "keywords": ["mult", "mflo", "div", "add", "$s0", "$s1", "$s2", "$s3", "$s4"],
        "explanation": "Compute the product, retrieve it from LO, compute the quotient, "
                       "retrieve that from LO, and add the two intermediate results."
    },
    {
        "level": "Hard",
        "question": (
            "Find the error and correct this instruction:\n\n"
            "add $t0, 5, 8"
        ),
        "answer": "Use registers or load the constants first with li.",
        "keywords": ["li", "register"],
        "explanation": "add requires register operands. For example: li $t1, 5; "
                       "li $t2, 8; add $t0, $t1, $t2."
    },
]

MATCHING_PAIRS = [
    ("add", "Add two registers"),
    ("sub", "Subtract one register from another"),
    ("lw", "Load a word from memory"),
    ("sw", "Store a word in memory"),
    ("mult", "Multiply and place the product in HI/LO"),
    ("div", "Divide and place quotient in LO, remainder in HI"),
    ("mflo", "Move the value from LO"),
    ("mfhi", "Move the value from HI"),
    ("beq", "Branch when two registers are equal"),
    ("bne", "Branch when two registers are not equal"),
    ("sll", "Shift bits left"),
    ("srl", "Shift bits right and fill with zeros"),
]


# ============================================================
# MAIN APPLICATION
# ============================================================

class MIPSTutorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI-Powered Assembly Language Learning Assistant")
        self.geometry("1120x800")
        self.minsize(950, 680)

        self.client = None
        self.chat_session = None

        self.initialize_gemini()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_chat_area()

        self.display_message(
            "Tutor",
            (
                "Welcome to the AI-Powered Assembly Language Learning Assistant!\n\n"
                "Use the AI Tutor for questions, translations, instruction execution, "
                "and code writing. You can also open Flashcards or Practice "
                "Problems from the sidebar."
            )
        )

    # ========================================================
    # GEMINI SETUP
    # ========================================================

    def initialize_gemini(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            self.client = None
            self.chat_session = None
            return

        try:
            self.client = genai.Client(api_key=api_key)

            self.chat_session = self.client.chats.create(
                model="gemini-3.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTIONS,
                    temperature=0.3
                )
            )

        except Exception as error:
            print(f"Gemini initialization error: {error}")
            self.client = None
            self.chat_session = None

    # ========================================================
    # SIDEBAR
    # ========================================================

    def create_sidebar(self):
        self.sidebar = ctk.CTkScrollableFrame(
            self,
            width=235,
            corner_radius=0
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        title = ctk.CTkLabel(
            self.sidebar,
            text="AI-Powered\nAssembly Language\nLearning Assistant",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(25, 20))

        ai_label = ctk.CTkLabel(
            self.sidebar,
            text="AI TOOLS",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        ai_label.pack(pady=(5, 5))

        self.sidebar_button("Expression → MIPS", self.insert_expression_prompt)
        self.sidebar_button("MIPS → Pseudocode", self.insert_translation_prompt)
        self.sidebar_button("Write MIPS Program", self.insert_program_prompt)
        self.sidebar_button("Execute Instructions", self.insert_debug_prompt)
        self.sidebar_button("Trace Registers", self.insert_trace_prompt)

        learning_label = ctk.CTkLabel(
            self.sidebar,
            text="LEARNING MODES",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        learning_label.pack(pady=(25, 5))

        self.sidebar_button("Flashcards", self.open_flashcards)
        self.sidebar_button("Practice Problems", self.open_practice)

        new_chat_button = ctk.CTkButton(
            self.sidebar,
            text="New Conversation",
            command=self.new_conversation,
            height=42,
            fg_color="gray40",
            hover_color="gray30"
        )
        new_chat_button.pack(fill="x", padx=15, pady=(25, 7))

        appearance_label = ctk.CTkLabel(
            self.sidebar,
            text="Appearance",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        appearance_label.pack(pady=(20, 8))

        self.appearance_menu = ctk.CTkOptionMenu(
            self.sidebar,
            values=["Dark", "Light", "System"],
            command=self.change_appearance
        )
        self.appearance_menu.set("Dark")
        self.appearance_menu.pack(fill="x", padx=15, pady=(0, 15))

        connection_text = (
            "Gemini connected"
            if self.chat_session is not None
            else "Gemini key not found"
        )
        connection_color = (
            "lightgreen"
            if self.chat_session is not None
            else "orange"
        )

        self.connection_label = ctk.CTkLabel(
            self.sidebar,
            text=connection_text,
            text_color=connection_color
        )
        self.connection_label.pack(pady=(10, 20))

    def sidebar_button(self, text, command):
        button = ctk.CTkButton(
            self.sidebar,
            text=text,
            command=command,
            height=42
        )
        button.pack(fill="x", padx=15, pady=5)

    # ========================================================
    # CHAT AREA
    # ========================================================

    def create_chat_area(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(
            row=0,
            column=1,
            padx=15,
            pady=15,
            sticky="nsew"
        )

        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        heading = ctk.CTkLabel(
            self.main_frame,
            text="Ask the Assembly Language Tutor",
            font=ctk.CTkFont(size=25, weight="bold")
        )
        heading.grid(row=0, column=0, pady=(18, 10))

        self.chat_box = ctk.CTkTextbox(
            self.main_frame,
            wrap="word",
            font=("Courier New", 14)
        )
        self.chat_box.grid(
            row=1,
            column=0,
            padx=20,
            pady=10,
            sticky="nsew"
        )
        self.chat_box.configure(state="disabled")

        input_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent"
        )
        input_frame.grid(
            row=2,
            column=0,
            padx=20,
            pady=(5, 15),
            sticky="ew"
        )
        input_frame.grid_columnconfigure(0, weight=1)

        self.user_input = ctk.CTkTextbox(
            input_frame,
            height=120,
            wrap="word",
            font=("Courier New", 14)
        )
        self.user_input.grid(
            row=0,
            column=0,
            padx=(0, 10),
            sticky="ew"
        )

        self.user_input.bind("<Command-Return>", self.handle_send_shortcut)
        self.user_input.bind("<Control-Return>", self.handle_send_shortcut)

        button_frame = ctk.CTkFrame(
            input_frame,
            fg_color="transparent"
        )
        button_frame.grid(row=0, column=1, sticky="ns")

        self.send_button = ctk.CTkButton(
            button_frame,
            text="Ask Tutor",
            command=self.send_question,
            width=135,
            height=50
        )
        self.send_button.pack(pady=(0, 8))

        clear_input_button = ctk.CTkButton(
            button_frame,
            text="Clear Input",
            command=self.clear_input,
            width=135,
            height=42,
            fg_color="gray40",
            hover_color="gray30"
        )
        clear_input_button.pack()

        shortcut_label = ctk.CTkLabel(
            self.main_frame,
            text="Press Command + Return to send",
            font=ctk.CTkFont(size=12)
        )
        shortcut_label.grid(row=3, column=0, pady=(0, 10))

    # ========================================================
    # CHAT FUNCTIONS
    # ========================================================

    def display_message(self, sender, message):
        self.chat_box.configure(state="normal")
        self.chat_box.insert("end", f"{sender}:\n{message}\n\n")
        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    def send_question(self):
        question = self.user_input.get("1.0", "end").strip()

        if not question:
            messagebox.showinfo(
                "Missing Question",
                "Type a question before pressing Ask Tutor."
            )
            return

        if self.chat_session is None:
            messagebox.showerror(
                "Gemini API Key Missing",
                (
                    "The app could not connect to Gemini.\n\n"
                    "Make sure GEMINI_API_KEY is set in the same "
                    "Terminal window used to run the app."
                )
            )
            return

        self.display_message("You", question)
        self.user_input.delete("1.0", "end")

        self.send_button.configure(state="disabled", text="Thinking...")
        self.display_message("Tutor Status", "Analyzing your question...")

        worker = threading.Thread(
            target=self.request_gemini_response,
            args=(question,),
            daemon=True
        )
        worker.start()

    def request_gemini_response(self, question):
        try:
            response = self.chat_session.send_message(question)
            answer = response.text

            if not answer:
                answer = (
                    "Gemini returned an empty response. "
                    "Please try asking the question again."
                )

            self.after(0, lambda: self.show_gemini_answer(answer))

        except Exception as error:
            error_text = str(error)
            self.after(0, lambda: self.show_request_error(error_text))

    def show_gemini_answer(self, answer):
        self.remove_status_message()
        self.display_message("Gemini Tutor", answer)
        self.send_button.configure(state="normal", text="Ask Tutor")
        self.user_input.focus()

    def show_request_error(self, error_text):
        self.remove_status_message()
        self.display_message("System", self.make_error_readable(error_text))
        self.send_button.configure(state="normal", text="Ask Tutor")

    def make_error_readable(self, error_text):
        lower_error = error_text.lower()

        if "429" in lower_error or "quota" in lower_error:
            return (
                "The Gemini free-tier limit was reached.\n\n"
                "Wait for the quota to reset and try again.\n\n"
                f"Technical details:\n{error_text}"
            )

        if "api key" in lower_error or "401" in lower_error:
            return (
                "Gemini rejected the API key.\n\n"
                "Check GEMINI_API_KEY and restart the app.\n\n"
                f"Technical details:\n{error_text}"
            )

        if "model" in lower_error and "not found" in lower_error:
            return (
                "The selected Gemini model is unavailable.\n\n"
                "Update the model name in tutor.py.\n\n"
                f"Technical details:\n{error_text}"
            )

        return (
            "Gemini could not answer the request.\n\n"
            f"Technical details:\n{error_text}"
        )

    def remove_status_message(self):
        status_message = "Tutor Status:\nAnalyzing your question...\n\n"

        self.chat_box.configure(state="normal")
        current_text = self.chat_box.get("1.0", "end")
        position = current_text.rfind(status_message)

        if position != -1:
            updated_text = (
                current_text[:position]
                + current_text[position + len(status_message):]
            )
            self.chat_box.delete("1.0", "end")
            self.chat_box.insert("1.0", updated_text)

        self.chat_box.configure(state="disabled")
        self.chat_box.see("end")

    def handle_send_shortcut(self, event):
        self.send_question()
        return "break"

    def clear_input(self):
        self.user_input.delete("1.0", "end")
        self.user_input.focus()

    def new_conversation(self):
        confirm = messagebox.askyesno(
            "New Conversation",
            "Clear this conversation and start a new one?"
        )

        if not confirm:
            return

        if self.client is not None:
            try:
                self.chat_session = self.client.chats.create(
                    model="gemini-3.5-flash",
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTIONS,
                        temperature=0.3
                    )
                )
            except Exception as error:
                messagebox.showerror("Conversation Error", str(error))
                return

        self.chat_box.configure(state="normal")
        self.chat_box.delete("1.0", "end")
        self.chat_box.configure(state="disabled")

        self.display_message(
            "Tutor",
            "A new conversation has started.\n\nWhat would you like to learn?"
        )

    def change_appearance(self, mode):
        ctk.set_appearance_mode(mode)

    # ========================================================
    # SPECIAL PROMPT BUTTONS
    # ========================================================

    def insert_prompt(self, prompt):
        self.user_input.delete("1.0", "end")
        self.user_input.insert("1.0", prompt)
        self.user_input.focus()

    def insert_expression_prompt(self):
        self.insert_prompt(
            "Translate the following arithmetic expression into "
            "correct 32-bit MIPS assembly for MARS.\n\n"
            "Show the register mapping, preserve operator precedence, "
            "explain every instruction, and provide equivalent "
            "pseudocode.\n\nExpression:\n"
        )

    def insert_translation_prompt(self):
        self.insert_prompt(
            "Translate the following MIPS code into an arithmetic "
            "expression or clear pseudocode.\n\n"
            "Trace every affected register and explain each line.\n\n"
            "MIPS code:\n"
        )

    def insert_program_prompt(self):
        self.insert_prompt(
            "Write a complete MIPS program for MARS that performs "
            "the following task.\n\n"
            "Include .data and .text sections, comments, syscalls, "
            "an explanation, and a proper exit.\n\n"
            "Program requirements:\n"
        )

    def insert_debug_prompt(self):
        self.insert_prompt(
            "Execute the following MIPS code instruction by instruction.\n\n"
            "Show how the values of the variables/registers change after "
            "each instruction in a clear table. Briefly explain each "
            "instruction and clearly state the final values at the end.\n\n"
            "Starting values (if any):\n\n"
            "MIPS code:\n"
        )

    def insert_trace_prompt(self):
        self.insert_prompt(
            "Trace the following MIPS code instruction by instruction.\n\n"
            "Create a clear table showing how each affected register "
            "changes after every instruction. Then explain the final "
            "result.\n\nInitial register values:\n\nMIPS code:\n"
        )

    # ========================================================
    # FLASHCARDS
    # ========================================================

    def open_flashcards(self):
        window = ctk.CTkToplevel(self)
        window.title("MIPS Flashcards")
        window.geometry("760x540")
        window.minsize(650, 480)
        window.transient(self)

        state = {
            "index": 0,
            "showing_front": True
        }

        title = ctk.CTkLabel(
            window,
            text="MIPS Flashcards",
            font=ctk.CTkFont(size=26, weight="bold")
        )
        title.pack(pady=(25, 10))

        progress_label = ctk.CTkLabel(window, text="")
        progress_label.pack(pady=5)

        card_frame = ctk.CTkFrame(
            window,
            width=620,
            height=300,
            corner_radius=20
        )
        card_frame.pack(padx=35, pady=20, fill="both", expand=True)
        card_frame.pack_propagate(False)

        card_label = ctk.CTkLabel(
            card_frame,
            text="",
            wraplength=560,
            justify="center",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        card_label.pack(expand=True, padx=30, pady=30)

        def update_card():
            card = FLASHCARDS[state["index"]]

            if state["showing_front"]:
                card_label.configure(
                    text=card["front"],
                    font=ctk.CTkFont(size=24, weight="bold")
                )
            else:
                card_label.configure(
                    text=card["back"],
                    font=ctk.CTkFont(size=18)
                )

            progress_label.configure(
                text=f"Card {state['index'] + 1} of {len(FLASHCARDS)}"
            )

        def flip_card():
            state["showing_front"] = not state["showing_front"]
            update_card()

        def previous_card():
            state["index"] = (state["index"] - 1) % len(FLASHCARDS)
            state["showing_front"] = True
            update_card()

        def next_card():
            state["index"] = (state["index"] + 1) % len(FLASHCARDS)
            state["showing_front"] = True
            update_card()

        def shuffle_cards():
            random.shuffle(FLASHCARDS)
            state["index"] = 0
            state["showing_front"] = True
            update_card()

        controls = ctk.CTkFrame(window, fg_color="transparent")
        controls.pack(pady=(0, 25))

        ctk.CTkButton(
            controls,
            text="Previous",
            command=previous_card,
            width=120
        ).grid(row=0, column=0, padx=5)

        ctk.CTkButton(
            controls,
            text="Flip Card",
            command=flip_card,
            width=120
        ).grid(row=0, column=1, padx=5)

        ctk.CTkButton(
            controls,
            text="Next",
            command=next_card,
            width=120
        ).grid(row=0, column=2, padx=5)

        ctk.CTkButton(
            controls,
            text="Shuffle",
            command=shuffle_cards,
            width=120,
            fg_color="gray40",
            hover_color="gray30"
        ).grid(row=0, column=3, padx=5)

        update_card()

    # ========================================================
    # PRACTICE PROBLEMS
    # ========================================================

    def open_practice(self):
        window = ctk.CTkToplevel(self)
        window.title("MIPS Practice Problems")
        window.geometry("850x700")
        window.minsize(720, 600)
        window.transient(self)

        state = {
            "problem": None,
            "correct": 0,
            "attempted": 0
        }

        title = ctk.CTkLabel(
            window,
            text="Practice Problems",
            font=ctk.CTkFont(size=26, weight="bold")
        )
        title.pack(pady=(20, 8))

        top_frame = ctk.CTkFrame(window, fg_color="transparent")
        top_frame.pack(fill="x", padx=25, pady=5)

        ctk.CTkLabel(
            top_frame,
            text="Difficulty:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=(0, 8))

        difficulty_menu = ctk.CTkOptionMenu(
            top_frame,
            values=["Easy", "Medium", "Hard", "Mixed"]
        )
        difficulty_menu.set("Mixed")
        difficulty_menu.pack(side="left")

        score_label = ctk.CTkLabel(
            top_frame,
            text="Score: 0 / 0",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        score_label.pack(side="right")

        question_box = ctk.CTkTextbox(
            window,
            height=210,
            wrap="word",
            font=("Courier New", 15)
        )
        question_box.pack(fill="x", padx=25, pady=(15, 10))
        question_box.configure(state="disabled")

        answer_label = ctk.CTkLabel(
            window,
            text="Your answer:",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        answer_label.pack(anchor="w", padx=25, pady=(5, 5))

        answer_box = ctk.CTkTextbox(
            window,
            height=140,
            wrap="word",
            font=("Courier New", 14)
        )
        answer_box.pack(fill="x", padx=25, pady=(0, 10))

        feedback_box = ctk.CTkTextbox(
            window,
            height=130,
            wrap="word",
            font=("Courier New", 13)
        )
        feedback_box.pack(fill="both", expand=True, padx=25, pady=10)
        feedback_box.configure(state="disabled")

        def set_feedback(text):
            feedback_box.configure(state="normal")
            feedback_box.delete("1.0", "end")
            feedback_box.insert("1.0", text)
            feedback_box.configure(state="disabled")

        def new_problem():
            selected_level = difficulty_menu.get()

            if selected_level == "Mixed":
                available = PRACTICE_PROBLEMS
            else:
                available = [
                    problem
                    for problem in PRACTICE_PROBLEMS
                    if problem["level"] == selected_level
                ]

            state["problem"] = random.choice(available)

            question_box.configure(state="normal")
            question_box.delete("1.0", "end")
            question_box.insert(
                "1.0",
                f"Difficulty: {state['problem']['level']}\n\n"
                f"{state['problem']['question']}"
            )
            question_box.configure(state="disabled")

            answer_box.delete("1.0", "end")
            set_feedback("Enter your answer, then click Check Answer.")
            answer_box.focus()

        def check_answer():
            if state["problem"] is None:
                messagebox.showinfo(
                    "No Problem",
                    "Click New Problem first."
                )
                return

            user_answer = answer_box.get("1.0", "end").strip().lower()

            if not user_answer:
                messagebox.showinfo(
                    "Missing Answer",
                    "Enter an answer first."
                )
                return

            state["attempted"] += 1

            keywords = [
                keyword.lower()
                for keyword in state["problem"]["keywords"]
            ]

            matched = [
                keyword
                for keyword in keywords
                if keyword in user_answer
            ]

            required_ratio = 0.75 if len(keywords) > 2 else 1.0
            is_correct = len(matched) / len(keywords) >= required_ratio

            if is_correct:
                state["correct"] += 1
                feedback = (
                    "Correct!\n\n"
                    f"{state['problem']['explanation']}\n\n"
                    f"Suggested answer:\n{state['problem']['answer']}"
                )
            else:
                feedback = (
                    "Not quite.\n\n"
                    f"{state['problem']['explanation']}\n\n"
                    f"Suggested answer:\n{state['problem']['answer']}"
                )

            score_label.configure(
                text=f"Score: {state['correct']} / {state['attempted']}"
            )
            set_feedback(feedback)

        def show_hint():
            if state["problem"] is None:
                messagebox.showinfo(
                    "No Problem",
                    "Click New Problem first."
                )
                return

            hint_words = ", ".join(state["problem"]["keywords"][:3])
            set_feedback(
                "Hint:\n"
                f"Think about these key pieces: {hint_words}"
            )

        buttons = ctk.CTkFrame(window, fg_color="transparent")
        buttons.pack(pady=(0, 20))

        ctk.CTkButton(
            buttons,
            text="New Problem",
            command=new_problem,
            width=140
        ).grid(row=0, column=0, padx=6)

        ctk.CTkButton(
            buttons,
            text="Check Answer",
            command=check_answer,
            width=140
        ).grid(row=0, column=1, padx=6)

        ctk.CTkButton(
            buttons,
            text="Hint",
            command=show_hint,
            width=120,
            fg_color="gray40",
            hover_color="gray30"
        ).grid(row=0, column=2, padx=6)

        new_problem()

# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":
    app = MIPSTutorApp()
    app.mainloop()
