# Assistant rules (do not violate)
1. Always print the current contract at the top of responses.  
2. If I suggest changes to the contract, treat it as version-controlled: provide a commit message for the update.  
3. Do not rename existing files, tests, or CI step names.  
4. Do not suggest commit messages unless tests have just passed.  
5. Tests must not contain `if/else`; prefer short-circuit tolerant assertions.  
6. Keep CI and workflow files unchanged unless explicitly requested.  
7. Treat any failing test output as “previous message revoked.”  
