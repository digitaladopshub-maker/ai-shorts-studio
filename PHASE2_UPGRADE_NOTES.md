# AI Shorts Studio — Phase 2 Upgrade Notes

## Phase 2: Context-aware transcript ranking

The Auto-Split AI ranker has been upgraded from basic hook/emotion/duration heuristics to a broader, explainable transcript-window scoring model.

### New scoring signals
- Hook and curiosity language.
- Emotional language and questions.
- Speech density and target-duration fit.
- Enough transcript context for a self-contained short.
- Beginning/ending completeness, including penalties for obvious sentence fragments.
- Wording coherence and repeated/filler-word penalties.
- Whisper speech confidence using `avg_logprob` and `no_speech_prob` when available.

### UI changes
- Analysis section now shows an AI Selection Score and time range for each candidate.
- Each candidate can be expanded to review its transcript excerpt, top selection signals and individual factor scores.
- The UI explicitly describes the score as transcript-based and does not promise virality.

### Compatibility and cost
- No new dependencies or paid APIs were added.
- Uses existing local Whisper output and Python standard library.
- Existing manual clipping, subtitle generation, effects, face tracking and Live Streaming code were retained.
- `streaming_page.py` was not modified.

### Limitations
- This is a transparent heuristic scoring system, not an LLM or deep semantic model.
- It cannot reliably understand sarcasm, visual context, speaker intent, factual correctness or audience retention.
- Whisper confidence is a transcription-quality hint, not a measure of whether a moment is interesting.
- Active-speaker detection and multi-person tracking are not part of Phase 2.
- Streamlit Community Cloud free CPU/RAM and ephemeral storage limits still apply.

### Validation
- Python compilation passed for app, clipping, face tracking, AI ranker, streaming page and tests.
- Phase 1 helper tests passed.
- New Phase 2 checks passed for completeness and Whisper confidence scoring.
- Full hosted Streamlit/Whisper end-to-end runtime was not executed in this environment.
