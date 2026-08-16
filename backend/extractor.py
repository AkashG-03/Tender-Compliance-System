# extractor.py
# FAISS RAG Requirements Extractor - OpenAI version (Hybrid retrieval)
# - Hybrid: generic heading detector + embedding-based retrieval over size-chunks
# - Caching / canonicalization for deterministic outputs
# - Minimal changes to external behaviour; drop-in replacement for previous extractor

import json
import re
import os
import hashlib
from typing import List, Tuple, Dict

import faiss
import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from models import Requirement


class Extractor:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        if not api_key:
            raise ValueError("API key required")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model

        # Cache directory for deterministic extraction results
        self.cache_dir = os.path.join("data", "extraction_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        print("📥 Loading embedding model...")
        self.emb_model = SentenceTransformer("all-MiniLM-L6-v2")
        dim = self.emb_model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(dim)
        print("✅ Extractor ready (OpenAI mode)")

        # ----------------------------
        # Retrieval & grouping params
        # ----------------------------
        self.top_m_sections = 6  # keep top M high-value sections
        self.semantic_queries = [
            "mandatory requirements for bidder",
            "submission requirements proposal documents",
            "technical proposal staff methodology deliverables",
            "financial proposal fees taxes pricing",
            "evaluation qualification criteria bidders",
            "scope of work deliverables milestones",
            "confidentiality indemnity insurance obligations",
            "proposal submission instructions deadlines",
            "application submission requirements",
            "contract obligations deliverables termination",
        ]
        self.top_k_per_query = 12
        self.max_selected_chunks_for_llm = 40
        self.enable_semantic_grouping = True
        self.semantic_grouping_threshold = 0.82  # cosine for adjacent merge
        self.max_merged_chars = 2500  # don't create enormous merged chunks

    # ----------------------------
    # Public extraction entrypoint
    # ----------------------------
    def extract(self, text: str) -> List[Requirement]:
        """
        Main extraction flow with canonicalization + caching.
        If a cached extraction for the normalized document exists, return it.
        Otherwise run the hybrid RAG extraction and cache the result.
        """
        print(f"\n{'=' * 70}")
        print("🎯 EXTRACTING REQUIREMENTS (Hybrid C: headings + semantic retrieval + cache)")
        print(f"{'=' * 70}\n")

        # Compute canonical normalized text and hash
        normalized = self._normalize_for_hash(text)
        doc_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        cache_path = os.path.join(self.cache_dir, f"{doc_hash}.json")

        # If cache exists return it (deterministic)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as fh:
                    cached = json.load(fh)
                print(f"🔁 Cache hit: returning cached extraction for hash {doc_hash}")
                reqs = []
                for r in cached.get("requirements", []):
                    reqs.append(
                        Requirement(
                            req_id=r.get("req_id", ""),
                            requirement_text=r.get("requirement_text", ""),
                            category=r.get("category", "General"),
                            mandatory=r.get("mandatory", True),
                            keywords=r.get("keywords", []),
                        )
                    )
                print(f"✅ Returned {len(reqs)} cached requirements\n")
                return reqs
            except Exception as e:
                print(f"⚠️ Failed to read cache ({cache_path}): {e}. Will re-extract.")

        # Proceed with extraction (cache miss)
        all_requirements: List[Requirement] = []

        # 0) Deterministic application requirements extraction (unchanged behaviour)
        core_reqs = self._extract_application_requirements(text)
        if core_reqs:
            print(f"✅ Deterministically extracted {len(core_reqs)} core submission requirements")
            all_requirements.extend(core_reqs)

        # 1) Chunk (size-based baseline)
        chunks = self._chunk(text)  # returns ordered list of strings
        print(f"✅ Created {len(chunks)} chunks")

        if not chunks:
            # If no chunks but we have core_reqs, return them and cache
            reqs = self._dedup(all_requirements)
            for i, r in enumerate(reqs, 1):
                r.req_id = f"REQ{i:03d}"
            self._save_cache(cache_path, reqs)
            print(f"✅ Final: {len(reqs)} requirements (no chunks) - cached\n")
            return reqs

        # Keep metadata: original index -> chunk text
        chunk_meta = [{"idx": i, "text": chunks[i]} for i in range(len(chunks))]

        # 2) Embed all size-chunks
        embeds = self.emb_model.encode([c["text"] for c in chunk_meta], convert_to_numpy=True)
        self.index.reset()  # reset index each call to avoid contamination
        self.index.add(np.array(embeds, dtype=np.float32))

        # 3a) Generic heading detection -> high_value_sections
        high_value_sections = self._detect_high_value_sections(text, top_m=self.top_m_sections)
        if high_value_sections:
            print(f"📌 Detected {len(high_value_sections)} high-value sections (heading detector)")
        else:
            print("ℹ️ No high-value sections detected by heading detector")

        # 3b) Semantic retrieval over size-chunks (combine queries)
        selected_indices = self._semantic_retrieve_indices(embeds, chunk_meta)
        print(f"✅ Semantic retrieval selected {len(selected_indices)} unique chunk indices")

        # Filter out front-matter / TOC heuristics and cap
        filtered_indices = self._filter_and_cap_indices(selected_indices, chunk_meta, cap=self.max_selected_chunks_for_llm)
        print(f"🧹 After TOC/front-matter filtering and cap: {len(filtered_indices)} chunks")

        # Order deterministically by original chunk index
        filtered_indices.sort()
        selected_chunks_ordered = [chunk_meta[i]["text"] for i in filtered_indices]

        # 4) Optional semantic grouping (merge adjacent chunks if highly similar)
        if self.enable_semantic_grouping and len(filtered_indices) > 1:
            print("🔗 Attempting semantic grouping of adjacent selected chunks...")
            selected_chunks_ordered = self._semantic_group_adjacent(filtered_indices, chunk_meta, embeds)
            print(f"🔗 After grouping: {len(selected_chunks_ordered)} chunks")

        # 5) Assemble LLM context: high_value_sections first, then selected chunks
        combined_parts = []
        # small metadata header (keeps context stable)
        combined_parts.append(f"[DOCUMENT HASH: {doc_hash}]")
        if high_value_sections:
            combined_parts.append("\n\n".join(high_value_sections))
        if selected_chunks_ordered:
            combined_parts.append("\n\n".join(selected_chunks_ordered[:self.max_selected_chunks_for_llm]))

        rel_text = "\n\n".join([p for p in combined_parts if p])
        print(f"📝 LLM context length: {len(rel_text)} chars\n")

        # Also include any deterministic extra section we previously used (Application Submission Requirements / Section III)
        extra_section = ""
        m = re.search(
            r"1\.\s*Application Submission Requirements(.+?)(\n\s*2\.\s*Guidelines for Preparations and Submission of Proposals|\Z)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if m:
            extra_section = m.group(0)
            print(f"📌 Added Application Submission Requirements section to LLM context (len={len(extra_section)})")

        if not extra_section:
            # include CAK-style SECTION III if present
            m2 = re.search(
                r"SECTION\s+III\s*-\s*EVALUATION AND QUALIFICATION CRITERIA(.+?)(SECTION\s+IV\b|PART\s+2\b|\Z)",
                text,
                re.DOTALL | re.IGNORECASE,
            )
            if m2:
                extra_section = m2.group(0)
                print(f"📌 Added Evaluation & Qualification Criteria section (len={len(extra_section)})")

        combined_text = rel_text
        if extra_section:
            combined_text = rel_text + "\n\n" + extra_section

        # 6) First pass: proposal / submission requirements via LLM
        print("🤖 Calling OpenAI for proposal requirements...")
        reqs_proposal = self._llm_extract(combined_text)
        all_requirements.extend(reqs_proposal)

        # 7) Second pass: Agreement / contract section via LLM (unchanged)
        agreement_text = self._extract_agreement_section(text)
        if agreement_text:
            print("📄 Extracting requirements from Agreement / contract section (LLM)...")
            reqs_agreement = self._llm_extract(agreement_text, agreement_mode=True)
            all_requirements.extend(reqs_agreement)
        else:
            print("ℹ️ No explicit Agreement section detected (skipping LLM Agreement pass)")

        # 8) Fallback if nothing (unchanged)
        if not all_requirements:
            print("⚠️ LLM returned 0, trying fallback with full document...")
            all_requirements = self._llm_extract_fallback(text[:20000])

        # 9) Deduplicate (smart, substring-aware) and assign IDs
        reqs = self._dedup(all_requirements)
        for i, r in enumerate(reqs, 1):
            r.req_id = f"REQ{i:03d}"

        # Save final extraction to cache for repeatable results
        try:
            self._save_cache(cache_path, reqs)
            print(f"💾 Saved extraction to cache: {cache_path}")
        except Exception as e:
            print(f"⚠️ Failed to save cache ({cache_path}): {e}")

        print(f"✅ Final: {len(reqs)} requirements\n")
        return reqs

    # ----------------------------
    # Helper: save cache
    # ----------------------------
    def _save_cache(self, path: str, requirements: List[Requirement]) -> None:
        """Save list of Requirement objects as JSON to cache path."""
        payload = {
            "requirements": [r.__dict__ if hasattr(r, "__dict__") else r.dict() for r in requirements]
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)

    # ----------------------------
    # Normalize for stable hashing
    # ----------------------------
    def _normalize_for_hash(self, text: str) -> str:
        """
        Normalize the document for stable hashing:
        - remove common footer/header artifacts
        - remove page numbers like 'Page 1 of 10' or '1 2025/07/14 9:56 AM'
        - collapse whitespace
        - remove repetitive short lines that likely are headers/footers
        """
        t = text

        # Remove timestamps and trailing date/time artifacts
        t = re.sub(r"\d+\s+\d{4}/\d{2}/\d{2}.*", " ", t)

        lines = t.splitlines()
        cleaned_lines = []
        freq = {}
        for ln in lines:
            s = ln.strip()
            if len(s) <= 3:
                continue
            freq[s] = freq.get(s, 0) + 1

        for ln in lines:
            s = ln.strip()
            low = s.lower()
            if not s:
                continue
            if re.search(r"page\s*\d+|\bpage\b|\brfp\b|\bproprietary and confidential\b", low):
                continue
            if freq.get(s, 0) > 5 and len(s) < 80:
                continue
            cleaned_lines.append(s)

        t2 = " ".join(cleaned_lines)
        t2 = re.sub(r"\s+", " ", t2).strip().lower()
        return t2

    # -------------------------------------------------------------------------
    # Deterministic Application Submission Requirements extraction
    # (unchanged internals preserved)
    # -------------------------------------------------------------------------
    def _extract_application_requirements(self, text: str) -> List[Requirement]:
        results: List[Requirement] = []

        app_match = re.search(
            r"1\.\s*Application Submission Requirements(.*?)(\n\s*2\.\s*Guidelines for Preparations and Submission of Proposals|\Z)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if not app_match:
            return results

        app_block = app_match.group(0)

        tech_match = re.search(
            r"a\)\s*Technical Proposal(.*?)(b\)\s*Financial Proposal|$)",
            app_block,
            re.DOTALL | re.IGNORECASE,
        )
        if tech_match:
            tech_block = tech_match.group(1)
            tech_items = self._extract_roman_bullets(tech_block)
            for item in tech_items:
                cleaned = self._clean_requirement_text(item)
                if len(cleaned) > 10:
                    results.append(
                        Requirement(
                            req_id="",
                            requirement_text=cleaned,
                            category="Technical Proposal",
                            mandatory=True,
                            keywords=[],
                        )
                    )

        fin_match = re.search(
            r"b\)\s*Financial Proposal(.*?)(\n\s*2\.\s*Guidelines for Preparations and Submission of Proposals|\Z)",
            app_block,
            re.DOTALL | re.IGNORECASE,
        )
        if fin_match:
            fin_block = fin_match.group(1)
            fin_items = self._extract_roman_bullets(fin_block)
            for item in fin_items:
                cleaned = self._clean_requirement_text(item)
                if len(cleaned) > 10:
                    results.append(
                        Requirement(
                            req_id="",
                            requirement_text=cleaned,
                            category="Financial Proposal",
                            mandatory=True,
                            keywords=[],
                        )
                    )

        guide_match = re.search(
            r"2\.\s*Guidelines for Preparations and Submission of Proposals(.*?)(\n\s*2\.1|\Z)",
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if guide_match:
            guide_block = guide_match.group(1)
            guide_items = self._extract_letter_bullets(guide_block)
            for item in guide_items:
                cleaned = self._clean_requirement_text(item)
                if len(cleaned) > 10:
                    results.append(
                        Requirement(
                            req_id="",
                            requirement_text=cleaned,
                            category="Guidelines",
                            mandatory=True,
                            keywords=[],
                        )
                    )

        return results

    def _extract_roman_bullets(self, block: str) -> List[str]:
        lines = block.splitlines()
        items: List[str] = []
        current = None

        roman_re = re.compile(r"^(i{1,3}|iv|v|vi{0,3}|ix|x)\.\s*(.*)", re.IGNORECASE)

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            m = roman_re.match(stripped)
            if m:
                if current:
                    items.append(current.strip())
                current = m.group(2).strip()
            else:
                if current is not None:
                    if not any(footer in stripped.lower() for footer in [
                        "proprietary and confidential", "rfp agra-nb-1346", "/2025"
                    ]):
                        current += " " + stripped

        if current:
            items.append(current.strip())

        return items

    def _extract_letter_bullets(self, block: str) -> List[str]:
        lines = block.splitlines()
        items: List[str] = []
        current = None

        letter_re = re.compile(r"^([a-z])\.\s*(.*)", re.IGNORECASE)

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            m = letter_re.match(stripped)
            if m:
                if current:
                    items.append(current.strip())
                current = m.group(2).strip()
            else:
                if current is not None:
                    if not any(footer in stripped.lower() for footer in [
                        "proprietary and confidential", "rfp agra-nb-1346", "/2025"
                    ]):
                        current += " " + stripped

        if current:
            items.append(current.strip())

        return items

    def _clean_requirement_text(self, text: str) -> str:
        t = text.strip()
        t = re.sub(r"\d+\s+\d{4}/\d{2}/\d{2}.*$", "", t)
        t = re.sub(r"\s+", " ", t)
        t = t.strip(" .")
        return t.strip()

    # -------------------------------------------------------------------------
    # Chunking (unchanged baseline)
    # -------------------------------------------------------------------------
    def _chunk(self, text: str) -> List[str]:
        paras = text.split("\n\n")
        chunks, curr = [], ""
        for p in paras:
            if len(curr) + len(p) <= 1000:
                curr += p + "\n\n"
            else:
                if curr.strip():
                    chunks.append(curr.strip())
                curr = p + "\n\n"
        if curr.strip():
            chunks.append(curr.strip())
        return [c for c in chunks if len(c) > 100]

    # -------------------------------------------------------------------------
    # Agreement / contract section extraction (unchanged)
    # -------------------------------------------------------------------------
    def _extract_agreement_section(self, text: str) -> str:
        m = re.search(r"(THIS AGREEMENT.*)", text, re.DOTALL | re.IGNORECASE)
        if m:
            section = m.group(1)
            section = section[:15000]
            print(f"📌 Agreement section detected (len={len(section)})")
            return section
        return ""

    # -------------------------------------------------------------------------
    # LLM extraction (unchanged)
    # -------------------------------------------------------------------------
    def _llm_extract(self, text: str, agreement_mode: bool = False) -> List[Requirement]:
        section_hint = (
            "You are now reading the Agreement / contract section. "
            "Most requirements here should be categorized as \"Contract / Legal\".\n"
            if agreement_mode
            else "You are now reading the proposal / submission parts of the tender.\n"
        )

        sys_msg = f"""You are a procurement expert. Extract ONLY requirements from the tender document.

{section_hint}
A "requirement" is any statement that defines something the bidder or consultant
MUST do, MUST provide, MUST comply with, or how the proposal MUST be structured.

This includes:
- Sentences using words like: shall, must, required, mandatory, should, will, needs to.
- Items in numbered or bulleted lists under headers like
  "Application Submission Requirements", "Technical Proposal", "Financial Proposal",
  "Guidelines for Preparation and Submission of Proposals", "Scope of Work",
  even if they don't explicitly say "shall" or "must".
- Contractual obligations on the Consultant or AGRA defined in the Agreement / contract section.

CATEGORIES:
Use ONLY the following category values:
- "Technical Proposal"   → for technical / content / methodology / team requirements.
- "Financial Proposal"   → for pricing, fees, taxes, financial structure.
- "Guidelines"           → for instructions under 'Guidelines for Preparation and Submission of Proposals'
                           or similar guidance sections.
- "Contract / Legal"     → for obligations defined in the Agreement / contract (e.g. deliverables, standards,
                           confidentiality, IP, termination, indemnity, compliance clauses).
- "General"              → for anything that does not clearly fit the above.

When deciding the category:
- Look at the heading or context above the sentence (e.g., if it is under 'Application Submission Requirements - Technical Proposal',
  then category is "Technical Proposal").
- If under 'Application Submission Requirements - Financial Proposal', use "Financial Proposal".
- If under 'Guidelines for Preparation and Submission of Proposals', use "Guidelines".
- If in the Agreement body (e.g. 'THIS AGREEMENT', 'The Consultant shall…'), use "Contract / Legal".

IMPORTANT:
- Treat each bullet or numbered list item as a SEPARATE requirement when it describes
  a distinct obligation or piece of information.
- Do NOT merge multiple bullets into one requirement.
- Most of these are mandatory → set mandatory: true unless the text clearly says 'optional', 'may', or 'at discretion'.

Return ONLY valid JSON:
{{
  "requirements": [
    {{
      "requirement_text": "...",
      "category": "Technical Proposal",
      "mandatory": true,
      "keywords": []
    }}
  ]
}}

If no requirements, return: {{"requirements": []}}"""

        user_msg = f"""From this text, extract only requirements:\n\n{text}\n\nReturn ONLY JSON, no other text."""

        try:
            print("   📤 Sending to OpenAI...")
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.0,
                top_p=0.0,
                n=1,
                max_tokens=3000,
            )

            content = resp.choices[0].message.content

            if not content or not content.strip():
                print("   ❌ Empty response from LLM")
                return []

            print(f"   📥 Got response: {content[:100]}...")

            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    print("   ❌ No valid JSON found")
                    return []

            reqs: List[Requirement] = []
            for r in data.get("requirements", []):
                req_text = r.get("requirement_text", "").strip()
                if len(req_text) > 20:
                    category = r.get("category", "General")
                    if category not in [
                        "Technical Proposal",
                        "Financial Proposal",
                        "Guidelines",
                        "Contract / Legal",
                        "General",
                    ]:
                        category = "General"

                    cleaned = self._clean_requirement_text(req_text)

                    reqs.append(
                        Requirement(
                            req_id="",
                            requirement_text=cleaned,
                            category=category,
                            mandatory=r.get("mandatory", True),
                            keywords=r.get("keywords", []),
                        )
                    )

            print(f"   ✅ Extracted {len(reqs)} requirements")
            return reqs

        except Exception as e:
            print(f"   ❌ OpenAI error: {type(e).__name__}: {e}")
            return []

    def _llm_extract_fallback(self, text: str) -> List[Requirement]:
        sys_msg = """Extract requirements from this tender document.

Use ONLY these categories:
- "Technical Proposal"
- "Financial Proposal"
- "Guidelines"
- "Contract / Legal"
- "General"

Return JSON:
{"requirements": [{"requirement_text": "...", "category": "General", "mandatory": true, "keywords": []}]}"""

        user_msg = f"""Tender:\n\n{text}\n\nExtract requirements. Return JSON only."""

        try:
            print("   📤 Fallback: Sending to OpenAI...")
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.0,
                top_p=0.0,
                n=1,
                max_tokens=3000,
            )

            content = resp.choices[0].message.content

            if not content or not content.strip():
                print("   ⚠️ Fallback: Empty response")
                return []

            print(f"   📥 Got: {content[:100]}...")

            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    print("   ⚠️ Fallback: No valid JSON")
                    return []

            reqs: List[Requirement] = []
            for r in data.get("requirements", []):
                req_text = r.get("requirement_text", "").strip()
                if len(req_text) > 20:
                    category = r.get("category", "General")
                    if category not in [
                        "Technical Proposal",
                        "Financial Proposal",
                        "Guidelines",
                        "Contract / Legal",
                        "General",
                    ]:
                        category = "General"

                    cleaned = self._clean_requirement_text(req_text)

                    reqs.append(
                        Requirement(
                            req_id="",
                            requirement_text=cleaned,
                            category=category,
                            mandatory=r.get("mandatory", True),
                            keywords=r.get("keywords", []),
                        )
                    )

            print(f"   ✅ Fallback: {len(reqs)} requirements")
            return reqs

        except Exception as e:
            print(f"   ⚠️ Fallback error: {type(e).__name__}: {e}")
            return []

    def _dedup(self, reqs: List[Requirement]) -> List[Requirement]:
        """
        Smarter de-duplication:
        - Normalizes whitespace and strips trailing date/footer junk
        - Removes exact duplicates
        - If one requirement is a substring of another, keep the LONGER one
        - If two requirements are near-duplicates (fuzzy similarity > 0.88),
          keep the longer / richer one.
        """
        from difflib import SequenceMatcher

        def norm_core(s: str) -> str:
            s = s.lower().strip()
            # Remove trailing date artifact like "7 2025/07/14 9:56 AM ..."
            s = re.sub(r"\d+\s+\d{4}/\d{2}/\d{2}.*$", "", s)
            # Collapse whitespace
            s = re.sub(r"\s+", " ", s)
            return s.strip()

        unique: List[Requirement] = []
        norms: List[str] = []

        for r in reqs:
            text = r.requirement_text.strip()
            if len(text) <= 20:
                continue

            n = norm_core(text)
            if not n:
                continue

            replaced = False
            remove_idx = None

            for idx, existing_norm in enumerate(norms):
                # Exact duplicate
                if n == existing_norm:
                    replaced = True
                    break

                # Substring-based duplicate: keep longer one
                if n in existing_norm or existing_norm in n:
                    # Keep the longer textual form
                    if len(n) > len(existing_norm):
                        remove_idx = idx
                    replaced = True
                    break

                # Fuzzy similarity check for near-duplicates
                # (conservative threshold to avoid merging distinct items)
                sim = SequenceMatcher(None, n, existing_norm).ratio()
                if sim >= 0.88:
                    # if new one is longer / richer, replace; otherwise keep existing
                    if len(n) > len(existing_norm):
                        remove_idx = idx
                    replaced = True
                    break

            if replaced:
                if remove_idx is not None:
                    # replace the existing item with the new richer one
                    unique[remove_idx] = r
                    norms[remove_idx] = n
                # else we skip adding because it's duplicate or similar but shorter
                continue

            unique.append(r)
            norms.append(n)

        print(f"🧹 De-duplication reduced {len(reqs)} → {len(unique)} requirements")
        return unique


    # -------------------------------------------------------------------------
    # ------------------- New helper methods for Hybrid retrieval --------------
    # -------------------------------------------------------------------------
    def _detect_high_value_sections(self, text: str, top_m: int = 6) -> List[str]:
        """
        Generic heading/section detector:
        - Find candidate heading lines (ALL CAPS, starts with SECTION/PART, or numbered headings)
        - For each heading, capture content until next heading
        - Score by presence of heading keywords
        - Return top_m sections content (preserve their original text)
        """
        lines = text.splitlines()
        candidate_indices = []

        # Identify heading line indices heuristically
        for i, ln in enumerate(lines):
            s = ln.strip()
            if not s:
                continue
            # heuristic: starts with SECTION/PART or numbered heading "1." or is mostly uppercase and meaningful length
            if re.match(r'^(SECTION|PART)\b', s, re.IGNORECASE):
                candidate_indices.append(i)
                continue
            if re.match(r'^\d+\.\s*\w+', s):  # "1. Application..."
                candidate_indices.append(i)
                continue
            # all-caps heuristic (consider it a heading if at least length>6 and >70% uppercase letters)
            letters = re.sub(r'[^A-Za-z]', '', s)
            if letters and len(letters) > 6:
                upper_ratio = sum(1 for ch in letters if ch.isupper()) / len(letters)
                if upper_ratio > 0.7:
                    candidate_indices.append(i)
                    continue

        # If no candidate headings, return empty
        if not candidate_indices:
            return []

        # Build sections as heading -> content until next heading (or end)
        sections = []
        for idx_pos, heading_idx in enumerate(candidate_indices):
            start = heading_idx
            end = candidate_indices[idx_pos + 1] if (idx_pos + 1) < len(candidate_indices) else len(lines)
            heading = lines[heading_idx].strip()
            content = "\n".join(lines[start:end]).strip()
            sections.append({"heading": heading, "content": content, "start_idx": start})

        # Score sections by presence of keywords in heading + content
        keywords = [
            "require", "submission", "evaluation", "qualification", "scope",
            "technical", "financial", "proposal", "deliverable", "deliverables",
            "terms", "conditions", "mandatory", "eligibility", "criteria"
        ]
        scored = []
        for s in sections:
            score = 0
            h_low = s["heading"].lower()
            c_low = s["content"].lower()
            for kw in keywords:
                if kw in h_low:
                    score += 3
                if kw in c_low:
                    score += 1
            # bonus if heading explicitly mentions "Application Submission" or "Guidelines"
            if re.search(r'application submission|guidelines for preparation|guidelines for preparations', s["heading"], re.IGNORECASE):
                score += 5
            scored.append((score, s))

        # Keep top_m sections by score (filter out zero-scored)
        scored = [t for t in scored if t[0] > 0]
        scored.sort(key=lambda x: (-x[0], x[1]["start_idx"]))
        top_sections = [s["content"] for score, s in scored[:top_m]]
        return top_sections

    def _semantic_retrieve_indices(self, embeds: np.ndarray, chunk_meta: List[Dict]) -> List[int]:
        """
        Run semantic queries, retrieve top_k per query, combine unique indices.
        """
        collected = []
        for q in self.semantic_queries:
            q_emb = self.emb_model.encode(q, convert_to_numpy=True)
            _, idx = self.index.search(np.array([q_emb], dtype=np.float32), k=self.top_k_per_query)
            for i in idx[0]:
                if 0 <= i < len(chunk_meta) and i not in collected:
                    collected.append(int(i))
        return collected

    def _filter_and_cap_indices(self, indices: List[int], chunk_meta: List[Dict], cap: int = 40) -> List[int]:
        """
        Filter out front-matter/TOC-like chunks and cap the selection.
        Heuristics for filtering:
         - chunk length < 100 chars
         - chunk contains 'table of contents' or 'contents' near top
         - chunk mostly numbers / page numbers
        """
        filtered = []
        for i in indices:
            text = chunk_meta[i]["text"].strip()
            low = text.lower()
            # length check
            if len(text) < 100:
                continue
            # Table of contents / front matter
            if "table of contents" in low or re.match(r'^\s*contents\b', low):
                continue
            # only numbers / page numbers
            stripped = re.sub(r'\s+', '', re.sub(r'[^0-9\s]', '', text))
            if len(stripped) > 0 and (len(stripped) / max(1, len(text)) > 0.6):
                continue
            filtered.append(i)

        # If filtered is empty fallback to original indices but cap
        if not filtered:
            filtered = indices[:cap]

        # Preserve original order but cap
        filtered = sorted(list(dict.fromkeys(filtered)))  # dedup, preserve order via dict
        return filtered[:cap]

    def _semantic_group_adjacent(self, selected_indices: List[int], chunk_meta: List[Dict], embeds: np.ndarray) -> List[str]:
        """
        Merge adjacent chunks (in document order) if cosine similarity of their embeddings exceeds threshold.
        Only merge adjacent indices (conservative), ensure merged chunk not too large.
        Returns list of chunk texts (merged where applied), in order.
        """
        # Compute normalized embeddings for cosine quickly
        if embeds is None or embeds.shape[0] == 0:
            return [chunk_meta[i]["text"] for i in selected_indices]

        # Precompute norms
        norms = np.linalg.norm(embeds, axis=1) + 1e-12

        results = []
        buffer_text = None
        buffer_len = 0

        # iterate through sorted indices
        for pos, idx in enumerate(selected_indices):
            cur_text = chunk_meta[idx]["text"]
            if buffer_text is None:
                buffer_text = cur_text
                buffer_len = len(cur_text)
                last_idx = idx
                continue

            # check adjacency (we only merge if current idx is immediately after last_idx)
            if idx == last_idx + 1:
                # compute cosine similarity between embeddings[last_idx] and embeddings[idx]
                v1 = embeds[last_idx]
                v2 = embeds[idx]
                sim = float(np.dot(v1, v2) / ((norms[last_idx] * norms[idx]) + 1e-12))
                if sim >= self.semantic_grouping_threshold and (buffer_len + len(cur_text)) <= self.max_merged_chars:
                    # merge
                    buffer_text = buffer_text + "\n\n" + cur_text
                    buffer_len += len(cur_text)
                    last_idx = idx
                    continue
                else:
                    # flush buffer, start new
                    results.append(buffer_text)
                    buffer_text = cur_text
                    buffer_len = len(cur_text)
                    last_idx = idx
            else:
                # non-adjacent: flush and start new
                results.append(buffer_text)
                buffer_text = cur_text
                buffer_len = len(cur_text)
                last_idx = idx

        if buffer_text is not None:
            results.append(buffer_text)

        return results

    # -------------------------------------------------------------------------
    # End of extractor
    # -------------------------------------------------------------------------


    # -------------------------------------------------------------------------
    # ------------------- New helper methods for Hybrid retrieval --------------
    # -------------------------------------------------------------------------
        # ----------------------------
    # Page-aware extraction helper
    # ----------------------------
    def extract_with_page_map(self, filepath: str) -> Tuple[str, Dict[int, int]]:
        """
        Extract full text AND build a sentence index → page number map.
        Returns:
          - full_text (str)
          - page_map: {sentence_index: page_number}
        """
        import fitz
        import docx
        import re

        ext = filepath.lower().split(".")[-1]
        full_text = ""
        page_map = {}
        sentence_idx = 0

        if ext == "pdf":
            with fitz.open(filepath) as doc:
                for page_num, page in enumerate(doc, start=1):
                    page_text = page.get_text()
                    sentences = re.split(r"(?<=[.!?])\s+", page_text)
                    # 🔽 TABLE PARSING (PAGE-AWARE)
                    try:
                        tables = page.find_tables()
                        for table in tables:
                            for row in table.extract():
                                cells = [str(c).strip() for c in row if c and str(c).strip()]
                                if len(cells) >= 2:
                                    sentence = " | ".join(cells)
                                    page_map[sentence_idx] = page_num
                                    full_text += sentence + ". "
                                    sentence_idx += 1
                    except Exception:
                        pass

                    for s in sentences:
                        clean = s.strip()
                        if len(clean) > 25:
                            page_map[sentence_idx] = page_num
                            sentence_idx += 1
                            full_text += clean + " "
        elif ext == "docx":
            doc = docx.Document(filepath)
            page_num = 1  # DOCX has no real pages → logical fallback
            for p in doc.paragraphs:
                sentences = re.split(r"(?<=[.!?])\s+", p.text)
                for s in sentences:
                    clean = s.strip()
                    if len(clean) > 25:
                        page_map[sentence_idx] = page_num
                        sentence_idx += 1
                        full_text += clean + " "
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                full_text = f.read()

        return full_text, page_map