# `check-v1` – variant `opus-check`

Model: `claude-opus-5-5` (the main Claude Code session, owner's request 2026-11-13), reading high-resolution crops of
the original photos (EXIF applied, grayscale, turned upright, 1600 px wide) around the places the `sonnet` reading
marked `[?]` or the model flagged as uncertain. Each record is the `sonnet` text with the checked places corrected,
except scan 128, transcribed whole with the `reread-v1` rules.

Changes against `sonnet`:

- 23: running header "TANEC SLUNCÍ" -> "TANEC SLUNCI" (as on every other page);
- 66: note 36, page "[?]" -> "31";
- 90: "nákup ně[?] symbolů" -> "nákup symbolů", "všechno jak prázdné..." -> "všechno nějak prázdné…" (the
  hyphenated "ně-jak" had been moved to the wrong line);
- 115: "z toho plyne" -> "Z toho plyne", "doktrína [?] (" -> "doktrína (" (rest of the paragraph confirmed);
- 128: page 148, new transcription (the `sonnet` record had the text of page 134 by a mix-up of two test images);
- 130: clause order restored: "se stroji, nebo se s nimi dokonce spojíme, nikoli jako hrozbu, ale jako příležitost";
- 181: "[?] jen úzce" -> "vedené jen úzce" (the photo shows "…edené", the first letter hidden in the fold; page 202
  ends "by mělo být");
- 206: "rYXeQbTuV[?]0" -> "rYXeQbTuVl0".

Confirmed without change: 86 (21 notes, numbers 17–37 between note 16 on page 102 and note 38 on page 104), 117,
131. Left as `[?]`: 4 (a word under a finger), 71 (two words blurred by motion), 37 and 44 (page numbers cut off;
the order gives 52 and 60).
