# Git commit and push

Commit all changes with a short 1-2 sentence message and push to the remote.

## Steps

1. Run `git status` to see what has changed.
2. Run `git diff` (and `git diff --staged` if needed) to understand the changes.
3. Write a commit message that is strictly one or two sentences only. No bullet points, no multi-line body. Single line preferred; two sentences max if needed.
4. Run `git add -A` to stage all changes.
5. Run `git commit -m "Your message here"` with the message you wrote. Use a single -m flag with one or two sentences only.
6. Run `git push` to push to the remote.

If the user provides a commit message when invoking this command, use that (still keep it to 1-2 sentences). Otherwise, generate a single-sentence message from the diff. Never use bullet points or a multi-line body.

Do not use `--no-verify` or skip hooks unless the user explicitly asks. If the push fails, report the error clearly.
