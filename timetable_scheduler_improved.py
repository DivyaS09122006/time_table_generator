"""
Improved Timetable Scheduler
- Respects "Semester Half" field to avoid first/second half conflicts
- Better conflict reporting
- Elective basket support
- Max 2 sessions per course per day constraint
"""

import json
from datetime import time
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, Counter

class SessionType(Enum):
    LECTURE = "Lecture"
    TUTORIAL = "Tutorial"
    PRACTICAL = "Practical"

@dataclass
class TimeSlot:
    day: str
    start_time: time
    end_time: time
    duration_hours: float
    
    def __hash__(self):
        return hash((self.day, self.start_time, self.end_time))
    
    def __eq__(self, other):
        return (self.day == other.day and 
                self.start_time == other.start_time and 
                self.end_time == other.end_time)
    
    def overlaps(self, other) -> bool:
        if self.day != other.day:
            return False
        return self.start_time < other.end_time and other.start_time < self.end_time
    
    def __str__(self):
        return f"{self.day} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"

@dataclass
class Course:
    course_id: str
    course_code: str
    course_title: str
    semester: int
    semester_half: str  # NEW: "Sem-I" or "Sem-II"
    branch: str
    section: Optional[str]
    lectures: int
    tutorials: int
    practicals: int
    faculty_name: str
    is_elective: bool
    basket: Optional[str] = None
    num_students: int = 60
    
    def get_student_key(self):
        """Identify which students take this course"""
        if self.section:
            return f"{self.branch}_{self.section}_Sem{self.semester}"
        else:
            year = (self.semester + 1) // 2
            return f"{self.branch}_Year{year}"

@dataclass
class Room:
    room_id: str
    capacity: int

@dataclass
class ScheduledSession:
    course: Course
    session_type: SessionType
    time_slot: TimeSlot
    room: Room
    faculty_name: str
    session_number: int = 1
    basket: Optional[str] = None

class ImprovedScheduler:
    def __init__(self, courses: List[Course], rooms: List[Room]):
        self.courses = courses
        self.rooms = rooms
        self.schedule: List[ScheduledSession] = []
        
        # Tracking by semester half
        self.faculty_schedule: Dict[str, Dict[str, List[TimeSlot]]] = defaultdict(lambda: defaultdict(list))
        self.room_schedule: Dict[str, Dict[str, List[TimeSlot]]] = defaultdict(lambda: defaultdict(list))
        self.student_schedule: Dict[str, Dict[str, List[TimeSlot]]] = defaultdict(lambda: defaultdict(list))
        
        # Track sessions per course per day
        self.course_daily_schedule: Dict[str, Dict[str, List[SessionType]]] = defaultdict(lambda: defaultdict(list))
        
        # Time slots
        self.time_slots = self._generate_time_slots()
        self.slots_by_duration: Dict[float, List[TimeSlot]] = defaultdict(list)
        for slot in self.time_slots:
            self.slots_by_duration[slot.duration_hours].append(slot)
        
        # Categorize rooms
        self.big_rooms = sorted([r for r in rooms if r.capacity >= 100], key=lambda r: -r.capacity)
        self.regular_rooms = sorted([r for r in rooms if r.capacity < 100 and not (r.room_id.startswith('L'))], key=lambda r: -r.capacity)
        self.labs = [r for r in rooms if r.room_id.startswith('L') or 'LAB' in r.room_id.upper()]
        
        # Enhanced conflict tracking
        self.conflicts = []
        self.conflict_reasons = Counter()
        
        # Detect elective baskets
        self.elective_baskets = self._detect_baskets()
        
        print(f"📚 Loaded:")
        print(f"  Courses: {len(courses)}")
        print(f"  Big rooms (100+): {[f'{r.room_id}({r.capacity})' for r in self.big_rooms]}")
        print(f"  Regular rooms: {len(self.regular_rooms)}")
        print(f"  Labs: {[r.room_id for r in self.labs]}")
        print(f"  Elective baskets detected: {len(self.elective_baskets)}")
    
    def _detect_baskets(self) -> Dict[str, List[Course]]:
        """Group electives into baskets by semester and branch"""
        baskets = defaultdict(list)
        basket_counter = 1
        
        # Group by semester, branch, and whether it's elective
        elective_groups = defaultdict(list)
        for course in self.courses:
            if course.is_elective:
                key = (course.semester, course.branch, course.semester_half)
                elective_groups[key].append(course)
        
        # Assign basket IDs
        for key, courses in elective_groups.items():
            if len(courses) > 1:
                basket_id = f"B{basket_counter}"
                for course in courses:
                    course.basket = basket_id
                    baskets[basket_id].append(course)
                basket_counter += 1
        
        return dict(baskets)
    
    def _generate_time_slots(self) -> List[TimeSlot]:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        slots = []
        
        for day in days:
            # 1.5h lectures
            slots.append(TimeSlot(day, time(9, 0), time(10, 30), 1.5))
            slots.append(TimeSlot(day, time(11, 0), time(12, 30), 1.5))
            slots.append(TimeSlot(day, time(14, 0), time(15, 30), 1.5))
            slots.append(TimeSlot(day, time(16, 0), time(17, 30), 1.5))
            
            # 1h tutorials
            slots.append(TimeSlot(day, time(9, 0), time(10, 0), 1.0))
            slots.append(TimeSlot(day, time(10, 30), time(11, 30), 1.0))
            slots.append(TimeSlot(day, time(11, 30), time(12, 30), 1.0))
            slots.append(TimeSlot(day, time(14, 0), time(15, 0), 1.0))
            slots.append(TimeSlot(day, time(15, 30), time(16, 30), 1.0))
            slots.append(TimeSlot(day, time(16, 30), time(17, 30), 1.0))
            
            # 2h practicals
            slots.append(TimeSlot(day, time(9, 0), time(11, 0), 2.0))
            slots.append(TimeSlot(day, time(11, 0), time(13, 0), 2.0))
            slots.append(TimeSlot(day, time(14, 0), time(16, 0), 2.0))
            slots.append(TimeSlot(day, time(16, 0), time(18, 0), 2.0))
        
        return slots
    
    def _get_suitable_rooms(self, course: Course, session_type: SessionType) -> List[Room]:
        """Get suitable rooms, prioritizing big rooms"""
        suitable = []
        
        if session_type == SessionType.PRACTICAL:
            for room in self.labs:
                if room.capacity >= course.num_students:
                    suitable.append(room)
            return suitable
        
        for room in self.big_rooms + self.regular_rooms:
            if room.capacity >= course.num_students:
                suitable.append(room)
        
        return suitable
    
    def _check_constraints(self, course: Course, session_type: SessionType, 
                          time_slot: TimeSlot, room: Room) -> Tuple[bool, str]:
        """Check scheduling constraints with semester half awareness"""
        
        semester_half = course.semester_half
        
        # Faculty conflict (within same semester half)
        if time_slot in self.faculty_schedule[course.faculty_name][semester_half]:
            self.conflict_reasons["Faculty busy"] += 1
            return False, "Faculty busy"
        
        # Room conflict (across all semester halves - rooms are shared)
        for half in ["Sem-I", "Sem-II"]:
            if time_slot in self.room_schedule[room.room_id][half]:
                self.conflict_reasons["Room occupied"] += 1
                return False, "Room occupied"
        
        # Student conflict (within same semester half)
        student_key = course.get_student_key()
        if time_slot in self.student_schedule[student_key][semester_half]:
            self.conflict_reasons["Students busy"] += 1
            return False, "Students busy"
        
        # Daily limit check
        day = time_slot.day
        daily_sessions = self.course_daily_schedule[course.course_id][day]
        
        if len(daily_sessions) >= 2:
            self.conflict_reasons["Max 2 sessions/day exceeded"] += 1
            return False, "Course already has 2 sessions today"
        
        if len(daily_sessions) == 1:
            existing_type = daily_sessions[0]
            
            if session_type == SessionType.PRACTICAL and existing_type == SessionType.PRACTICAL:
                self.conflict_reasons["Two practicals same day"] += 1
                return False, "Already has a practical today"
            
            if session_type == SessionType.LECTURE and existing_type == SessionType.LECTURE:
                self.conflict_reasons["Two lectures same day"] += 1
                return False, "Already has a lecture today"
            
            if session_type == SessionType.TUTORIAL and existing_type == SessionType.TUTORIAL:
                self.conflict_reasons["Two tutorials same day"] += 1
                return False, "Already has a tutorial today"
            
            if ((session_type == SessionType.LECTURE and existing_type == SessionType.TUTORIAL) or
                (session_type == SessionType.TUTORIAL and existing_type == SessionType.LECTURE)):
                self.conflict_reasons["Lecture+Tutorial same day"] += 1
                return False, "Already has a theory session today"
        
        # Duration check
        required = {SessionType.LECTURE: 1.5, SessionType.TUTORIAL: 1.0, SessionType.PRACTICAL: 2.0}
        if time_slot.duration_hours != required[session_type]:
            self.conflict_reasons["Wrong duration"] += 1
            return False, "Wrong duration"
        
        return True, "OK"
    
    def schedule_course(self, course: Course) -> int:
        """Schedule all sessions for a course"""
        sessions_needed = [
            (SessionType.LECTURE, course.lectures),
            (SessionType.TUTORIAL, course.tutorials),
            (SessionType.PRACTICAL, course.practicals)
        ]
        
        scheduled_count = 0
        
        for session_type, count in sessions_needed:
            for session_num in range(1, count + 1):
                if self._schedule_session(course, session_type, session_num):
                    scheduled_count += 1
                else:
                    self.conflicts.append(
                        f"{course.course_code} ({course.branch} {course.section or ''} {course.semester_half}) - "
                        f"{session_type.value} #{session_num} - Faculty: {course.faculty_name}"
                    )
        
        return scheduled_count
    
    def _schedule_session(self, course: Course, session_type: SessionType, session_number: int) -> bool:
        """Schedule a single session"""
        suitable_rooms = self._get_suitable_rooms(course, session_type)
        if not suitable_rooms:
            self.conflict_reasons["No suitable room"] += 1
            return False
        
        required = {SessionType.LECTURE: 1.5, SessionType.TUTORIAL: 1.0, SessionType.PRACTICAL: 2.0}
        available_slots = self.slots_by_duration[required[session_type]]
        
        for time_slot in available_slots:
            for room in suitable_rooms:
                valid, _ = self._check_constraints(course, session_type, time_slot, room)
                if valid:
                    session = ScheduledSession(
                        course=course,
                        session_type=session_type,
                        time_slot=time_slot,
                        room=room,
                        faculty_name=course.faculty_name,
                        session_number=session_number,
                        basket=course.basket
                    )
                    self.schedule.append(session)
                    
                    # Update tracking
                    semester_half = course.semester_half
                    self.faculty_schedule[course.faculty_name][semester_half].append(time_slot)
                    self.room_schedule[room.room_id][semester_half].append(time_slot)
                    self.student_schedule[course.get_student_key()][semester_half].append(time_slot)
                    self.course_daily_schedule[course.course_id][time_slot.day].append(session_type)
                    
                    return True
        
        return False
    
    def generate_timetable(self) -> Dict:
        """Generate the complete timetable"""
        print("\n" + "="*60)
        print("GENERATING TIMETABLE")
        print("="*60)
        
        # Sort: semester half, semester, practicals, size
        sorted_courses = sorted(
            self.courses,
            key=lambda c: (c.semester_half, c.semester, -c.practicals, -c.num_students)
        )
        
        total_sessions = 0
        for course in sorted_courses:
            count = self.schedule_course(course)
            total_sessions += count
        
        print(f"\n✓ Scheduled {total_sessions} sessions")
        print(f"⚠️  {len(self.conflicts)} conflicts")
        
        # Print conflict breakdown
        print(f"\n📊 Conflict Breakdown:")
        for reason, count in self.conflict_reasons.most_common():
            print(f"   {reason}: {count}")
        
        return self.export_timetable()
    
    def export_timetable(self) -> Dict:
        return {
            "metadata": {
                "total_sessions": len(self.schedule),
                "total_conflicts": len(self.conflicts),
                "total_courses": len(self.courses),
                "elective_baskets": len(self.elective_baskets),
                "conflict_breakdown": dict(self.conflict_reasons)
            },
            "conflicts": self.conflicts,
            "schedule": [
                {
                    "course_code": s.course.course_code,
                    "course_title": s.course.course_title,
                    "semester": s.course.semester,
                    "semester_half": s.course.semester_half,
                    "branch": s.course.branch,
                    "section": s.course.section,
                    "is_elective": s.course.is_elective,
                    "basket": s.basket,
                    "session_type": s.session_type.value,
                    "session_number": s.session_number,
                    "day": s.time_slot.day,
                    "start_time": s.time_slot.start_time.strftime("%H:%M"),
                    "end_time": s.time_slot.end_time.strftime("%H:%M"),
                    "room": s.room.room_id,
                    "room_capacity": s.room.capacity,
                    "faculty": s.faculty_name,
                    "year": (s.course.semester + 1) // 2
                } for s in self.schedule
            ]
        }
    
    def export_by_student_group(self) -> Dict:
        organized = defaultdict(list)
        
        for session in self.schedule:
            key = session.course.get_student_key()
            organized[key].append({
                "course_code": session.course.course_code,
                "course_title": session.course.course_title,
                "semester_half": session.course.semester_half,
                "session_type": session.session_type.value,
                "session_number": session.session_number,
                "day": session.time_slot.day,
                "time": f"{session.time_slot.start_time.strftime('%H:%M')}-{session.time_slot.end_time.strftime('%H:%M')}",
                "room": session.room.room_id,
                "faculty": session.faculty_name,
                "is_elective": session.course.is_elective,
                "basket": session.basket
            })
        
        # Sort
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        for key in organized:
            organized[key].sort(key=lambda x: (
                day_order.index(x["day"]) if x["day"] in day_order else 999,
                x["time"]
            ))
        
        return dict(organized)


def load_data(filepath: str):
    """Load data from JSON"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    courses = []
    course_counter = 0
    for c in data['Courses']:
        course_counter += 1
        
        # Get semester half, default to "Sem-II" if missing
        semester_half = c.get('Semester Half', 'Sem-II')
        
        courses.append(Course(
            course_id=f"COURSE_{course_counter}",
            course_code=c['Course Code'].strip(),
            course_title=c['Course Title'],
            semester=int(c['Semester']),
            semester_half=semester_half,
            branch=c.get('Branch', ''),
            section=c.get('Section') if c.get('Section') not in ['None', None, ''] else None,
            lectures=int(c['Lectures']),
            tutorials=int(c['Tutorials']),
            practicals=int(c['Practicals']),
            faculty_name=c['Faculty'],
            is_elective=c.get('Electives') == 'T',
            num_students=60
        ))
    
    # Load rooms
    rooms = []
    for r in data['Rooms']:
        room_id = r['Room']
        if room_id not in ['-', 'Online', None, '']:
            rooms.append(Room(
                room_id=room_id,
                capacity=int(r['Seating Capacity'])
            ))
    
    return courses, rooms


def main():
    import sys
    import os
    
    # Determine input file
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        possible_files = [
            'input.json',
            '/mnt/user-data/uploads/1770664935774_Filled_Timetable_Basket_Removed.json',
        ]
        
        input_file = None
        for filepath in possible_files:
            if os.path.exists(filepath):
                input_file = filepath
                break
        
        if input_file is None:
            print("❌ Error: No input file found!")
            sys.exit(1)
    
    print(f"📂 Loading data from: {input_file}")
    courses, rooms = load_data(input_file)
    
    # Create scheduler
    scheduler = ImprovedScheduler(courses, rooms)
    
    # Generate timetable
    timetable = scheduler.generate_timetable()
    
    # Save to outputs directory
    output_dir = '/mnt/user-data/outputs'
    os.makedirs(output_dir, exist_ok=True)
    
    with open(f'{output_dir}/timetable_output.json', 'w') as f:
        json.dump(timetable, f, indent=2)
    
    with open(f'{output_dir}/timetable_by_student.json', 'w') as f:
        json.dump(scheduler.export_by_student_group(), f, indent=2)
    
    print(f"\n✓ Files saved to {output_dir}:")
    print("  - timetable_output.json")
    print("  - timetable_by_student.json")
    
    total_attempted = timetable['metadata']['total_sessions'] + timetable['metadata']['total_conflicts']
    success_rate = (timetable['metadata']['total_sessions'] / total_attempted * 100) if total_attempted > 0 else 0
    
    print(f"\n📊 FINAL SUMMARY:")
    print(f"  Total courses: {timetable['metadata']['total_courses']}")
    print(f"  Sessions scheduled: {timetable['metadata']['total_sessions']}")
    print(f"  Conflicts: {timetable['metadata']['total_conflicts']}")
    print(f"  Success rate: {success_rate:.1f}%")
    print(f"  Elective baskets: {timetable['metadata']['elective_baskets']}")
    
    if timetable['conflicts']:
        print(f"\n⚠️  Conflicts (showing first 20):")
        for conflict in timetable['conflicts'][:20]:
            print(f"  • {conflict}")
        if len(timetable['conflicts']) > 20:
            print(f"  ... and {len(timetable['conflicts']) - 20} more")


if __name__ == "__main__":
    main()
