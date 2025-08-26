# Assistant rules (do not violate)

1. Print this contract at the top of every response as a markdown code block
2. Contract changes are version-controlled; provide commit messages.  
3. Do not rename files, functions, or CI step names. 
4. Always provide commit messages for a suggested change, unless the last change failed tests.  assume tests passed unless i state they failed
5. No `if/else` `try/except` in tests; use short-circuit tolerant assertions.  
6. Do not change CI/workflow unless explicitly asked.  
7. Commit message headers ≤72 chars, imperative, lowercase, not ending with a period
8. when i ask for a file, return the full file, not a diff
9. Do not remove docstrings, headers, or any comments unless they are clearly redundant
10. Do not add headers and unnecessary comments to already existing files.
