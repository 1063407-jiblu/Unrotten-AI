# Unrotten

### Find Clarity from Chaos

**Unrotten** is an AI-powered document research application created by
**Saai Pranav Balavelayutha Doss Rajesh**.

It is designed to make large and complicated documents easier to search,
understand, and verify.

Unrotten can work with SEC Form 10-K filings as well as user-uploaded PDF
documents. Instead of requiring users to manually search through hundreds
of pages, they can ask questions in natural language and let the application
retrieve the most relevant sections.

## Live Website

https://unrotten.framer.ai/

## What Problem Does Unrotten Solve?

Large financial and business documents often contain hundreds of pages of
technical language, financial statements, tables, footnotes, and legal
information.

Finding one specific piece of information can take a significant amount of
time.

There is also a problem with long AI conversations known as **context rot**.
As a conversation becomes longer, an AI system can have more difficulty
tracking earlier information. This can make follow-up questions such as
"What about the second one?" harder to answer correctly.

Unrotten was created to address both problems.

## How Unrotten Works

The basic workflow is:

User Question
      ↓
Project or SEC Question?
      ↓
SEC Question → Follow-up Resolution
      ↓
ChromaDB Retrieval
      ↓
Relevant Document Evidence
      ↓
Groq AI
      ↓
Answer

For project or general questions, Unrotten can answer without requiring a
PDF.

For SEC questions, the application retrieves relevant document sections
before generating the answer.

## Main Features

### Chat Without a Document

Users can start a conversation without uploading a document.

This mode can be used for questions about:

- Unrotten
- the project
- documentation
- coding
- architecture
- assignments
- general questions

### SEC 10-K Analysis

Users can select supported companies and retrieve their SEC Form 10-K
filings.

### Custom PDF Upload

Users can upload their own PDF documents for analysis.

### Document Chunking

Large documents are split into smaller overlapping sections so that relevant
information can be retrieved more efficiently.

### ChromaDB Semantic Search

The document sections are converted into vector embeddings and stored in
ChromaDB.

This allows Unrotten to search by meaning rather than relying only on exact
keyword matches.

### Query Expansion

Unrotten can add related terminology to a user's question before searching.
This helps improve retrieval when the wording of the question differs from
the wording used in the source document.

### Conversation Context

Unrotten maintains a compact conversation state to help understand
follow-up questions.

This is designed to reduce the effects of context rot without repeatedly
sending an entire conversation to the model.

### Source Evidence

For document-based questions, Unrotten can display the source text retrieved
from the document so users can check the information behind an answer.

### Light / Dark / System Themes

The interface includes Light, Dark, and System appearance modes.

## Technology

Unrotten is built using:

- Python
- Streamlit
- ChromaDB
- Groq API
- PyPDF
- SEC EDGAR
- semantic vector search
