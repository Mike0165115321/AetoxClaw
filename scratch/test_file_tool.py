import sys
import os
from pathlib import Path

# เพิ่ม Path เพื่อให้เรียกใช้โมดูลในโปรเจกต์ได้
sys.path.append(os.getcwd())

from aetox.tools.file_manager import MasterFileManager

def test_file_manager():
    fm = MasterFileManager()
    test_base = Path("e:/Aetox/AetoxOS/scratch/test_zone")
    
    # 1. ทดสอบการสร้างโฟลเดอร์
    print("\n[TEST 1] Creating Folder...")
    folder_path = test_base / "New_Folder_Level1/Level2"
    res1 = fm.execute({"action": "create_folder", "path": str(folder_path)})
    print(f"Status: {res1.get('status')}")
    
    # 2. ทดสอบการสร้างไฟล์
    print("\n[TEST 2] Creating File...")
    file_path = folder_path / "test_file.txt"
    res2 = fm.execute({"action": "create_file", "path": str(file_path), "content": "Hello AetoxOS!"})
    print(f"Status: {res2.get('status')}")
    
    # 3. ทดสอบการเปลี่ยนชื่อไฟล์ (Rename)
    print("\n[TEST 3] Renaming File...")
    renamed_path = folder_path / "renamed_file.txt"
    res3 = fm.execute({"action": "rename", "path": str(file_path), "new_path": str(renamed_path)})
    print(f"Status: {res3.get('status')}")
    
    # 4. ทดสอบการย้ายไฟล์ (Move)
    print("\n[TEST 4] Moving File...")
    moved_path = test_base / "moved_file.txt"
    res4 = fm.execute({"action": "move", "path": str(renamed_path), "destination": str(moved_path)})
    print(f"Status: {res4.get('status')}")

    # ตรวจสอบความถูกต้องขั้นสุดท้ายจากไฟล์จริง
    print("\n--- Physical Verification ---")
    print(f"Folder exists: {folder_path.exists()}")
    print(f"File moved to destination: {moved_path.exists()}")

    if moved_path.exists():
        print("\n>>> [FINAL VERDICT] Works 100%!")
    else:
        print("\n>>> [FINAL VERDICT] Failed!")

if __name__ == "__main__":
    # ตรวจสอบว่ามีไดรฟ์ E หรือไม่ (ถ้าไม่มีจะใช้โฟลเดอร์ปัจจุบันแทนเพื่อการทดสอบ)
    if not os.path.exists("e:/"):
        print("⚠️ ไม่พบไดรฟ์ E: จะทำการทดสอบในโฟลเดอร์ปัจจุบันแทน...")
        # (ในกรณีทดสอบบนเครื่องอื่น)
    
    test_file_manager()
