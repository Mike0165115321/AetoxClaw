# 🧠 AetoxClaw: Algorithms & Flowcharts (Deep Dive)

เอกสารฉบับนี้อธิบายอัลกอริทึมและตรรกะการทำงานภายในของ **AetoxClaw** (Agentic Local OS Orchestrator) อย่างละเอียดที่สุด โดยอ้างอิงจากโครงสร้างโค้ดจริงในปัจจุบัน

---

## 1. High-Level System Flow (The Big Picture)

AetoxClaw ทำงานบนสถาปัตยกรรม **Stateless Core** โดยมี Discord เป็น Interface หลัก ระบบจะจัดการทรัพยากรแยกตาม User ID ผ่าน `SessionManager`

```mermaid
graph TD
    User([User on Discord]) -->|Message| Bot[Discord Interface]
    Bot -->|User ID| SM[Session Manager]
    SM -->|Get/Create| SC[Session Context & Dispatcher]
    
    SC -->|Goal + History| IE[Intent Extraction]
    
    IE -->|Analysis| Lane{Execution Lane?}
    
    Lane -->|steps <= 2| Direct[Unified Streaming Pipe]
    Lane -->|steps > 2| Plan[Multi-Step Planning Lane]
    
    Direct -->|Tool Result| Res1[Response & History Update]
    Plan -->|Plan Results| Res2[Task Summary & History Update]
    
    Res1 -->|Token Stream| User
    Res2 -->|Final Report| User
```

---

## 2. Intent Extraction & Dynamic Tool Discovery

หัวใจของการวิเคราะห์เจตนาไม่ใช่การใช้ `if-else` แต่เป็นการใช้ **Tool Schema Injection** เพื่อให้โมเดลเข้าใจความสามารถของระบบแบบ Real-time

### Algorithm: Schema-Based Extraction
1.  **Registry Scan**: ระบบโหลดเครื่องมือทั้งหมดจาก `aetox/tools/`
2.  **Schema Generation**: แปลง Class Methods เป็น JSON Schema (Prompt-friendly)
3.  **Context Injection**: ฉีด Schema + ประวัติล่าสุด (3-5 รอบ) เข้าไปใน Prompt
4.  **LLM Reasoning**: โมเดลวิเคราะห์ว่าควรใช้เครื่องมือใด พร้อมประมาณการจำนวนขั้นตอน (`estimated_steps`)

```mermaid
sequenceDiagram
    participant D as Dispatcher
    participant TR as Tool Registry
    participant LLM as extraction_model (JSON)
    
    D->>TR: build_prompt_doc()
    TR-->>D: Tool Descriptions & Params
    D->>LLM: Goal + Tools + History
    LLM-->>D: { "tool": "file_mgr", "action": "read", "estimated_steps": 1, "confidence": 0.9 }
```

---

## 3. Unified Streaming Pipeline (Single-Action Lane)

เมื่อระบบวิเคราะห์แล้วว่างานไม่ซับซ้อน จะเข้าสู่เลนการทำงานที่เร็วที่สุด พร้อมระบบสรุปเนื้อหาอัตโนมัติ

```mermaid
flowchart LR
    Start[Run Action] --> Tool[Execute Tool]
    Tool --> Out{Output Length?}
    Out -->|> 600 chars| Sum[Summarize with LLM]
    Out -->|<= 600 chars| Raw[Use Raw Output]
    Sum --> Stream[Stream to Discord]
    Raw --> Stream
    Stream --> Hist[Add to SessionContext]
```

---

## 4. Multi-Step Planning Lane (The Dispatcher Loop)

สำหรับงานที่ต้องทำหลายขั้นตอน ระบบจะใช้ `AetoxPlanner` สร้างแผนงาน และรันผ่าน **Feedback-Loop** โดยมี **Critic** คอยตรวจสอบ

### Algorithm: Dispatcher Loop with Critic
1.  **Planning**: สร้างลิสต์ของขั้นตอน (Steps) พร้อมเหตุผล
2.  **Execution**: รัน Executor ทีละขั้นตอน
3.  **Evaluation**: ส่งผลลัพธ์ให้ **Critic Agent** ตรวจสอบ (Pass/Fail)
4.  **Feedback & Retry**: หากไม่ผ่าน จะนำ Feedback จาก Critic ไปเป็น "Hint" ในการลองใหม่ (สูงสุด 3 ครั้ง)

```mermaid
graph TD
    P[Create Plan] --> Approve{User Approve?}
    Approve -->|No| End[Cancel]
    Approve -->|Yes| Step[Run Step N]
    
    Step --> Critic{Critic Verdict?}
    Critic -->|Pass| Next{Next Step?}
    Critic -->|Fail| Feedback[Inject Feedback as Hint]
    
    Feedback --> Retry{Retry Count < 3?}
    Retry -->|Yes| Step
    Retry -->|No| Fail[Report Failure]
    
    Next -->|Yes| Step
    Next -->|No| Success[Task Complete]
```

---

## 5. Memory Compression Algorithm (3-Level Context)

AetoxClaw ใช้หลักการ **Stateless History Injection** เพื่อประหยัด Token และรองรับโมเดลขนาดเล็ก (7B-9B)

| ระดับ | ข้อมูล | การจัดการ | ตัวอย่าง |
| :--- | :--- | :--- | :--- |
| **1. Critical** | Goal, Plan ID, Root Path | **เก็บตลอด** จนจบ Task | `global_goal` |
| **2. Context** | Step Results, Chat History | **สรุป (Summarize)** หรือตัดให้สั้น | `plan_summary` |
| **3. Discard** | Raw Logs, Metadata, Temp Files | **ทิ้งทันที** หลังจบขั้นตอน | Raw JSON response |

### Token Budget Manager
- **Sliding Window**: เก็บ Chat History แค่ 5 ล่าสุด (ตั้งค่าได้ใน `SessionContext`)
- **Truncation**: ตัดความยาว Output ของเครื่องมือเหลือ 200-500 ตัวอักษรก่อนบันทึกลงความจำ

---

## 6. Safety Layer: Permission & Sandbox

ระบบความปลอดภัยแบ่งตามความเสี่ยง (Risk Levels) โดยใช้ `config/permissions.yaml` เป็นเกณฑ์

### Risk Assessment Logic
```mermaid
flowchart TD
    Action[Action: delete_file] --> Check{Risk Level?}
    Check -->|Low| Exec[Execute Immediately]
    Check -->|Medium/High| UI[Send Approval Payload]
    UI -->|JSON Payload| Discord[Discord Reaction Buttons]
    Discord -->|Approved| Exec
    Discord -->|Denied| Stop[Abort & Notify]
```

**Approval Payload Example:**
```json
{
  "action": "delete_file",
  "details": "Deleting 'logs/old_data.txt' in sandboxed directory",
  "risk": "HIGH",
  "path": "e:/Aetox/AetoxOS/logs/old_data.txt"
}
```

---

## 7. Tool Registry Flow (Dynamic Loading)

การเพิ่มความสามารถใหม่ให้ AetoxClaw ทำได้แบบ **Zero Configuration** ผ่านระบบ Registry

```mermaid
graph LR
    Folder[aetox/tools/*.py] --> Loader[Tool Loader]
    Loader -->|Import| Class[BaseTool Subclasses]
    Class --> Registry[Global Registry]
    Registry -->|Schema| Dispatcher[Dispatcher / Planner]
```

---

## 8. Error Recovery & Escalation

หากระบบติด Loop หรือแก้ปัญหาไม่ได้ในเลนปกติ จะมีการยกระดับ (Escalation):
- **Retry**: พยายามแก้ไขจุดผิดพลาดเดิมตามคำแนะนำของ Critic
- **Feedback Injection**: ส่ง Feedback กลับไปที่ Planner เพื่อปรับแผน (ถ้าจำเป็น)
- **User Hand-off**: หากล้มเหลวครบโควตา จะหยุดและสรุปปัญหาให้ผู้ใช้ช่วยตัดสินใจ

---
*Document Version: 2026.05.06 | Real-time Alignment with AetoxClaw Codebase*
