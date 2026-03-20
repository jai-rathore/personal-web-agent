# FluxBot — Factory Knowledge RAG System

## What It Is

FluxBot is a RAG (Retrieval-Augmented Generation) system Jai built at Tesla to give factory floor workers instant answers about equipment, machinery, and operating procedures. Workers on the line can ask questions in plain English and get accurate answers drawn from Tesla's internal documentation — without needing to search through PDFs or call a specialist.

## The Problem It Solved

Tesla's factories contain thousands of pieces of equipment, each with detailed instruction manuals, maintenance guides, and operating procedures. This documentation was historically scattered across file systems, hard to search, and inaccessible to workers who needed it most — the people physically operating or maintaining the equipment.

When a machine behaved unexpectedly or a worker needed to follow a procedure they hadn't done before, the options were: call someone who knew, search through files manually, or guess. All of these wasted time on the factory floor.

## How It Works

FluxBot indexes 1M+ pages of equipment documentation using vector embeddings (pgvector on PostgreSQL). When a worker asks a question, the system:

1. Embeds the query and retrieves the most relevant document chunks
2. Passes those chunks plus the question to an LLM
3. Returns a grounded, cited answer — with references back to the source document

The interface is a simple chat UI accessible from line-side terminals and mobile devices.

## Scale & Impact

- **1M+ documents** indexed across Tesla's equipment library
- Deployed to production factory floors at Fremont and other sites
- Reduced the time workers spend looking up equipment information from minutes to seconds
- Reduced calls to specialists for routine procedure questions

## Technical Details

- **Embedding model:** Custom fine-tuned embeddings for technical/industrial vocabulary
- **Vector store:** PostgreSQL with pgvector extension
- **Retrieval:** Hybrid search (dense + sparse BM25) for better recall on equipment part numbers and technical terms
- **Backend:** Go microservice, Kubernetes, internal Tesla infra
- **Auth:** Integrated with Tesla's internal identity system; respects document-level access controls
