# Drafting guide (style + section template)

## Normative language
- **shall** = mandatory. **should** = recommended; deviation needs a reason.
- **may** = permitted. **can** = capability, never a requirement.
- Never use "must", "has to", "needs to", "is required to" or "will"
  for requirements; use "shall".
- One requirement per sentence, so each can be checked on its own.

## Voice
- Present tense, active voice, plain words. Short sentences.
- Address the role, not "you": "The integrator shall...".
- Explain the reason in a separate rationale paragraph, not inside the
  requirement sentence.

## Terms and names
- Use the preferred term from `glossary.txt` exactly. Define new terms
  in the Terminology chapter and add them to `glossary.txt`.
- Product names exactly as the vendor writes them (EcoStruxure Control
  Expert, Ignition Perspective, Modicon M580).
- Data types in `\texttt{}` (e.g. \texttt{DDT\_Device}).

## Formatting
- Requirements as numbered lists so they can be cited (e.g. 7.3.2).
- Tables for hardware lists, type members and parameter limits.
- `\label` every chapter, section and table: `sec:`, `tab:`, `fig:`.
- Cross-reference with `\ref`/`\autoref`; never write a section number by
  hand.
- New content in a revision is wrapped in `\newtag{}` until release.

# Section template

```latex
\section{<Title>}\label{sec:<slug>}

\subsection*{Purpose}
<One or two sentences: what this section controls and why.>

\subsection*{Scope}
<What it applies to; what it explicitly does not cover.>

\subsection*{Requirements}
\begin{enumerate}
  \item <Role> shall <single verifiable requirement>.
  \item <Role> should <recommendation>.
\end{enumerate}

\subsection*{Rationale}
<Why. Cite the incident, project or type that drove it.>

\subsection*{Example}
<Concrete case from an active project (e.g. R23 columns) or a real
type definition. Prefer tables over prose.>

\subsection*{References}
<Related sections via \ref, external standards (NFPA 79, UL 508A),
type library files.>
```

Omit Example or References only when there is genuinely nothing to put
there. Keep Purpose and Scope short; the requirements are the content.
