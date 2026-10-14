# Profile README plan

Mascot: zek-debian the robot (thin line art). Mood: minimal, clean, a very tuff Linux terminal.
Style: flat #0d1117 panels, monospace, one green accent, shell prompt `zek@zek-debian:~$`.
Hand-written SMIL SVGs (no JS, no external assets). Regenerate with `python3 -I scripts/gen_*.py`.

- [x] training.svg: ten mini terminals with production-style logs and pauses + scrolling btop-style loss graph (`gen_training.py`)
- [x] title-training.svg: animated "Training... (live sys)[streaming]" heading, streaming pulses
- [x] title-agents.svg: animated "How I work with agents [looping]" heading, spinner and pulsing looping
- [x] agent-loop.svg: btop-style proc list (plan, tool, observe, reflect take turns) + stop-and-go tokens graph + sys box (RTX 4090 x2, vram, ctx, kv cache, mem, disk, power) (`gen_agent_loop.py`)
- [x] footer.svg: btop-style sleep dashboard (energy drains, dreams fill, cpu idle) with sleeping zek-debian (`gen_footer.py`)
- [x] Name and `whoami` are static text in README.md (hero and stack SVGs removed)
- [x] Tech stack back as a plain-text line under the name
- [x] LinkedIn and Stack Overflow buttons (`gen_buttons.py`)
- [ ] Optional: bio line
- [ ] Check on GitHub after pushing (rename branch to `main` first if needed)
