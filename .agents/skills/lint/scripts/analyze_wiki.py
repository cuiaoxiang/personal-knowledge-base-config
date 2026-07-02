import os
import re
import unicodedata
import json
import urllib.parse
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

def load_config_vaults(base_dir):
    config_vaults = {}
    config_path = os.path.join(base_dir, ".agents", "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                vaults = config_data.get("sync_sources", {}).get("external_vaults", [])
                for v in vaults:
                    name = v.get("name")
                    path = v.get("path")
                    if name and path:
                        config_vaults[name] = os.path.expanduser(path)
        except Exception:
            pass
    return config_vaults

config_vaults = load_config_vaults(base_dir)

def parse_frontmatter(fm_text):
    fm = {}
    current_key = None
    for line in fm_text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        
        # Check if list item
        if stripped.startswith("-") and current_key:
            val = stripped[1:].strip()
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            if not isinstance(fm.get(current_key), list):
                fm[current_key] = []
            fm[current_key].append(val)
            continue
            
        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip()
            val = parts[1].strip()
            
            # If inline list like [a, b]
            if val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                if not inner:
                    fm[key] = []
                else:
                    items = [item.strip() for item in inner.split(",")]
                    fm[key] = [item[1:-1] if (item.startswith('"') and item.endswith('"')) or (item.startswith("'") and item.endswith("'")) else item for item in items]
                current_key = key
            elif not val:
                fm[key] = []
                current_key = key
            else:
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                fm[key] = val
                current_key = key
    return fm

def check_file_resolved(target, base_dir, wiki_map):
    target_clean = clean_str(target)
    target_lower = target_clean.lower()
    
    if target_lower.startswith("wiki/"):
        clean_target = target_clean[5:]
        if clean_target.lower() in wiki_map:
            return True
        test_path = os.path.join(base_dir, target_clean)
        if not test_path.endswith(".md"):
            test_path += ".md"
        return os.path.exists(test_path)
    elif target_lower.startswith("sources/"):
        test_path = os.path.join(base_dir, target_clean)
        if not test_path.endswith(".md") and not os.path.splitext(target_clean)[1]:
            test_path += ".md"
        return os.path.exists(test_path)
    elif target_lower.startswith("file:///"):
        clean_path = urllib.parse.unquote(target_clean[7:])
        return os.path.exists(clean_path)
    elif target_clean.startswith("/"):
        return os.path.exists(target_clean)
    else:
        if target_lower in wiki_map:
            return True
        test_path = os.path.join(wiki_dir, target_clean)
        if not test_path.endswith(".md"):
            test_path += ".md"
        if os.path.exists(test_path):
            return True
        test_path2 = os.path.join(base_dir, target_clean)
        if not test_path2.endswith(".md"):
            test_path2 += ".md"
        return os.path.exists(test_path2)

def check_url_resolved(url, base_dir, config_vaults):
    if url.startswith("file:///"):
        clean_path = urllib.parse.unquote(url[7:])
        return os.path.exists(clean_path)
    elif url.startswith("obsidian://open"):
        try:
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            vname = params.get("vault", [None])[0]
            vfile = params.get("file", [None])[0]
            if vname and vfile:
                vault_path = config_vaults.get(vname)
                if vault_path:
                    full_path = os.path.join(vault_path, urllib.parse.unquote(vfile))
                    return os.path.exists(full_path)
        except Exception:
            pass
    elif url.startswith("http://") or url.startswith("https://"):
        return True
    return False

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
schema_errors = []
VALID_TYPES = {"Library", "Concept", "Person", "Project", "Decision", "Synthesis"}

for fpath in wiki_files:
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Parse YAML frontmatter
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        try:
            fm = parse_frontmatter(fm_text)
            
            # --- Schema Validation ---
            mtype = fm.get("type")
            if not mtype:
                schema_errors.append(f"{fpath}: Missing 'type' field in frontmatter")
            elif mtype not in VALID_TYPES:
                schema_errors.append(f"{fpath}: Invalid type '{mtype}' (must be one of {VALID_TYPES})")
                
            confidence = fm.get("confidence")
            if confidence is not None:
                try:
                    c_val = float(confidence)
                    if not (0.0 <= c_val <= 1.0):
                        schema_errors.append(f"{fpath}: Confidence value {confidence} is out of bounds (0.0 - 1.0)")
                except ValueError:
                    schema_errors.append(f"{fpath}: Confidence '{confidence}' is not a valid float")
            
            last_confirmed = fm.get("last_confirmed")
            if last_confirmed is not None:
                try:
                    datetime.strptime(str(last_confirmed).strip(), "%Y-%m-%d")
                except ValueError:
                    schema_errors.append(f"{fpath}: last_confirmed date '{last_confirmed}' is not in YYYY-MM-DD format")
            
            # --- Decay Checking ---
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
                except Exception:
                    pass
                    
            # --- Sources Link Check inside frontmatter ---
            sources = fm.get("sources", [])
            if isinstance(sources, list):
                for src in sources:
                    resolved = False
                    src_clean = src.strip()
                    # Check if wikilink or obsidian link
                    wikilink_match = re.match(r"^\[\[([^\]]+)\]\]$", src_clean)
                    if wikilink_match:
                        target = wikilink_match.group(1).split("|")[0].strip()
                        resolved = check_file_resolved(target, base_dir, wiki_map)
                    else:
                        mdlink_match = re.match(r"^\[([^\]]*)\]\(([^)]+)\)$", src_clean)
                        if mdlink_match:
                            url = mdlink_match.group(2).strip()
                            resolved = check_url_resolved(url, base_dir, config_vaults)
                        else:
                            resolved = check_file_resolved(src_clean, base_dir, wiki_map) or check_url_resolved(src_clean, base_dir, config_vaults)
                    if not resolved:
                        dead_links.append({
                            "source_file": fpath,
                            "link_text": f"frontmatter.sources: {src}",
                            "resolved_target": src
                        })
        except Exception as e:
            schema_errors.append(f"{fpath}: Failed to parse YAML frontmatter: {str(e)}")
            
    # Find all Wikilinks in content
    wikilinks = re.findall(r"\[\[([^\]]+)\]\]", content)
    for link in wikilinks:
        target = clean_str(link.split("|")[0].strip())
        target_file = clean_str(target.split("#")[0].strip())
        resolved = check_file_resolved(target_file, base_dir, wiki_map)
        
        if resolved:
            # If it's a valid wiki link, record incoming link
            target_lower = target_file.lower()
            if target_lower.startswith("wiki/"):
                clean_target = target_file[5:]
                if clean_target.lower() in incoming_links:
                    incoming_links[clean_target.lower()].append(fpath)
            elif target_lower in incoming_links:
                incoming_links[target_lower].append(fpath)
        else:
            if os.path.basename(fpath) == "README.md" and (target in ["C++23", "CUIAOXIANG"] or "obsidian-setup.md" in target):
                continue
            dead_links.append({
                "source_file": fpath,
                "link_text": link,
                "resolved_target": target
            })
            
    # Find all standard Markdown links in content
    markdown_links = re.findall(r"\[([^\]]*)\]\(([^)]+)\)", content)
    for label, url in markdown_links:
        # Ignore external links, check local file/// and obsidian:// links
        if url.startswith("http://") or url.startswith("https://") or url.startswith("#"):
            continue
        resolved = check_url_resolved(url, base_dir, config_vaults) or check_file_resolved(url, base_dir, wiki_map)
        if not resolved:
            dead_links.append({
                "source_file": fpath,
                "link_text": f"[{label}]({url})",
                "resolved_target": url
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

print("\n=== SCHEMA ERRORS ===")
for se in schema_errors:
    print(se)



# 5. Scheduled Task 历史过期数据清理 (GC)
def run_scheduled_tasks_gc():
    import json
    import shutil
    
    home = os.path.expanduser("~")
    events_dir = os.path.join(home, ".gemini", "antigravity", "sidecar_data", "lint-and-scale", "events")
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
                        os.path.join(home, ".gemini", "antigravity", "brain", conv_id),
                        os.path.join(home, ".gemini", "antigravity-cli", "brain", conv_id),
                    ]
                    files_to_delete = [
                        os.path.join(home, ".gemini", "antigravity", "conversations", f"{conv_id}.db"),
                        os.path.join(home, ".gemini", "antigravity", "conversations", f"{conv_id}.db-shm"),
                        os.path.join(home, ".gemini", "antigravity", "conversations", f"{conv_id}.db-wal"),
                        os.path.join(home, ".gemini", "antigravity-cli", "conversations", f"{conv_id}.db"),
                        os.path.join(home, ".gemini", "antigravity-cli", "conversations", f"{conv_id}.db-shm"),
                        os.path.join(home, ".gemini", "antigravity-cli", "conversations", f"{conv_id}.db-wal"),
                    ]
                    
                    success = True
                    for dp in paths_to_delete:
                        if os.path.exists(dp):
                            try:
                                shutil.rmtree(dp)
                            except Exception:
                                pass
                            if os.path.exists(dp):
                                success = False
                    for fp in files_to_delete:
                        if os.path.exists(fp):
                            try:
                                os.remove(fp)
                            except Exception:
                                pass
                            if os.path.exists(fp):
                                success = False
                                
                    if success:
                        deleted_sessions.append(conv_id)
                        try:
                            os.remove(filepath)
                        except Exception:
                            pass
        except Exception as e:
            pass
            
    if deleted_sessions:
        print("\n=== CLEANED EXPIRED SCHEDULED SESSIONS ===")
        for cid in deleted_sessions:
            print(f"Cleaned expired conversation: {cid}")

run_scheduled_tasks_gc()

