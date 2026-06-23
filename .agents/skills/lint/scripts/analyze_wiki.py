import os
import re
import unicodedata
from datetime import datetime

def clean_str(s):
    return unicodedata.normalize('NFC', s)

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "..", ".."))
wiki_dir = os.path.join(base_dir, "wiki")
sources_dir = os.path.join(base_dir, "sources")
attachments_dir = os.path.join(sources_dir, "attachments")
index_path = os.path.join(base_dir, "index.md")
current_date = datetime.now()

def parse_frontmatter(fm_text):
    fm = {}
    for line in fm_text.strip().split("\n"):
        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip()
            val = parts[1].strip()
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            fm[key] = val
    return fm

# 1. Scan files
wiki_files = []
for root, dirs, files in os.walk(wiki_dir):
    for f in files:
        if f.endswith(".md"):
            wiki_files.append(os.path.join(root, f))

all_md_files = [index_path] + wiki_files
for root, dirs, files in os.walk(sources_dir):
    for f in files:
        if f.endswith(".md"):
            all_md_files.append(os.path.join(root, f))

# 2. Map all existing wiki pages (basename without .md -> path)
wiki_map = {}
for fpath in wiki_files:
    bname = os.path.basename(fpath)
    name_without_ext = os.path.splitext(bname)[0]
    wiki_map[clean_str(name_without_ext).lower()] = fpath

# Track links
dead_links = []
incoming_links = {name.lower(): [] for name in wiki_map.keys()}

# Frontmatter and decay tracking
confidence_decays = []

for fpath in wiki_files:
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Parse YAML frontmatter
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        try:
            fm = parse_frontmatter(fm_text)
            confidence = fm.get("confidence")
            last_confirmed = fm.get("last_confirmed")
            if confidence is not None and last_confirmed is not None:
                try:
                    conf_val = float(confidence)
                    if conf_val < 1.0:
                        last_confirmed_date = datetime.strptime(str(last_confirmed).strip(), "%Y-%m-%d")
                        days_elapsed = (current_date - last_confirmed_date).days
                        intervals = days_elapsed // 180
                        if intervals >= 1:
                            decay = intervals * 0.1
                            new_conf = max(0.0, conf_val - decay)
                            confidence_decays.append({
                                "file": fpath,
                                "old_conf": conf_val,
                                "new_conf": round(new_conf, 2),
                                "last_confirmed": last_confirmed_date.strftime("%Y-%m-%d"),
                                "days_elapsed": days_elapsed
                            })
                except Exception as e:
                    pass
        except Exception as e:
            pass
            
    # Find all Wikilinks
    wikilinks = re.findall(r"\[\[([^\]]+)\]\]", content)
    for link in wikilinks:
        target = clean_str(link.split("|")[0].strip())
        # Split by '#' to remove section anchors (e.g. [[NoteName#Section]] -> NoteName)
        target_file = clean_str(target.split("#")[0].strip())
        resolved = False
        target_lower = target_file.lower()
        
        if target_lower.startswith("wiki/"):
            clean_target = target_file[5:]
            if clean_target.lower() in wiki_map:
                resolved = True
                incoming_links[clean_target.lower()].append(fpath)
            else:
                test_path = os.path.join(base_dir, target_file)
                if not test_path.endswith(".md"):
                    test_path += ".md"
                if os.path.exists(test_path):
                    resolved = True
        elif target_lower.startswith("sources/"):
            test_path = os.path.join(base_dir, target_file)
            if not test_path.endswith(".md") and not os.path.splitext(target_file)[1]:
                test_path += ".md"
            if os.path.exists(test_path):
                resolved = True
        elif target_lower.startswith("file:///"):
            from urllib.parse import unquote
            clean_path = unquote(target_file[8:])
            if os.path.exists(clean_path):
                resolved = True
        elif target_file.startswith("/"):
            if os.path.exists(target_file):
                resolved = True
        else:
            if target_lower in wiki_map:
                resolved = True
                incoming_links[target_lower].append(fpath)
            else:
                # Check under wiki_dir
                test_path = os.path.join(wiki_dir, target_file)
                if not test_path.endswith(".md"):
                    test_path += ".md"
                if os.path.exists(test_path):
                    resolved = True
                else:
                    # Check under base_dir
                    test_path2 = os.path.join(base_dir, target_file)
                    if not test_path2.endswith(".md"):
                        test_path2 += ".md"
                    if os.path.exists(test_path2):
                        resolved = True
        
        if not resolved:
            if os.path.basename(fpath) == "README.md" and (target in ["C++23", "CUIAOXIANG"] or "obsidian-setup.md" in target):
                continue
            dead_links.append({
                "source_file": fpath,
                "link_text": link,
                "resolved_target": target
            })

# Also parse links in index.md
if os.path.exists(index_path):
    with open(index_path, "r", encoding="utf-8") as f:
        index_content = f.read()
    index_wikilinks = re.findall(r"\[\[([^\]]+)\]\]", index_content)
    for link in index_wikilinks:
        target = clean_str(link.split("|")[0].strip())
        target_file = clean_str(target.split("#")[0].strip())
        target_lower = target_file.lower()
        if target_lower.startswith("wiki/"):
            clean_target = target_file[5:]
            if clean_target.lower() in wiki_map:
                incoming_links[clean_target.lower()].append(index_path)
        else:
            if target_lower in wiki_map:
                incoming_links[target_lower].append(index_path)

# Check orphaned pages (excluding README.md)
orphaned_pages = []
for name, refs in incoming_links.items():
    if name == "readme":
        continue
    if len(refs) == 0:
        orphaned_pages.append(wiki_map[name])

# Scan attachments
attachments = []
if os.path.exists(attachments_dir):
    for root, dirs, files in os.walk(attachments_dir):
        for f in files:
            if not f.startswith("."):
                attachments.append(f)

# Find orphaned attachments
orphaned_attachments = []
md_contents = {}
for md_path in all_md_files:
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            md_contents[md_path] = f.read()
    except Exception as e:
        pass

for att in attachments:
    referenced = False
    for md_path, mdc in md_contents.items():
        if att in mdc:
            referenced = True
            break
    if not referenced:
        orphaned_attachments.append(att)

# Output results
print("\n=== DEAD LINKS ===")
for dl in dead_links:
    print(f"In {dl['source_file']}: dead link [[{dl['link_text']}]]")

print("\n=== ORPHANED PAGES ===")
for op in orphaned_pages:
    print(f"Orphaned page: {op}")

print("\n=== ORPHANED ATTACHMENTS ===")
for oa in orphaned_attachments:
    print(f"Orphaned attachment: {oa}")

print("\n=== CONFIDENCE AGE DECAYS ===")
for cd in confidence_decays:
    print(f"File: {cd['file']} | Old Conf: {cd['old_conf']} -> New Conf: {cd['new_conf']} (Last Confirmed: {cd['last_confirmed']}, Elapsed: {cd['days_elapsed']} days)")

# 5. Scheduled Task 历史过期数据清理 (GC)
def run_scheduled_tasks_gc():
    import json
    import shutil
    
    events_dir = "/Users/cuiaoxiang/.gemini/antigravity/sidecar_data/lint-and-scale/events"
    if not os.path.exists(events_dir):
        return
        
    current_time = datetime.now().timestamp()
    expire_seconds = 7 * 24 * 3600  # 7 天
    deleted_sessions = []
    
    for filename in os.listdir(events_dir):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(events_dir, filename)
        try:
            mtime = os.path.getmtime(filepath)
            if current_time - mtime > expire_seconds:
                with open(filepath, "r", encoding="utf-8") as f:
                    event_data = json.load(f)
                conv_id = event_data.get("payload", {}).get("newConversation", {}).get("conversationId")
                if conv_id:
                    # 本地路径定义
                    paths_to_delete = [
                        f"/Users/cuiaoxiang/.gemini/antigravity/brain/{conv_id}",
                        f"/Users/cuiaoxiang/.gemini/antigravity-cli/brain/{conv_id}",
                    ]
                    files_to_delete = [
                        f"/Users/cuiaoxiang/.gemini/antigravity/conversations/{conv_id}.db",
                        f"/Users/cuiaoxiang/.gemini/antigravity/conversations/{conv_id}.db-shm",
                        f"/Users/cuiaoxiang/.gemini/antigravity/conversations/{conv_id}.db-wal",
                        f"/Users/cuiaoxiang/.gemini/antigravity-cli/conversations/{conv_id}.db",
                        f"/Users/cuiaoxiang/.gemini/antigravity-cli/conversations/{conv_id}.db-shm",
                        f"/Users/cuiaoxiang/.gemini/antigravity-cli/conversations/{conv_id}.db-wal",
                    ]
                    
                    for dp in paths_to_delete:
                        if os.path.exists(dp):
                            shutil.rmtree(dp, ignore_errors=True)
                    for fp in files_to_delete:
                        if os.path.exists(fp):
                            try:
                                os.remove(fp)
                            except:
                                pass
                                
                    deleted_sessions.append(conv_id)
                # 删除 json 文件本身
                os.remove(filepath)
        except Exception as e:
            pass
            
    if deleted_sessions:
        print("\n=== CLEANED EXPIRED SCHEDULED SESSIONS ===")
        for cid in deleted_sessions:
            print(f"Cleaned expired conversation: {cid}")

run_scheduled_tasks_gc()

