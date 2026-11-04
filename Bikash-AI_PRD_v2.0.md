# Bikash-AI --- Product Requirements Document (PRD)

**Version:** 2.0\
**Status:** Development planning\
**Document date:** 4 November 2026\
**Product owner and architect:** Bikash Talukder\
**Project type:** Personal, offline-first Small Language Model (SLM)
assistant

------------------------------------------------------------------------

## 1. Executive Summary

### 1.1 Product overview

Bikash-AI is a personal, lightweight AI assistant built around a small
language model (SLM). It is designed to run locally, work without an
internet connection for its core features, and provide useful Bengali,
English, and Banglish conversations.

The product combines a locally running language model with application
logic, persistent local memory, retrieval over user-approved files, and
a controlled set of local tools. The model is the language and reasoning
component; the surrounding application provides reliable storage,
permissions, tool execution, and user experience.

### 1.2 Product vision

> Intelligence should not always require the cloud.

Bikash-AI should be private, responsive, useful, and portable. It should
continue to provide its core capabilities when the device is
disconnected from the internet.

### 1.3 Core value proposition

-   Offline-first conversations and local inference.
-   Natural Bengali, English, and Banglish interaction.
-   A consistent identity and personality.
-   Optional persistent memory controlled by the user.
-   Local assistance for programming, mathematics, and everyday tasks.
-   Local document retrieval and summarization.
-   Small-model deployment on resource-constrained hardware.

### 1.4 Primary success outcome

A user can launch Bikash-AI on the primary Mac, disconnect the network,
and still chat, receive coding and learning assistance, use supported
local tools, and access previously saved memories and indexed documents.

------------------------------------------------------------------------

## 2. Goals, Non-Goals, and Product Principles

### 2.1 Goals

1.  Select and evaluate a compact multilingual base model.
2.  Customize the model using supervised fine-tuning where evaluation
    shows a clear benefit.
3.  Establish a reliable creator identity and assistant personality.
4.  Implement local conversation history and user-controlled long-term
    memory.
5.  Provide safe local tools such as a calculator and document search.
6.  Measure model quality, latency, and memory use.
7.  Build an offline-first desktop experience before expanding to other
    platforms.
8.  Keep model, application, and data layers modular so they can be
    replaced independently.

### 2.2 Non-goals for the first release

-   Training a foundation model from scratch.
-   Matching the capabilities of large cloud models.
-   Real-time web search while offline.
-   Voice interaction.
-   Image or video understanding and generation.
-   Autonomous computer control.
-   Automatic execution of arbitrary shell commands.
-   Guaranteed identical performance across all mobile and browser
    devices.

### 2.3 Product principles

-   **Offline by default:** Core functionality must not depend on a
    remote API.
-   **Privacy by design:** User data stays on-device unless the user
    explicitly exports or shares it.
-   **Honesty:** The assistant must admit uncertainty and avoid
    fabricating facts.
-   **User control:** Memory, files, and tool permissions must be
    manageable by the user.
-   **Measured performance:** Claims about speed, quality, and memory
    must be backed by tests.
-   **Modularity:** Model, inference runtime, memory, tools, and
    interface remain separate components.

------------------------------------------------------------------------

## 3. Target Users and Use Cases

### 3.1 Target users

-   **Primary user:** Bikash Talukder.
-   **Future users:** Optional users through separate local profiles.
-   **Developer audience:** People interested in running or customizing
    a personal offline assistant.

### 3.2 Main use cases

  -----------------------------------------------------------------------
  Area                                Example
  ----------------------------------- -----------------------------------
  Conversation                        Discuss a topic naturally in
                                      Bengali or English

  Programming                         Explain, debug, and write C++,
                                      Python, or JavaScript

  Education                           Explain mathematics and computer
                                      science step by step

  Reasoning                           Work through logical and
                                      mathematical problems

  Personal memory                     Recall information the user
                                      explicitly chose to save

  Documents                           Search and summarize local PDF,
                                      TXT, and Markdown files

  Productivity                        Perform calculations and draft text

  Offline use                         Continue core tasks with Wi-Fi and
                                      mobile data disabled
  -----------------------------------------------------------------------

### 3.3 Supported language modes

-   Bengali script: `তুমি কেমন আছো?`
-   English: `How does a neural network work?`
-   Banglish: `Tumi amake prefix sum bujhiye dite parbe?`
-   Mixed-language prompts and responses.

The application should preserve the user's language where practical.
Users may also request a specific response language.

------------------------------------------------------------------------

## 4. Functional Requirements

Priority definitions:

-   **P0:** Required for the first usable release.
-   **P1:** Important, but may follow the first release.
-   **P2:** Future enhancement.

### 4.1 Chat and inference

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  FR-001                  User can send and       P0
                          receive text messages.  

  FR-002                  Assistant supports      P0
                          Bengali and English     
                          prompts.                

  FR-003                  Assistant can respond   P0
                          to Banglish prompts.    

  FR-004                  User can start a new    P0
                          conversation.           

  FR-005                  User can view and       P0
                          delete conversation     
                          history.                

  FR-006                  User can stop an        P1
                          ongoing generation.     

  FR-007                  User can adjust         P1
                          generation settings     
                          such as temperature and 
                          maximum output tokens.  

  FR-008                  The interface displays  P0
                          model loading and       
                          generation states.      
  -----------------------------------------------------------------------

### 4.2 Identity and personality

Bikash-AI must maintain a consistent assistant identity across supported
languages.

**Canonical identity facts:**

-   Assistant name: Bikash-AI.
-   Creator: Bikash Talukder.
-   Creator description: A CSE student and the creator of Bikash-AI.
-   Project origin: Created as a personal AI project during the
    creator's second year of computer science studies.

The original requested creator response is:

> I was born by Bikash Talukder, he is a talented AI engineer, 24 years
> old, currently studying computer science and engineering, he made me
> in his second year of his computer science journey.

For production, prefer a grammatically natural response while preserving
the intended facts:

> I was created by Bikash Talukder, a computer science and engineering
> student who built me during his second year of study as part of his
> journey into AI engineering.

The creator's age and academic status can change. Store time-sensitive
personal facts in a versioned local identity configuration rather than
permanently baking them into model weights. Do not present a stale age
as current.

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  FR-009                  Assistant identifies    P0
                          itself as Bikash-AI.    

  FR-010                  Assistant correctly     P0
                          identifies Bikash       
                          Talukder as its         
                          creator.                

  FR-011                  Identity questions are  P0
                          tested in Bengali,      
                          English, and Banglish.  

  FR-012                  Identity facts can be   P0
                          updated without         
                          retraining the model.   

  FR-013                  Assistant follows a     P0
                          consistent, friendly,   
                          honest personality.     
  -----------------------------------------------------------------------

### 4.3 Memory

Memory must be explicit, local, and user-controlled.

  -----------------------------------------------------------------------
  Memory type             Description             Example
  ----------------------- ----------------------- -----------------------
  Core identity           Assistant's stable      Name and creator
                          identity and            
                          configuration           

  Session context         Recent messages in the  Current task details
                          active conversation     

  Conversation history    Locally stored past     Previous chat
                          conversations           

  Long-term memory        User-approved facts and Preferred programming
                          preferences             language

  Document knowledge      Searchable chunks from  Notes and study
                          user-selected files     materials
  -----------------------------------------------------------------------

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  FR-014                  Store conversation      P0
                          history locally.        

  FR-015                  Allow the user to save  P0
                          a memory explicitly.    

  FR-016                  Retrieve relevant saved P1
                          memories when useful.   

  FR-017                  Allow users to view,    P0
                          edit, and delete saved  
                          memories.               

  FR-018                  Memory persists after   P0
                          application restart.    

  FR-019                  The assistant must not  P0
                          claim to remember       
                          information that is not 
                          stored or present in    
                          context.                

  FR-020                  Provide a control to    P1
                          disable long-term       
                          memory.                 
  -----------------------------------------------------------------------

### 4.4 Local tools

The model must not directly execute arbitrary operating-system commands.
A local tool router should validate requests, check permissions, execute
approved operations, and return structured results.

  -----------------------------------------------------------------------
  Tool                    Function                Priority
  ----------------------- ----------------------- -----------------------
  Calculator              Evaluate supported      P0
                          arithmetic expressions  

  Date and time           Read local device date  P1
                          and time                

  File reader             Read supported local    P1
                          text and document files 

  Local document search   Retrieve relevant       P1
                          passages from indexed   
                          files                   

  Code explanation        Explain code supplied   P0
                          by the user             

  Python execution        Run code in a           P2
                          restricted sandbox      

  Notes                   Create and search local P2
                          notes                   
  -----------------------------------------------------------------------

**Tool safety requirements:**

-   Require user permission before accessing files outside approved
    folders.
-   Never execute arbitrary shell commands generated by the model.
-   Use a restricted environment for any future code execution.
-   Apply time, memory, and output limits to executable tools.
-   Treat document contents as untrusted data, not as system
    instructions.
-   Clearly distinguish model-generated answers from tool results.

### 4.5 Local document retrieval

The application may support retrieval-augmented generation (RAG) over
files selected by the user.

Initial supported formats:

-   TXT
-   Markdown
-   PDF with extractable text

Requirements:

1.  User chooses which files or folders to index.
2.  Extracted text is split into manageable chunks.
3.  Chunk metadata records the source filename and location where
    available.
4.  Retrieval returns relevant passages to the model.
5.  Answers should identify the source document when possible.
6.  Removing an indexed file must also remove its stored chunks and
    embeddings.
7.  File indexing and retrieval must work offline.

Scanned PDFs and image-only documents are outside the first release
unless a local OCR component is added.

------------------------------------------------------------------------

## 5. Model Strategy

### 5.1 Candidate base models

The initial candidates are:

-   `Qwen/Qwen3-1.7B`
-   `google/gemma-3-1b-it`

These are candidates, not a final selection. The project must benchmark
both using the same evaluation dataset, prompts, hardware, and
generation settings.

Evaluate:

-   Bengali and Banglish quality.
-   English quality.
-   Coding ability.
-   Instruction following.
-   Reasoning quality.
-   Model license and redistribution conditions.
-   Runtime compatibility.
-   Memory footprint and generation speed.

The model with the best measured balance should be selected. Do not
assume that a larger parameter count or a claimed multilingual
capability guarantees better Bengali output.

### 5.2 Fine-tuning strategy

Preferred approach:

1.  Start with a capable instruction-tuned base model.
2.  Establish a baseline evaluation.
3.  Prepare a high-quality, deduplicated dataset.
4.  Apply LoRA or another supported parameter-efficient fine-tuning
    method.
5.  Compare the fine-tuned model against the baseline.
6.  Keep the fine-tuned checkpoint only if it improves the target tasks
    without unacceptable regressions.

Potential frameworks:

-   MLX-LM for native Apple Silicon workflows.
-   Unsloth in a compatible cloud notebook or supported environment.
-   Other compatible training tools if model architecture support
    requires them.

Fine-tuning should teach response style, instruction following, and
target-domain behavior. Do not rely on fine-tuning as the only source of
exact identity facts or dynamic personal memory.

### 5.3 Quantization

Candidate deployment formats:

-   MLX 4-bit quantization for Apple Silicon.
-   GGUF `Q4_K_M` for compatible llama.cpp-based runtimes.

These formats are not interchangeable. Conversion and runtime
compatibility must be verified for the selected model architecture.

Quantized models must be evaluated for quality loss, memory usage, and
inference speed.

### 5.4 Dataset format

Use JSONL with a consistent conversation schema. ChatML-style or
ShareGPT-style records may be used, but the selected format must match
the training framework's expected schema.

Example ChatML-style record:

``` json
{
  "messages": [
    {
      "role": "system",
      "content": "You are Bikash-AI, a helpful offline assistant."
    },
    {
      "role": "user",
      "content": "তোমাকে কে তৈরি করেছে?"
    },
    {
      "role": "assistant",
      "content": "আমাকে Bikash Talukder তৈরি করেছে।"
    }
  ]
}
```

Dataset quality requirements:

-   Include Bengali, English, and Banglish examples.
-   Include coding, mathematics, general assistance, and identity
    examples.
-   Remove duplicates and malformed records.
-   Avoid including private user conversations without explicit
    permission.
-   Keep evaluation examples separate from training examples.
-   Track dataset version, source, and license.
-   Review examples for factual accuracy and unsafe instructions.

------------------------------------------------------------------------

## 6. System Architecture

### 6.1 High-level architecture

``` text
                    USER
                     |
                     v
             CHAT INTERFACE
                     |
                     v
              APPLICATION CORE
          +----------+-----------+
          |          |           |
          v          v           v
      PROMPT      MEMORY       TOOL
      MANAGER     MANAGER      ROUTER
          |          |           |
          +----------+-----------+
                     |
                     v
               MODEL RUNTIME
                     |
                     v
             LOCAL LANGUAGE MODEL
                     |
                     v
             RESPONSE VALIDATION
                     |
                     v
                CHAT OUTPUT
```

### 6.2 Main components

  Component          Responsibility
  ------------------ --------------------------------------------------
  Chat interface     Message input, output, and conversation controls
  Application core   Coordinates application workflows
  Prompt manager     Builds system and conversation context
  Model runtime      Loads the model and performs inference
  Memory manager     Stores and retrieves local memories
  Tool router        Validates and invokes approved local tools
  Document indexer   Extracts and indexes selected files
  Storage layer      Stores conversations, settings, and metadata
  Security layer     Enforces permissions and data protection

### 6.3 Separation of responsibilities

The language model should not be responsible for enforcing permissions,
storing data, or directly controlling the operating system. Those
responsibilities belong to deterministic application code.

------------------------------------------------------------------------

## 7. Recommended Technology Stack

  -----------------------------------------------------------------------
  Layer                   Initial choice          Notes
  ----------------------- ----------------------- -----------------------
  Base model              Qwen3-1.7B or Gemma 3   Benchmark before
                          1B                      selecting

  Local inference on Mac  MLX / MLX-LM            Native Apple Silicon
                                                  path

  Alternative model       GGUF                    For compatible runtimes
  format                                          

  Fine-tuning             MLX-LM LoRA or Unsloth  Depends on model
                                                  support and training
                                                  environment

  Dataset                 JSONL                   Versioned training and
                                                  evaluation data

  Local database          SQLite                  Conversations,
                                                  settings, and memories

  Embeddings              Small multilingual      Must run locally
                          embedding model         

  Retrieval               SQLite-backed search    Keep the first
                          initially; local vector implementation simple
                          index if needed         

  Desktop interface       Lightweight local       Select after runtime
                          application or PWA      prototype

  Browser inference       WebGPU runtime          Separate compatibility
                                                  and memory tests

  Mobile inference        Compatible native GGUF  Validate model support
                          or platform runtime     per platform

  Testing                 Automated test suite    Include Bengali
                          plus human evaluation   speakers
  -----------------------------------------------------------------------

### 7.1 Runtime strategy

Do not force one inference runtime onto every platform.

-   **Mac:** Start with MLX.
-   **GGUF-compatible devices:** Evaluate llama.cpp-based runtimes.
-   **Browser:** Evaluate a WebGPU-compatible runtime and supported
    model conversion.
-   **Android/iOS:** Select a native runtime after testing model
    compatibility, memory, battery use, and licensing.

The same model weights may not run unchanged in every runtime.

------------------------------------------------------------------------

## 8. Hardware and Performance Requirements

### 8.1 Primary development device

-   Device: MacBook Air M4
-   Unified memory: 16 GB
-   Storage: 256 GB
-   Architecture: Apple Silicon
-   Primary development runtime: MLX

### 8.2 Memory budget

The original target of 1.5 GB must be defined carefully. A 1.7B
parameter model at 4-bit requires roughly 0.85 GB for raw 4-bit weights
before metadata and runtime overhead. Actual memory usage will be higher
due to quantization metadata, model runtime, KV cache, context length,
application memory, and operating-system overhead.

Therefore, track these separately:

1.  Model weights memory.
2.  Runtime and KV-cache memory.
3.  Application memory.
4.  Total process memory.
5.  System memory pressure.

**Initial performance targets (to be validated):**

  -----------------------------------------------------------------------
  Metric                              Initial target
  ----------------------------------- -----------------------------------
  Core offline functionality          Works with network disabled

  Model format                        4-bit candidate

  Model runtime memory                Aim for ≤1.5 GB for a carefully
                                      defined short-context configuration

  Cold model load                     Measure and establish baseline

  Generation speed                    Measure tokens per second on the
                                      target device

  Memory stability                    No unbounded growth during repeated
                                      conversations

  Context handling                    Test short, medium, and long
                                      conversations
  -----------------------------------------------------------------------

The 1.5 GB target is a stretch goal, not a guaranteed requirement for
every model, context length, and runtime. If it cannot be met without
unacceptable quality loss, document the measured result and revise the
target.

### 8.3 Storage management

The 256 GB device has limited storage. The application should:

-   Keep only necessary model checkpoints.
-   Separate training datasets from deployment assets.
-   Allow deletion of temporary checkpoints and caches.
-   Document model and dataset disk requirements.
-   Avoid keeping duplicate quantized model files unnecessarily.

------------------------------------------------------------------------

## 9. Privacy and Security Requirements

  ------------------------------------------------------------------------
  ID                      Requirement              Priority
  ----------------------- ------------------------ -----------------------
  SEC-001                 Core chat and inference  P0
                          work without network     
                          access.                  

  SEC-002                 No user data is sent to  P0
                          remote APIs by default.  

  SEC-003                 User can delete          P0
                          conversations and        
                          memories.                

  SEC-004                 File access is limited   P0
                          to user-approved         
                          locations.               

  SEC-005                 Tool execution is        P0
                          permission-controlled.   

  SEC-006                 Arbitrary                P0
                          model-generated shell    
                          commands are never       
                          executed.                

  SEC-007                 Imported documents are   P0
                          treated as untrusted     
                          input.                   

  SEC-008                 Logs do not expose       P1
                          private content          
                          unnecessarily.           

  SEC-009                 Optional local database  P1
                          encryption is evaluated. 
  ------------------------------------------------------------------------

### 9.1 Offline verification

Offline mode must be tested, not merely assumed.

Test procedure:

1.  Download and install all required assets.
2.  Disable Wi-Fi and other network access.
3.  Launch the application.
4.  Load the local model.
5.  Test chat, memory, calculator, and indexed document retrieval.
6.  Inspect application behavior for unexpected network requests.
7.  Record any feature that still requires connectivity.

Model downloads, software updates, and initial setup may require
internet access. These are setup operations, not offline runtime
capabilities.

------------------------------------------------------------------------

## 10. User Experience Requirements

### 10.1 Initial interface

The first interface should remain simple:

-   Conversation list.
-   Chat message area.
-   Text input.
-   Send and stop controls.
-   Model status indicator.
-   New conversation action.
-   Settings and memory controls.

### 10.2 Settings

Initial settings should include:

-   Selected local model.
-   Generation temperature.
-   Maximum output tokens.
-   Memory enabled/disabled.
-   Conversation history management.
-   Approved document folders.
-   Tool permissions.
-   Clear local data.

### 10.3 User feedback

The interface should clearly indicate:

-   Model loading.
-   Model unavailable or incompatible.
-   Response generation.
-   Tool execution.
-   Memory saved or unavailable.
-   File indexing progress.
-   Errors and recovery instructions.

------------------------------------------------------------------------

## 11. Evaluation and Acceptance Criteria

A release must pass repeatable tests before being considered complete.

### 11.1 Evaluation categories

  Category      Example
  ------------- ----------------------------------------------
  Bengali       Explain machine learning in Bengali
  English       Explain neural networks in English
  Banglish      Respond to a natural Banglish question
  Identity      Answer who created Bikash-AI
  Coding        Solve and explain a C++ array problem
  Mathematics   Solve a multi-step arithmetic problem
  Memory        Recall a saved preference after restart
  Retrieval     Answer a question using an indexed document
  Tool use      Calculate an expression using the calculator
  Offline       Complete core tasks with network disabled
  Safety        Refuse unauthorized file or command access

### 11.2 Acceptance criteria

  -----------------------------------------------------------------------
  Requirement                         Pass condition
  ----------------------------------- -----------------------------------
  Local inference                     Selected model loads and responds
                                      without remote inference

  Offline operation                   All P0 features pass with
                                      networking disabled

  Identity                            Correct creator information in
                                      supported-language test cases

  Language                            Responses are understandable and
                                      relevant in Bengali and English

  Memory persistence                  Saved data remains available after
                                      restart

  Memory control                      User can inspect and delete saved
                                      memories

  Tool safety                         Unauthorized tool requests are
                                      blocked

  Document retrieval                  Retrieved passages come from
                                      indexed user-selected files

  Performance                         RAM, load time, and tokens/sec are
                                      measured and documented

  Stability                           Repeated test conversations do not
                                      crash or cause unbounded memory
                                      growth
  -----------------------------------------------------------------------

### 11.3 Benchmark reporting

Every model experiment should record:

-   Model name and exact revision.
-   Quantization format and settings.
-   Runtime and runtime version.
-   Device and operating-system version.
-   Prompt and generation settings.
-   Test dataset version.
-   Quality scores.
-   Tokens per second.
-   Model load time.
-   Peak memory use.
-   Known failures and limitations.

------------------------------------------------------------------------

## 12. Development Roadmap

### Phase 1 --- Base model prototype

**Deliverables:**

-   Download candidate models.
-   Run local inference on the Mac.
-   Test Bengali, English, Banglish, coding, and reasoning.
-   Record baseline memory and speed.

**Exit condition:** At least one candidate runs reliably on the target
device.

### Phase 2 --- Dataset preparation

**Deliverables:**

-   Define JSONL schema.
-   Prepare identity and personality examples.
-   Prepare multilingual and coding examples.
-   Create a separate evaluation dataset.
-   Track dataset versions and sources.

**Exit condition:** Dataset passes format, quality, and privacy checks.

### Phase 3 --- Fine-tuning experiment

**Deliverables:**

-   Run a small LoRA experiment.
-   Save training configuration and checkpoints.
-   Compare base and fine-tuned models.
-   Evaluate regressions and improvements.

**Exit condition:** Fine-tuning produces a measurable improvement on
target tasks.

### Phase 4 --- Local application and chat

**Deliverables:**

-   Basic chat interface.
-   Model loading and inference integration.
-   Conversation creation and history.
-   Error and loading states.

**Exit condition:** User can chat with the local model through the
application.

### Phase 5 --- Memory system

**Deliverables:**

-   SQLite schema.
-   Conversation persistence.
-   Explicit memory saving.
-   Memory listing, editing, and deletion.
-   Restart persistence tests.

**Exit condition:** User-controlled memory works locally.

### Phase 6 --- Tools and document retrieval

**Deliverables:**

-   Calculator tool.
-   Permission-controlled file reader.
-   Document indexing and retrieval.
-   Tool router and validation.
-   Security tests.

**Exit condition:** Approved tools work offline and unauthorized
operations are blocked.

### Phase 7 --- Optimization and security

**Deliverables:**

-   Quantized model.
-   Performance benchmarks.
-   Memory profiling.
-   Offline verification.
-   Privacy and security review.

**Exit condition:** Performance and security targets are documented and
acceptable.

### Phase 8 --- Additional deployment targets

**Deliverables:**

-   Evaluate GGUF deployment.
-   Prototype browser WebGPU inference.
-   Evaluate Android and iOS runtimes.
-   Test compatibility, battery use, and memory.

**Exit condition:** Each supported platform has its own verified runtime
and acceptance report.

------------------------------------------------------------------------

## 13. Suggested Repository Structure

``` text
bikash-ai/
│
├── README.md
├── LICENSE
├── .gitignore
├── pyproject.toml
│
├── configs/
│   ├── identity.json
│   ├── model.yaml
│   ├── generation.yaml
│   └── tools.yaml
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── training/
│   └── evaluation/
│
├── models/
│   ├── base/
│   ├── finetuned/
│   └── quantized/
│
├── training/
│   ├── prepare_dataset.py
│   ├── train_lora.py
│   ├── evaluate.py
│   └── export_model.py
│
├── app/
│   ├── interface/
│   ├── core/
│   ├── inference/
│   ├── prompts/
│   ├── memory/
│   ├── retrieval/
│   ├── tools/
│   └── security/
│
├── storage/
│   ├── database/
│   └── migrations/
│
├── tests/
│   ├── test_identity.py
│   ├── test_languages.py
│   ├── test_memory.py
│   ├── test_tools.py
│   ├── test_retrieval.py
│   └── test_offline.py
│
├── benchmarks/
│   ├── results/
│   └── reports/
│
└── docs/
    ├── architecture.md
    ├── dataset.md
    ├── training.md
    ├── security.md
    └── deployment.md
```

This is a proposed structure. The exact framework and interface may
change after the first local inference prototype.

------------------------------------------------------------------------

## 14. Risks and Mitigation

  -----------------------------------------------------------------------
  Risk                    Impact                  Mitigation
  ----------------------- ----------------------- -----------------------
  Weak Bengali output     Poor user experience    Compare candidates and
                                                  improve data quality

  Fine-tuning regressions Worse general ability   Keep baseline and run
                                                  regression tests

  High memory use         Slow or failed          Reduce context,
                          inference               optimize runtime,
                                                  benchmark quantization

  Hallucinated identity   Incorrect creator       Use versioned identity
                          information             configuration

  Unsafe tool execution   Data loss or security   Permission checks and
                          issue                   sandboxing

  Mobile incompatibility  Deployment delays       Validate each platform
                                                  independently

  Large storage usage     Limited disk space      Remove redundant
                                                  checkpoints and caches

  Poor retrieval quality  Incorrect document      Test chunking,
                          answers                 embeddings, and source
                                                  grounding

  License restrictions    Limits distribution     Review model and
                                                  dataset licenses before
                                                  release
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 15. Release Plan

### Version 0.1 --- Local prototype

-   One selected base model.
-   Local text chat.
-   Bengali and English testing.
-   Basic identity prompt.
-   Basic performance report.

### Version 0.5 --- Personalized assistant

-   Fine-tuned model if justified by evaluation.
-   Persistent conversation history.
-   Creator identity configuration.
-   Initial memory controls.

### Version 1.0 --- Offline personal assistant

-   Stable local inference.
-   Bengali, English, and Banglish support.
-   User-controlled memory.
-   Calculator and approved file tools.
-   Offline verification.
-   Security and benchmark reports.

### Version 2.0 --- Multi-platform expansion

-   GGUF deployment option.
-   Browser WebGPU prototype or release where compatible.
-   Android and iOS prototypes or releases where compatible.
-   Improved document retrieval.
-   Expanded local tool ecosystem.

A version number represents completed and tested capabilities, not
merely planned features.

------------------------------------------------------------------------

## 16. Open Technical Decisions

The following decisions must be settled through prototypes and
measurements:

1.  Which candidate model gives the best Bengali, Banglish, coding, and
    reasoning quality?
2.  Should the first interface be a desktop app or a local PWA?
3.  Which local embedding model performs well for Bengali and English?
4.  Is SQLite full-text search sufficient for the first release, or is a
    vector index needed?
5.  What context length gives a reasonable quality and memory trade-off?
6.  Which runtime is most practical for Android and iOS?
7.  What exact memory measurement will define the 1.5 GB target?
8.  Which model and dataset licenses permit the intended use and
    redistribution?

These decisions should not be guessed in advance. Record the experiment,
evidence, and final decision in the project documentation.

------------------------------------------------------------------------

## 17. Definition of Done

Bikash-AI Version 1.0 is complete when:

-   The selected model runs locally.
-   Core features work without an internet connection.
-   Bengali and English conversations pass the agreed evaluation.
-   Identity questions return the correct creator information.
-   Conversation history persists locally.
-   Users can manage and delete saved memories.
-   Approved local tools work with permission checks.
-   No arbitrary model-generated shell commands are executed.
-   Performance and memory use are measured on the target Mac.
-   Setup, usage, limitations, and troubleshooting are documented.

------------------------------------------------------------------------

## 18. Final Product Statement

**Bikash-AI is a personal offline intelligence system created by Bikash
Talukder. It combines a compact language model with local memory,
retrieval, and controlled tools to deliver private, useful, multilingual
assistance without depending on cloud inference.**

Its defining qualities are:

-   Small, but useful.
-   Offline, but capable.
-   Personal, but user-controlled.
-   Helpful, but honest.
-   Intelligent, with safety enforced by the application.

**Guiding principle: Build a reliable system around a small model rather
than expecting a small model to do everything alone.**
