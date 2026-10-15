import os
import shutil

def clean_title(filename):
    name, ext = os.path.splitext(filename)
    # remove common suffixes from download sites
    for pat in [" - Djjohal.fm", " (Djjohal.fm)", " (PenduJatt.Com.Se)",
                " (Mr-Punjab.Com)", "-128kb", "_128 Kbps", " 128 Kbps",
                " 320 Kbps", "(PenduJatt.Com.Se)", "SpotiDown.App - ",
                "(MP3.co)", " (1)", " (2)", " (3)", " (Official HD Audio)",
                " (From The Vault)"]:
        name = name.replace(pat, "").replace(pat.strip(), "")
    
    # Optional: also remove singer prefix/suffix if it's there, but let's keep it simple
    return name.strip().strip("_").strip("-").strip() + ext

def main():
    audio_dir = os.path.join("static", "audio")
    count = 0
    
    for singer in os.listdir(audio_dir):
        singer_path = os.path.join(audio_dir, singer)
        if not os.path.isdir(singer_path):
            continue
            
        for f in os.listdir(singer_path):
            if not f.lower().endswith(('.mp3', '.wav', '.m4a')):
                continue
                
            old_path = os.path.join(singer_path, f)
            new_name = clean_title(f)
            
            if new_name != f:
                new_path = os.path.join(singer_path, new_name)
                # handle collisions just in case
                if os.path.exists(new_path) and old_path.lower() != new_path.lower():
                    print(f"Skipping rename to {new_name} as it already exists.")
                    continue
                os.rename(old_path, new_path)
                print(f"Renamed: '{f}' -> '{new_name}'")
                count += 1
                
    print(f"\nDone! Successfully cleaned up {count} messy filenames in the VS Code workspace.")

if __name__ == "__main__":
    main()
