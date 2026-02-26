# 🎓 IIIT Dharwad Timetable Scheduler

An intelligent course scheduling system that automatically generates conflict-free timetables for multiple branches, sections, and elective baskets.



## ✨ Features

- **Smart Scheduling**: Automatically schedules lectures, tutorials, and practicals
- **Conflict Detection**: Tracks faculty, room, and student conflicts
- **Semester Half Support**: Separates first-half and second-half courses
- **Elective Baskets**: Groups electives across branches at identical time slots
- **Room Optimization**: Prioritizes large rooms for bigger classes
- **Daily Limits**: Enforces max 2 sessions per course per day
- **Export Options**: Download as JSON or CSV

---

## 🚀 Quick Start

```bash
# 1. Run the scheduler
python3 timetable_scheduler_improved.py input.json

# 2. Build the HTML viewer
python3 rebuild_html.py

# 3. Open in browser
open timetable_standalone.html
```

That's it! 🎉

---

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- No external libraries needed (uses only standard library)

### Setup

1. **Clone or download** this repository
2. **Ensure you have** these files:
   ```
   ├── input.json                      # Your course data
   ├── timetable_scheduler_improved.py # Main scheduler
   └── rebuild_html.py                 # HTML generator
   ```

3. **Verify Python version**:
   ```bash
   python3 --version
   ```

That's all! No pip install needed.

---

## 📖 Usage

### Basic Workflow

```bash
# Step 1: Edit your course data (if needed)
nano input.json

# Step 2: Generate the timetable
python3 timetable_scheduler_improved.py input.json

# Step 3: Build the HTML viewer
python3 rebuild_html.py

# Step 4: View the results
open timetable_standalone.html
```

### What Gets Generated

After running, you'll have:
- `timetable_output.json` - Complete schedule with metadata
- `timetable_by_student.json` - Organized by student groups
- `timetable_standalone.html` - Interactive web viewer


### Web Interface

The HTML viewer has three tabs:

1. **Student View**: Select a student group to see their weekly schedule
2. **Elective Baskets**: See which electives share time slots
3. **Export Data**: Download as JSON or CSV

---

## ➕ Adding/Modifying Courses

### Method 1: Edit JSON Directly

Open `input.json` and add to the `"Courses"` array:

```json
{
  "Course Code": "CS499",
  "Course Title": "Advanced Machine Learning",
  "Lectures": 3,
  "Tutorials": 1,
  "Practicals": 0,
  "Self-Study": 0,
  "Credits": 4,
  "Faculty": "Dr. Jane Smith",
  "Classroom": "C302",
  "Semester": 6,
  "Electives": "T",
  "Section": "",
  "Branch": "CSE",
  "Semester Half": "Sem-II",
  "Combined": "CS499 - Sem-II"
}
```

### Field Reference

| Field | Required | Values | Example |
|-------|----------|--------|---------|
| `Course Code` | ✅ | Alphanumeric | "CS301" |
| `Course Title` | ✅ | Text | "Operating Systems" |
| `Lectures` | ✅ | 0-5 | 3 |
| `Tutorials` | ✅ | 0-3 | 1 |
| `Practicals` | ✅ | 0-3 | 2 |
| `Faculty` | ✅ | Text | "Dr. John Doe" |
| `Semester` | ✅ | 2, 4, 6, 8 | 4 |
| `Electives` | ✅ | "F" or "T" | "F" (required) or "T" (elective) |
| `Section` | ⚠️ | Text or "" | "2A" or "" for year-wide |
| `Branch` | ✅ | Text | "CSE", "DSAI", "ECE" |
| `Semester Half` | ✅ | "Sem-I" or "Sem-II" | "Sem-II" |

### After Adding Courses

**Always run both commands:**
```bash
python3 timetable_scheduler_improved.py input.json
python3 rebuild_html.py
```

### Method 2: Using Python Script

Create `add_course.py`:

```python
import json

with open('input.json', 'r') as f:
    data = json.load(f)

new_course = {
    "Course Code": "CS499",
    "Course Title": "Advanced ML",
    "Lectures": 3,
    "Tutorials": 1,
    "Practicals": 0,
    "Self-Study": 0,
    "Credits": 4,
    "Faculty": "Dr. Smith",
    "Classroom": "C302",
    "Semester": 6,
    "Electives": "T",
    "Section": "",
    "Branch": "CSE",
    "Semester Half": "Sem-II",
    "Combined": "CS499 - Sem-II"
}

data['Courses'].append(new_course)

with open('input.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"✓ Added {new_course['Course Code']}")
```

Run it:
```bash
python3 add_course.py
python3 timetable_scheduler_improved.py input.json
python3 rebuild_html.py
```

---

## 📁 File Structure

```
timetable-scheduler/
├── README.md                           # This file
│
├── input.json                          # INPUT: Course data
├── timetable_scheduler_improved.py     # SCRIPT: Main scheduler
│
├── timetable_output.json               # OUTPUT: Complete schedule
├── timetable_by_student.json           # OUTPUT: Per-student view
└── timetable_standalone.html           # OUTPUT: Web viewer
```

### Input Format

**input.json** contains:
```json
{
  "Courses": [...],  // List of courses
  "Rooms": [...],    // Available rooms
  "Faculty": [...]   // Faculty list (optional)
}
```

### Output Format

**timetable_output.json** contains:
```json
{
  "metadata": {
    "total_sessions": 298,
    "total_conflicts": 105,
    "elective_baskets": 6,
    "conflict_breakdown": {...}
  },
  "conflicts": [...],
  "schedule": [...]
}
```

---

## 🧮 Algorithm Details

### Scheduling Strategy

1. **Priority Sorting**
   - Semester number (lower first)
   - Practicals first (need labs)
   - Larger classes first

2. **Constraint Checking**
   - Faculty availability
   - Room availability
   - Student conflicts
   - Daily session limits
   - Duration matching

3. **Room Assignment**
   - Big rooms (100+ seats): C002, C003, C004
   - Regular rooms (78-96 seats): C101-C405
   - Labs: L406-L408

### Time Slots

**Per Day:**
- 1.5h lectures: 9:00-10:30, 11:00-12:30, 14:00-15:30, 16:00-17:30
- 1h tutorials: 9:00-10:00, 10:30-11:30, 11:30-12:30, 14:00-15:00, 15:30-16:30, 16:30-17:30
- 2h practicals: 9:00-11:00, 11:00-13:00, 14:00-16:00, 16:00-18:00

**Total:** 20 slots per week (4 per day × 5 days)

### Elective Baskets

Courses in the same basket are automatically scheduled at identical times:
```
BASKET B1:
  CS471 (Deep Computer Vision)
  DS357 (Large Language Models)
  CS458 (Natural Language Processing)
  → All scheduled: Monday 9:00-10:30
```

This allows students to choose any elective from the basket.

---

## ⚠️ Known Limitations

### Current Constraints

1. **Room Capacity**
   - Only 2 large rooms (100+ seats)
   - Bottleneck for year-wide courses
   - **Impact**: ~26% of conflicts

2. **Faculty Availability**
   - Some faculty teach multiple sections
   - Sequential scheduling only
   - **Impact**: ~10% of conflicts

3. **Daily Session Limits**
   - Max 2 sessions per course per day
   - Only allows: (1 theory + 1 practical) OR (2 theory if different types)
   - **Impact**: ~14% of conflicts

4. **Time Slot Scarcity**
   - 20 slots/week may be insufficient
   - Peak demand during elective semesters
   - **Impact**: ~50% of conflicts

### What We're NOT Handling

- Student prerequisites or corequisites
- Faculty preferences or soft constraints
- Room feature requirements (projector, AC, etc.)
- Multi-campus scheduling



## 📈 Performance Tips

### Optimizing Success Rate

1. **Separate Semester Halves**
   - Schedule Sem-I courses weeks 1-7
   - Schedule Sem-II courses weeks 8-14
   - **Expected improvement**: 73.9% → 85%+

2. **Add Time Slots**
   - Early morning: 8:00-9:30
   - Late afternoon: 17:30-19:00
   - Saturday mornings
   - **Expected improvement**: +10-15%

3. **Rotate Electives**
   - Don't offer all electives every semester
   - Alternate between odd/even semesters
   - **Expected improvement**: +5-10%

4. **Add Rooms**
   - 2-3 more large rooms (100+ seats)
   - 1-2 more labs
   - **Expected improvement**: +15-20%


**Supported Branches:**
- CSE (Computer Science & Engineering)
- DSAI (Data Science & Artificial Intelligence)
- ECE (Electronics & Communication Engineering)



## 🎯 Quick Reference Card

```bash
# Basic Usage
python3 timetable_scheduler_improved.py input.json
python3 rebuild_html.py
open timetable_standalone.html

# Add a course
# 1. Edit input.json
# 2. python3 timetable_scheduler_improved.py input.json
# 3. python3 rebuild_html.py

# Validate JSON
python3 -m json.tool input.json

# Check output
cat timetable_output.json | grep "total_sessions"
```
