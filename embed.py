import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dotenv import load_dotenv
from supabase import Client, create_client
from tqdm import tqdm

from features import extract_features, generate_fingerprint

load_dotenv()

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

WORKERS = 12  # tune up/down based on your network


def process_chant(chant: dict) -> tuple[str, bool, str]:
    """Download, extract features + fingerprint, and upsert one chant."""
    try:
        resp = requests.get(chant["audio_url"], timeout=30)
        resp.raise_for_status()
        features    = extract_features(resp.content)
        fingerprint = generate_fingerprint(resp.content)
        supabase.table("chants").update({
            "embedding":   features.tolist(),
            "fingerprint": fingerprint,
        }).eq("id", chant["id"]).execute()
        return chant["id"], True, ""
    except Exception as e:
        return chant["id"], False, str(e)


def embed_all_chants():
    result = (
        supabase.table("chants")
        .select("id, team, chant_name, audio_url")
        .is_("fingerprint", "null")
        .execute()
    )
    chants = result.data
    total  = len(chants)
    print(f"Found {total} chant(s) to embed — running {WORKERS} workers\n")

    ok = fail = 0
    errors: list[str] = []

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(process_chant, c): c for c in chants}
        with tqdm(total=total, unit="chant") as bar:
            for future in as_completed(futures):
                chant = futures[future]
                _, success, msg = future.result()
                if success:
                    ok += 1
                else:
                    fail += 1
                    errors.append(f"{chant['chant_name']} — {chant['team']}: {msg}")
                bar.set_postfix(ok=ok, fail=fail)
                bar.update(1)

    print(f"\nDone: {ok} embedded, {fail} failed")
    if errors:
        print("\nFailed chants:")
        for e in errors:
            print(f"  {e}")


if __name__ == "__main__":
    embed_all_chants()
