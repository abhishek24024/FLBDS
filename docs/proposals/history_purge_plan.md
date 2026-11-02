# Git History Purge Plan: Proprietary Excerpts and Review Packets

## 1. Overview and Rationale
The GitHub repository `abhishek24024/FLBDS` is public (`"visibility": "public"`, verified via GitHub API). In earlier audit commits (specifically `950ce25`), literal abstract excerpts from non-CC-BY literature (e.g., Shi et al., 2015, *Science*, DOI: `10.1126/science.aab3564`) and review packets were committed to version control. While current working trees replace these excerpts with DOIs and mathematical parameters, git history retains earlier commits containing these texts.

Under the project standing rules, git history must not be rewritten without prior authorization and an explicit, verified execution procedure. This document outlines the exact paths, strings, commands, and backup/re-clone procedures.

---

## 2. Inventory of Targets

### A. Exact File Paths to Purge from History
The following files were previously committed and must be completely removed from all historical commits:
1. `docs/audit/blind_screening_packet_user.md` (committed in `950ce25`, removed from tree in `5e19f6a`)
2. `docs/audit/review_packet_20_blind.md` (if referenced in earlier branches/stashes)
3. `flbds_data/` (ensure no transient data path is retained in any past tree)

### B. Literal Text Strings to Redact / Replace
The following literal text strings from non-open-access sources must be purged or replaced across all historical commits (e.g., in `docs/audit/handover_verification.md` and `scripts/generate_handover_verification.py`):
- **String 1 (Shi et al. 2015 abstract excerpt)**:
  `"Saharan silver ants foraging in midday sun"` or any verbatim sentences from Science 2015 paper.
  *Replacement*: DOI reference `10.1126/science.aab3564` and solution-neutral physical mechanism description.
- **String 2 (Unverified screening/packet passages)**:
  Any unredacted blind screening packets or ungrounded card review passages.

---

## 3. Preparation and Safety Backup Procedure

Before executing any history rewriting command, create redundant full backups:

```bash
# Step 1: Create a full mirror clone / git bundle backup on local machine
cd /Users/abhishektripathi/Desktop
git clone --mirror FLBDS FLBDS_backup_mirror.git
git -C FLBDS bundle create FLBDS_pre_purge_backup.bundle --all

# Step 2: Backup remote server repository
ssh -i ~/.ssh/bio_server abhishek24024@192.168.2.69 \
  "cp -r /home/abhishek24024/flbds /home/abhishek24024/flbds_backup_pre_purge"
```

---

## 4. `git-filter-repo` Execution Commands

Using the standard, lossless tool `git-filter-repo` (recommended over legacy `git filter-branch`):

```bash
# Ensure working tree is clean and on main
cd /Users/abhishektripathi/Desktop/FLBDS

# 1. Purge specific committed packet files from all commits
git filter-repo --invert-paths --path docs/audit/blind_screening_packet_user.md

# 2. Text replacement expressions (expressions file: /tmp/history_replacements.txt)
cat << 'EOF' > /tmp/history_replacements.txt
# Replace non-CC-BY abstract quotes with canonical DOIs
regex:(?i)Keeping cool: Enhanced optical reflection and radiative heat dissipation in Saharan silver ants==>Shi et al. (2015) [DOI: 10.1126/science.aab3564]
EOF

git filter-repo --replace-text /tmp/history_replacements.txt
```

---

## 5. Post-Purge Verification, Remote Force-Push, and Server Re-Clone

1. **Verify Local Integrity**:
   ```bash
   git log -S "blind_screening_packet_user" --all  # MUST return empty
   pytest tests/                                  # All 107 tests MUST pass
   ```

2. **Re-add Remote and Force-Push**:
   ```bash
   git remote add origin git@github.com:abhishek24024/FLBDS.git
   git push origin main --force --tags
   ```

3. **Re-sync Compute Server**:
   ```bash
   # On 192.168.2.69:
   cd /home/abhishek24024
   rm -rf flbds
   git clone git@github.com:abhishek24024/FLBDS.git flbds
   # Verify tests on server:
   cd flbds && /home/abhishek24024/flbds_env/bin/pytest
   ```
