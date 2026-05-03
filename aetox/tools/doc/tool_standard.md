# AetoxOS: มาตรฐานการสร้างเครื่องมือ (Tool Standard)

เอกสารฉบับนี้กำหนดโครงสร้างมาตรฐานสำหรับการสร้างเครื่องมือ (Tools) ใหม่ใน AetoxOS เพื่อให้ระบบคงความยืดหยุ่น (Flexibility) และรองรับการขยายตัว (Scalability) ได้อย่างไร้รอยต่อ

---

## 1. โครงสร้างพื้นฐาน (Core Architecture)
ทุกเครื่องมือต้องสืบทอดคุณสมบัติ (Inherit) จากคลาส `BaseTool` เพื่อให้แน่ใจว่ามี Interface ที่เหมือนกัน

### ส่วนประกอบที่สำคัญ:
1. **Name:** ชื่อเครื่องมือ (ภาษาอังกฤษ lowercase)
2. **Description:** คำอธิบายหน้าที่ (ภาษาไทย) **สำคัญมาก:** AI จะใช้ข้อมูลนี้ในการตัดสินใจเลือกใช้เครื่องมือ
3. **Actions:** รายการคำสั่งที่เครื่องมือนี้รองรับ (List of Strings)
4. **Execute Method:** จุดรับคำสั่งและพารามิเตอร์จาก AI

---

## 2. รูปแบบการเขียนคลาส (Class Structure)

```python
class YourNewTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="your_tool_name",
            description="อธิบายว่าเครื่องมือนี้ทำอะไร (เน้นคีย์เวิร์ดที่ผู้ใช้จะสั่ง)",
            actions=["action_1", "action_2"]
        )

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # 1. ดึงพารามิเตอร์ที่ AI ส่งมา
        action = params.get("action")
        target = params.get("target") or params.get("path")

        # 2. ตรวจสอบ Action และทำงานตาม Logic
        if action == "action_1":
            return self._logic_function(target)

        return {"status": "failure", "error": f"ไม่รู้จักคำสั่ง: {action}"}
```

---

## 3. มาตรฐานการรับ-ส่งข้อมูล (Input/Output Standard)

### การรับข้อมูล (Input):
- รับพารามิเตอร์ในรูปแบบ `Dict[str, Any]` (JSON จาก AI)
- ชื่อตัวแปรควรใช้มาตรฐานกลาง: `path`, `target`, `targets`, `message`

### การส่งข้อมูล (Output):
ต้องคืนค่าเป็น `Dict` ที่มีโครงสร้างดังนี้เสมอ:
- `status`: "success" หรือ "failure"
- `output`: ข้อความสรุปผลงาน (ถ้าสำเร็จ)
- `error`: ข้อความอธิบายสาเหตุ (ถ้าล้มเหลว)

---

## 4. ขั้นตอนการลงทะเบียน (Registration Process)
เมื่อสร้างไฟล์เครื่องมือใน `aetox/tools/` เรียบร้อยแล้ว ต้องทำการเชื่อมต่อที่ **`ExecutorAgent`**:
1. Import คลาสเครื่องมือใหม่
2. Initialize ใน `__init__`
3. เพิ่มชื่อตัวแปรลงในเมธอด `_get_tools_info` เพื่อให้ระบบฉีดข้อมูลลงในพรอมต์อัตโนมัติ (Dynamic Discovery)

---

## 5. กฎเหล็ก (Best Practices)
- **Description is King:** เขียนคำอธิบายหน้าที่ใน `__init__` ให้ชัดเจนที่สุด เพื่อให้ AI เลือกใช้ได้ถูกงานโดยไม่ต้องจูนพรอมต์เพิ่ม
- **Atomic Actions:** หนึ่ง Action ควรทำงานอย่างเดียวให้จบ (Single Responsibility)
- **Error Handling:** ต้องมี `try-except` ครอบ Logic เสมอ เพื่อไม่ให้บอทค้างเวลาทำงานพลาด
