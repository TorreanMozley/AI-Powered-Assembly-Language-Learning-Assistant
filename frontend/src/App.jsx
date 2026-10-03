import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import './App.css'


// ============================================================
// FLASHCARDS
// ============================================================

const FLASHCARDS = [
  {
    front: 'add $d, $s, $t',
    back: 'Adds two signed register values and stores the result in $d. It traps on signed overflow.'
  },
  {
    front: 'addu $d, $s, $t',
    back: 'Adds two register values without trapping on overflow.'
  },
  {
    front: 'addi $t, $s, immediate',
    back: 'Adds a sign-extended immediate value to $s and stores the result in $t. It traps on signed overflow.'
  },
  {
    front: 'sub $d, $s, $t',
    back: 'Subtracts $t from $s and stores the result in $d.'
  },
  {
    front: 'mult $s, $t',
    back: 'Multiplies two signed 32-bit values. The 64-bit product is stored in HI and LO.'
  },
  {
    front: 'div $s, $t',
    back: 'Divides $s by $t. The quotient goes to LO and the remainder goes to HI.'
  },
  {
    front: 'mflo $d',
    back: 'Moves the value from the special LO register into $d.'
  },
  {
    front: 'mfhi $d',
    back: 'Moves the value from the special HI register into $d.'
  },
  {
    front: 'lw $t, offset($s)',
    back: 'Loads a 32-bit word from memory address $s + offset into $t.'
  },
  {
    front: 'sw $t, offset($s)',
    back: 'Stores the 32-bit value in $t at memory address $s + offset.'
  },
  {
    front: 'beq $s, $t, label',
    back: 'Branches to label when $s and $t contain equal values.'
  },
  {
    front: 'bne $s, $t, label',
    back: 'Branches to label when $s and $t contain different values.'
  },
  {
    front: '$zero',
    back: 'Register that always contains the value 0.'
  },
  {
    front: '$sp',
    back: 'Stack pointer. It points to the current top of the runtime stack.'
  },
  {
    front: '$ra',
    back: 'Return-address register used by procedure calls.'
  }
]


// ============================================================
// PRACTICE PROBLEMS
// ============================================================

const PRACTICE_PROBLEMS = [
  {
    level: 'Easy',
    question: `Translate this expression into MIPS:

f = a + b

Assume a is in $s0, b is in $s1, and store f in $s2.`,
    answer: 'add $s2, $s0, $s1',
    keywords: ['add', '$s2', '$s0', '$s1'],
    explanation:
      'The add instruction directly computes $s0 + $s1 and stores it in $s2.'
  },

  {
    level: 'Easy',
    question: `What value is stored in $t0?

li $t1, 9
li $t2, 4
sub $t0, $t1, $t2`,
    answer: '5',
    keywords: ['5'],
    explanation: '$t0 receives 9 - 4, so the result is 5.'
  },

  {
    level: 'Easy',
    question: 'Which instruction loads a 32-bit word from memory?',
    answer: 'lw',
    keywords: ['lw'],
    explanation: 'lw means load word.'
  },

  {
    level: 'Medium',
    question: `Translate this expression into MIPS:

f = (a + b) - c

Assume a → $s0, b → $s1, c → $s2, and f → $s3.`,
    answer: `add $t0, $s0, $s1
sub $s3, $t0, $s2`,
    keywords: ['add', 'sub', '$t0', '$s0', '$s1', '$s2', '$s3'],
    explanation:
      'First calculate a + b in a temporary register. Then subtract c.'
  },

  {
    level: 'Medium',
    question: `After this code runs, where are the quotient and remainder?

div $s0, $s1`,
    answer: 'Quotient in LO; remainder in HI.',
    keywords: ['lo', 'hi', 'quotient', 'remainder'],
    explanation:
      'MIPS div places the quotient in LO and the remainder in HI.'
  },

  {
    level: 'Medium',
    question: `What value is stored in $t0?

li $t1, 6
sll $t0, $t1, 2`,
    answer: '24',
    keywords: ['24'],
    explanation:
      'A left shift by 2 multiplies 6 by 2², so 6 × 4 = 24.'
  },

  {
    level: 'Hard',
    question: `Translate this expression into MIPS:

f = (a * b) + (c / d)

Assume a → $s0, b → $s1, c → $s2, d → $s3, and f → $s4.`,
    answer: `mult $s0, $s1
mflo $t0
div $s2, $s3
mflo $t1
add $s4, $t0, $t1`,
    keywords: [
      'mult',
      'mflo',
      'div',
      'add',
      '$s0',
      '$s1',
      '$s2',
      '$s3',
      '$s4'
    ],
    explanation:
      'Compute the product, retrieve it from LO, compute the quotient, retrieve that from LO, and add the two intermediate results.'
  },

  {
    level: 'Hard',
    question: `Find the error and correct this instruction:

add $t0, 5, 8`,
    answer: 'Use registers or load the constants first with li.',
    keywords: ['li', 'register'],
    explanation:
      'add requires register operands. For example: li $t1, 5; li $t2, 8; add $t0, $t1, $t2.'
  }
]


function App() {

  const [view, setView] = useState('chat')

  // Chat
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const [messages, setMessages] = useState([
    {
      sender: 'Tutor',
      text: `Welcome to the AI-Powered Assembly Language Learning Assistant!

Use the AI Tutor for questions, translations, instruction execution, and code writing. You can also open Flashcards or Practice Problems from the sidebar.`
    }
  ])

  // Flashcards
  const [cards, setCards] = useState(FLASHCARDS)
  const [cardIndex, setCardIndex] = useState(0)
  const [showingFront, setShowingFront] = useState(true)

  // Practice
  const [difficulty, setDifficulty] = useState('Mixed')
  const [problem, setProblem] = useState(PRACTICE_PROBLEMS[0])
  const [practiceAnswer, setPracticeAnswer] = useState('')
  const [feedback, setFeedback] = useState(
    'Enter your answer, then click Check Answer.'
  )
  const [correct, setCorrect] = useState(0)
  const [attempted, setAttempted] = useState(0)


  // ============================================================
  // AI TOOL PROMPTS
  // ============================================================

  const prompts = {

    expression: `Translate the following arithmetic expression into correct 32-bit MIPS assembly for MARS.

Show the register mapping, preserve operator precedence, explain every instruction, and provide equivalent pseudocode.

Expression:
`,

    pseudocode: `Translate the following MIPS code into an arithmetic expression or clear pseudocode.

Trace every affected register and explain each line.

MIPS code:
`,

    program: `Write a complete MIPS program for MARS that performs the following task.

Include .data and .text sections, comments, syscalls, an explanation, and a proper exit.

Program requirements:
`,

    execute: `Execute the following MIPS code instruction by instruction.

Show how the values of the variables/registers change after each instruction in a clear table. Briefly explain each instruction and clearly state the final values at the end.

Starting values (if any):

MIPS code:
`,

    trace: `Trace the following MIPS code instruction by instruction.

Create a clear table showing how each affected register changes after every instruction. Then explain the final result.

Initial register values:

MIPS code:
`
  }


  // ============================================================
  // CHAT
  // ============================================================

  function insertPrompt(prompt) {
    setView('chat')
    setInput(prompt)
  }

  function clearInput() {
    setInput('')
  }

  function newConversation() {

    setView('chat')

    setMessages([
      {
        sender: 'Tutor',
        text: 'A new conversation has started.\n\nWhat would you like to learn?'
      }
    ])

    setInput('')
  }


  async function sendQuestion() {

    if (!input.trim() || isLoading) {
      return
    }

    const question = input

    setMessages(previousMessages => [
      ...previousMessages,
      {
        sender: 'You',
        text: question
      }
    ])

    setInput('')
    setIsLoading(true)

    try {

      // Local development uses the local FastAPI server.
      // Production uses the same Render URL as the React website.
      const API_URL = import.meta.env.PROD
        ? ''
        : 'http://127.0.0.1:8000'

      const response = await fetch(
        `${API_URL}/chat`,
        {
          method: 'POST',

          headers: {
            'Content-Type': 'application/json'
          },

          body: JSON.stringify({
            message: question
          })
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.detail || 'The tutor could not respond.'
        )
      }

      setMessages(previousMessages => [
        ...previousMessages,
        {
          sender: 'Tutor',
          text: data.answer
        }
      ])

    } catch (error) {

      setMessages(previousMessages => [
        ...previousMessages,
        {
          sender: 'Tutor',
          text: `Error: ${error.message}`
        }
      ])

    } finally {

      setIsLoading(false)

    }
  }


  function handleInputKeyDown(event) {

    if (event.key === 'Enter' && !event.shiftKey) {

      event.preventDefault()

      sendQuestion()
    }
  }


  // ============================================================
  // FLASHCARDS
  // ============================================================

  function openFlashcards() {
    setView('flashcards')
    setShowingFront(true)
  }

  function flipCard() {
    setShowingFront(!showingFront)
  }

  function nextCard() {
    setCardIndex((cardIndex + 1) % cards.length)
    setShowingFront(true)
  }

  function previousCard() {
    setCardIndex(
      (cardIndex - 1 + cards.length) % cards.length
    )

    setShowingFront(true)
  }

  function shuffleCards() {

    const shuffled = [...cards]

    for (let i = shuffled.length - 1; i > 0; i--) {

      const randomIndex =
        Math.floor(Math.random() * (i + 1))

      const temp = shuffled[i]

      shuffled[i] = shuffled[randomIndex]
      shuffled[randomIndex] = temp
    }

    setCards(shuffled)
    setCardIndex(0)
    setShowingFront(true)
  }


  // ============================================================
  // PRACTICE
  // ============================================================

  function getProblemsForDifficulty(level) {

    if (level === 'Mixed') {
      return PRACTICE_PROBLEMS
    }

    return PRACTICE_PROBLEMS.filter(
      currentProblem =>
        currentProblem.level === level
    )
  }


  function chooseNewProblem(level = difficulty) {

    const available =
      getProblemsForDifficulty(level)

    const randomIndex =
      Math.floor(Math.random() * available.length)

    setProblem(available[randomIndex])

    setPracticeAnswer('')

    setFeedback(
      'Enter your answer, then click Check Answer.'
    )
  }


  function openPractice() {
    setView('practice')
    chooseNewProblem(difficulty)
  }


  function changeDifficulty(event) {

    const selectedLevel = event.target.value

    setDifficulty(selectedLevel)

    chooseNewProblem(selectedLevel)
  }


  function checkAnswer() {

    const userAnswer =
      practiceAnswer.trim().toLowerCase()

    if (!userAnswer) {

      setFeedback('Enter an answer first.')

      return
    }

    const keywords =
      problem.keywords.map(
        keyword => keyword.toLowerCase()
      )

    const matched =
      keywords.filter(
        keyword =>
          userAnswer.includes(keyword)
      )

    const requiredRatio =
      keywords.length > 2 ? 0.75 : 1.0

    const isCorrect =
      matched.length / keywords.length >=
      requiredRatio

    setAttempted(previous => previous + 1)

    if (isCorrect) {

      setCorrect(previous => previous + 1)

      setFeedback(
        `Correct!

${problem.explanation}

Suggested answer:
${problem.answer}`
      )

    } else {

      setFeedback(
        `Not quite.

${problem.explanation}

Suggested answer:
${problem.answer}`
      )
    }
  }


  function showHint() {

    const hintWords =
      problem.keywords
        .slice(0, 3)
        .join(', ')

    setFeedback(
      `Hint:

Think about these key pieces: ${hintWords}`
    )
  }


  const currentCard = cards[cardIndex]


  // ============================================================
  // INTERFACE
  // ============================================================

  return (

    <div className="app">

      <aside className="sidebar">

        <h1>
          AI-Powered
          <br />
          Assembly Language
          <br />
          Learning Assistant
        </h1>


        <h3>AI TOOLS</h3>


        <button
          onClick={() =>
            insertPrompt(prompts.expression)
          }
        >
          Expression → MIPS
        </button>


        <button
          onClick={() =>
            insertPrompt(prompts.pseudocode)
          }
        >
          MIPS → Pseudocode
        </button>


        <button
          onClick={() =>
            insertPrompt(prompts.program)
          }
        >
          Write MIPS Program
        </button>


        <button
          onClick={() =>
            insertPrompt(prompts.execute)
          }
        >
          Execute Instructions
        </button>


        <button
          onClick={() =>
            insertPrompt(prompts.trace)
          }
        >
          Trace Registers
        </button>


        <h3>LEARNING MODES</h3>


        <button onClick={openFlashcards}>
          Flashcards
        </button>


        <button onClick={openPractice}>
          Practice Problems
        </button>


        <button
          className="secondary"
          onClick={newConversation}
        >
          New Conversation
        </button>


        <div className="connection">
          ● AI Tutor Connected
        </div>

      </aside>


      {/* ================= CHAT ================= */}


      {view === 'chat' && (

        <main className="main">

          <h2>
            Ask the Assembly Language Tutor
          </h2>


          <div className="chat">

            {messages.map(
              (message, index) => (

                <div
                  className={`message ${
                    message.sender === 'You'
                      ? 'user'
                      : 'tutor'
                  }`}
                  key={index}
                >

                  <strong>
                    {message.sender}
                  </strong>


                  {message.sender === 'Tutor' ? (

                    <div className="markdown">

                      <ReactMarkdown>
                        {message.text}
                      </ReactMarkdown>

                    </div>

                  ) : (

                    <pre>
                      {message.text}
                    </pre>

                  )}

                </div>
              )
            )}


            {isLoading && (

              <div className="message tutor">

                <strong>Tutor</strong>

                <p>Thinking...</p>

              </div>

            )}

          </div>


          <div className="inputArea">

            <textarea
              value={input}
              onChange={event =>
                setInput(event.target.value)
              }
              onKeyDown={handleInputKeyDown}
              placeholder="Ask a MIPS assembly question..."
              disabled={isLoading}
            />


            <div className="inputButtons">

              <button
                onClick={sendQuestion}
                disabled={isLoading}
              >
                {isLoading
                  ? 'Thinking...'
                  : 'Ask Tutor'}
              </button>


              <button
                className="secondary"
                onClick={clearInput}
                disabled={isLoading}
              >
                Clear Input
              </button>

            </div>

          </div>


          <p className="shortcut">
            Enter to send • Shift + Enter for a new line
          </p>

        </main>
      )}


      {/* ================= FLASHCARDS ================= */}


      {view === 'flashcards' && (

        <main className="main flashcardPage">

          <h2>MIPS Flashcards</h2>


          <p className="cardProgress">
            Card {cardIndex + 1} of {cards.length}
          </p>


          <div
            className="flashcard"
            onClick={flipCard}
          >

            <p className="cardSide">

              {showingFront
                ? 'QUESTION'
                : 'ANSWER'}

            </p>


            <div className="cardContent">

              {showingFront
                ? currentCard.front
                : currentCard.back}

            </div>


            <p className="flipHint">
              Click card to flip
            </p>

          </div>


          <div className="flashcardControls">

            <button onClick={previousCard}>
              ← Previous
            </button>


            <button onClick={flipCard}>
              Flip Card
            </button>


            <button onClick={nextCard}>
              Next →
            </button>


            <button
              className="secondary"
              onClick={shuffleCards}
            >
              Shuffle
            </button>

          </div>

        </main>
      )}


      {/* ================= PRACTICE ================= */}


      {view === 'practice' && (

        <main className="main practicePage">

          <h2>MIPS Practice Problems</h2>


          <div className="practiceTop">

            <div className="difficultyControl">

              <label htmlFor="difficulty">
                Difficulty:
              </label>


              <select
                id="difficulty"
                value={difficulty}
                onChange={changeDifficulty}
              >

                <option>Easy</option>
                <option>Medium</option>
                <option>Hard</option>
                <option>Mixed</option>

              </select>

            </div>


            <strong className="score">

              Score: {correct} / {attempted}

            </strong>

          </div>


          <div className="practicePanel">


            <div className="questionPanel">

              <span className="difficultyBadge">

                {problem.level}

              </span>


              <pre>
                {problem.question}
              </pre>

            </div>


            <label
              className="answerLabel"
              htmlFor="practiceAnswer"
            >
              Your answer:
            </label>


            <textarea
              id="practiceAnswer"
              className="practiceAnswer"
              value={practiceAnswer}
              onChange={event =>
                setPracticeAnswer(
                  event.target.value
                )
              }
              placeholder="Enter your answer here..."
            />


            <div className="feedbackPanel">

              <pre>
                {feedback}
              </pre>

            </div>


            <div className="practiceControls">

              <button
                onClick={() =>
                  chooseNewProblem()
                }
              >
                New Problem
              </button>


              <button onClick={checkAnswer}>
                Check Answer
              </button>


              <button
                className="secondary"
                onClick={showHint}
              >
                Hint
              </button>

            </div>

          </div>

        </main>
      )}

    </div>
  )
}


export default App
