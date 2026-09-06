"""Basit, GUI'siz test: sahte bir Downloads klasoru olusturup organizer
mantiginin dosyalari dogru klasorlere tasidigini dogrular."""

import logging
import shutil
import sys
import tempfile
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import organizer as org  # noqa: E402


def run_test():
    tmp = Path(tempfile.mkdtemp(prefix="dl_organizer_test_"))
    watch = tmp / "Downloads"
    watch.mkdir()

    config_data = {
        "watch_folder": str(watch),
        "ignore_extensions": [".crdownload", ".tmp"],
        "stability_check_seconds": 0.2,
        "poll_interval_seconds": 0.1,
        "rules": [
            {
                "name": "Faturalar",
                "match": {"name_contains": ["fatura", "invoice"]},
                "destination": str(watch / "Belgeler" / "Faturalar"),
            },
            {
                "name": "Resimler",
                "match": {"extensions": [".jpg", ".png"]},
                "destination": str(watch / "Resimler"),
            },
            {
                "name": "Arsivler",
                "match": {"extensions": [".zip"]},
                "destination": str(watch / "Arsivler"),
            },
        ],
        "default_destination": str(watch / "Diger"),
        "log_file": str(tmp / "log.txt"),
    }

    config_path = tmp / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config_data, f, allow_unicode=True)

    config = org.Config.load(config_path)
    logger = org.setup_logger(config.log_file)
    logging.getLogger("downloads_organizer").propagate = False

    # --- Test dosyalari olustur ---
    test_files = {
        "eylul_fatura.pdf": "Belgeler/Faturalar",
        "tatil_foto.jpg": "Resimler",
        "yedek.zip": "Arsivler",
        "gizemli_dosya.xyz": "Diger",
        "invoice_2026.pdf": "Belgeler/Faturalar",
    }

    for fname in test_files:
        (watch / fname).write_bytes(b"test-icerik-" + fname.encode())

    # Ayrica: yaziliyor gibi davranan, stabilite kontrolunden gecmemesi
    # gereken bir "gecici" dosya (ignore_extensions'da).
    (watch / "buyuk_dosya.crdownload").write_bytes(b"henuz-bitmedi")

    results = {}
    for fname in list(test_files.keys()):
        moved_to = org.process_file(watch / fname, config, logger)
        results[fname] = moved_to

    ignored_result = org.process_file(watch / "buyuk_dosya.crdownload", config, logger)

    # --- Dogrulama ---
    all_ok = True
    for fname, expected_subdir in test_files.items():
        expected_path = watch / expected_subdir / fname
        ok = expected_path.exists()
        print(f"[{'OK' if ok else 'HATA'}] {fname} -> beklenen: {expected_path.relative_to(watch)}  var_mi={ok}")
        all_ok = all_ok and ok

    ignore_ok = ignored_result is None and (watch / "buyuk_dosya.crdownload").exists()
    print(f"[{'OK' if ignore_ok else 'HATA'}] .crdownload dosyasi yok sayildi mi: {ignore_ok}")
    all_ok = all_ok and ignore_ok

    # --- Cakisma (ayni isimde dosya) testi ---
    (watch / "Resimler").mkdir(parents=True, exist_ok=True)
    dup_source = watch / "tatil_foto2.jpg"
    dup_source.write_bytes(b"baska-icerik")
    # Hedefte ayni isimli baska bir dosya varmis gibi hazirla
    existing_target = watch / "Resimler" / "tatil_foto2.jpg"
    existing_target.write_bytes(b"zaten-var-olan-dosya")

    moved = org.process_file(dup_source, config, logger)
    collision_ok = moved is not None and moved.name == "tatil_foto2 (1).jpg" and moved.exists()
    print(f"[{'OK' if collision_ok else 'HATA'}] Isim cakismasi guvenli sekilde cozuldu mu: {collision_ok} (sonuc: {moved})")
    all_ok = all_ok and collision_ok

    print()
    print("TUM TESTLER BASARILI" if all_ok else "BAZI TESTLER BASARISIZ")

    shutil.rmtree(tmp, ignore_errors=True)
    return all_ok


if __name__ == "__main__":
    ok = run_test()
    sys.exit(0 if ok else 1)
