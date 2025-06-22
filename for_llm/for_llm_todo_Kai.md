# Todo List for Kai
# Last Updated: 2025-01-19T10:00:01Z

## Project Improvement Initiative

- [x] 1. Create root `README.md`
- [x] 2. Update `.gitignore` to exclude `.benchmarks/` directory
- [x] 3. Create missing `FOLDER_GUIDE.md` files for:
  - [x] `/.github`
  - [x] `/.github/workflows`
  - [x] `/docs`
  - [x] `/tests`
- [x] 4. Review and improve `.github/workflows/ci.yml` (No improvements needed, already excellent)
- [x] 5. Update Linear project with latest status
- [x] 6. Create Linear issues for improvement tasks

## Critical Bug Fixes (High Priority)

- [ ] 7. Fix ReviewQueue datetime parsing issues in `from_row` method
- [ ] 8. Fix API mismatches between tests and implementation:
  - [ ] 8a. Tests expect `add_file` but implementation uses `add_item`
  - [ ] 8b. Tests expect `add_files` but GitRepo uses `add_all`
  - [ ] 8c. Fix CommitWorker constructor parameter mismatches
- [ ] 9. Fix missing attributes in classes:
  - [ ] 9a. GitRepo missing `repo_path` attribute
  - [ ] 9b. LLMConfig missing `rstrip` method
- [ ] 10. Fix database schema and file permission issues in tests
- [ ] 11. Fix integration test failures and missing imports

## Implementation Completion

- [ ] 12. Complete the file monitoring and commit workflow integration
- [ ] 13. Implement proper error handling and fallback mechanisms
- [ ] 14. Add comprehensive logging and monitoring
- [ ] 15. Create user documentation and usage examples

## Testing and Quality Assurance

- [ ] 16. Ensure all tests pass with proper test isolation
- [ ] 17. Add integration tests for the complete workflow
- [ ] 18. Add performance tests for large file sets
- [ ] 19. Add error handling and recovery tests 