# Release process

1. Ensure `main` is green in CI.
2. Update `CHANGELOG.md`, `KNOWN_ISSUES.md`, and relevant documentation.
3. Run checks locally.
4. Create a signed or annotated tag: `git tag -a v0.4.0 -m "JobHunt MU v0.4.0"`.
5. Push the tag and create a GitHub Release.
6. Include summary, migration instructions, security notes, breaking changes, and rollback steps.
7. Attach no databases, resumes, secrets, or third-party datasets.

## Release-note template

```markdown
## Highlights
## Added
## Changed
## Fixed
## Security
## Database migrations
## Upgrade instructions
## Known issues
## Contributors
```
