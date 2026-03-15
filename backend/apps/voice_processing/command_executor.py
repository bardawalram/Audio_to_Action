"""
Command executor for voice commands.
Prepares confirmation data and executes confirmed commands.
"""
import logging
from django.db import models, transaction
from django.conf import settings
from apps.academics.models import Student, ClassSection, Class, Section
from apps.marks.models import Marks, Subject, ExamType
from apps.marks.utils import calculate_student_grade
from apps.attendance.models import AttendanceSession, AttendanceRecord
from apps.audit.models import AuditLog
from datetime import date

logger = logging.getLogger(__name__)


class CommandExecutor:
    """
    Executes voice commands after confirmation.
    """

    @classmethod
    def prepare_confirmation(cls, intent, entities, user):
        """
        Prepare confirmation data for display to user.

        Args:
            intent (str): Command intent
            entities (dict): Extracted entities
            user: User who issued the command

        Returns:
            dict: Confirmation data to display
        """
        if intent == 'BATCH_UPDATE_QUESTION_MARKS':
            return cls._prepare_batch_question_marks_confirmation(entities, user)
        elif intent == 'UPDATE_QUESTION_MARKS':
            return cls._prepare_question_marks_confirmation(entities, user)
        elif intent == 'OPEN_QUESTION_SHEET':
            return cls._prepare_question_sheet_navigation(entities, user)
        elif intent == 'ENTER_MARKS':
            return cls._prepare_marks_confirmation(entities, user)
        elif intent == 'MARK_ATTENDANCE':
            return cls._prepare_attendance_confirmation(entities, user)
        elif intent == 'VIEW_STUDENT':
            return cls._prepare_student_view_confirmation(entities, user)
        elif intent == 'NAVIGATE_MARKS':
            return cls._prepare_navigation_confirmation('marks', None, user)
        elif intent == 'NAVIGATE_ATTENDANCE':
            return cls._prepare_navigation_confirmation('attendance', None, user)
        elif intent == 'NAVIGATE_DASHBOARD':
            return cls._prepare_navigation_confirmation('dashboard', None, user)
        elif intent == 'NAVIGATE_REPORTS':
            return cls._prepare_navigation_confirmation('reports', None, user)
        elif intent == 'NAVIGATE_CLASS_REPORT':
            return cls._prepare_navigation_confirmation('reports', {'tab': 'class'}, user)
        elif intent == 'NAVIGATE_STUDENT_REPORT':
            return cls._prepare_navigation_confirmation('reports', {'tab': 'student'}, user)
        elif intent == 'NAVIGATE_ATTENDANCE_REPORT':
            return cls._prepare_navigation_confirmation('reports', {'tab': 'attendance'}, user)
        elif intent == 'OPEN_MARKS_SHEET':
            return cls._prepare_navigation_confirmation('marks', entities, user)
        elif intent == 'OPEN_ATTENDANCE_SHEET':
            return cls._prepare_navigation_confirmation('attendance', entities, user)
        elif intent == 'UPDATE_MARKS':
            return cls._prepare_marks_update_confirmation(entities, user)
        elif intent == 'DOWNLOAD_PROGRESS_REPORT':
            return cls._prepare_progress_report_confirmation(entities, user)
        elif intent == 'SELECT_EXAM_TYPE':
            return cls._prepare_exam_type_selection(entities, user)
        elif intent == 'COLLECT_FEE':
            return cls._prepare_fee_collection_confirmation(entities, user)
        elif intent == 'SHOW_FEE_DETAILS':
            return cls._prepare_fee_details_confirmation(entities, user)
        elif intent == 'OPEN_FEE_PAGE':
            return cls._prepare_fee_page_navigation(entities, user)
        elif intent == 'SHOW_DEFAULTERS':
            return cls._prepare_defaulters_confirmation(entities, user)
        elif intent == 'TODAY_COLLECTION':
            return cls._prepare_today_collection_confirmation(entities, user)
        elif intent == 'NAVIGATE_FEE_REPORTS':
            return cls._prepare_navigation_confirmation('fee-reports', None, user)
        else:
            raise ValueError(f"Unknown intent: {intent}")

    @classmethod
    def execute(cls, intent, entities, confirmation_data, user):
        """
        Execute the confirmed command.

        Args:
            intent (str): Command intent
            entities (dict): Extracted entities
            confirmation_data (dict): Prepared confirmation data
            user: User executing the command

        Returns:
            dict: Execution result
        """
        if intent == 'BATCH_UPDATE_QUESTION_MARKS':
            return cls._execute_batch_question_marks_update(entities, confirmation_data, user)
        elif intent == 'UPDATE_QUESTION_MARKS':
            return cls._execute_question_marks_update(entities, confirmation_data, user)
        elif intent == 'OPEN_QUESTION_SHEET':
            return cls._execute_navigation(intent, confirmation_data, user)
        elif intent == 'ENTER_MARKS':
            return cls._execute_marks_entry(entities, confirmation_data, user)
        elif intent == 'MARK_ATTENDANCE':
            return cls._execute_attendance(entities, confirmation_data, user)
        elif intent == 'VIEW_STUDENT':
            return cls._execute_student_view(entities, confirmation_data, user)
        elif intent in ['NAVIGATE_MARKS', 'NAVIGATE_ATTENDANCE', 'NAVIGATE_DASHBOARD', 'NAVIGATE_REPORTS', 'NAVIGATE_CLASS_REPORT', 'NAVIGATE_STUDENT_REPORT', 'NAVIGATE_ATTENDANCE_REPORT', 'OPEN_MARKS_SHEET', 'OPEN_ATTENDANCE_SHEET', 'SELECT_EXAM_TYPE', 'OPEN_FEE_PAGE', 'NAVIGATE_FEE_REPORTS', 'SELECT_SECTION']:
            return cls._execute_navigation(intent, confirmation_data, user)
        elif intent == 'UPDATE_MARKS':
            return cls._execute_marks_update(entities, confirmation_data, user)
        elif intent == 'DOWNLOAD_PROGRESS_REPORT':
            return cls._execute_progress_report_download(entities, confirmation_data, user)
        elif intent == 'COLLECT_FEE':
            return cls._execute_fee_collection(entities, confirmation_data, user)
        elif intent == 'SHOW_FEE_DETAILS':
            return cls._execute_navigation(intent, confirmation_data, user)
        elif intent == 'SHOW_DEFAULTERS':
            return cls._execute_navigation(intent, confirmation_data, user)
        elif intent == 'TODAY_COLLECTION':
            return cls._execute_navigation(intent, confirmation_data, user)
        else:
            raise ValueError(f"Unknown intent: {intent}")

    @classmethod
    def _prepare_marks_confirmation(cls, entities, user):
        """
        Prepare marks entry confirmation.
        """
        # Validate required entities
        required = ['roll_number', 'class', 'section', 'marks']
        missing = [field for field in required if field not in entities or not entities[field]]

        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        # Get student
        try:
            class_obj = Class.objects.get(grade_number=entities['class'])
            section_obj = Section.objects.get(name=entities['section'])

            # Get current academic year's class section
            class_section = ClassSection.objects.filter(
                class_obj=class_obj,
                section=section_obj
            ).order_by('-academic_year').first()

            if not class_section:
                raise ValueError(f"Class {entities['class']}{entities['section']} not found")

            student = Student.objects.get(
                roll_number=entities['roll_number'],
                class_section=class_section,
                is_active=True
            )

        except Class.DoesNotExist:
            raise ValueError(f"Class {entities['class']} not found")
        except Section.DoesNotExist:
            raise ValueError(f"Section {entities['section']} not found")
        except Student.DoesNotExist:
            raise ValueError(f"Student with roll number {entities['roll_number']} not found in class {entities['class']}{entities['section']}")

        # Check teacher permissions
        if user.role == 'TEACHER':
            teacher_profile = getattr(user, 'teacher_profile', None)
            if teacher_profile:
                assigned_classes = teacher_profile.assigned_classes.all()
                if class_section not in assigned_classes:
                    raise PermissionError(f"You are not assigned to class {entities['class']}{entities['section']}")

        # Get default exam type
        exam_type = ExamType.objects.filter(
            code=settings.DEFAULT_EXAM_TYPE,
            is_active=True
        ).first()

        if not exam_type:
            raise ValueError("Default exam type not configured")

        # Prepare marks table data
        marks_table = []
        for subject_code, marks_value in entities['marks'].items():
            try:
                subject = Subject.objects.get(code=subject_code.upper())
                marks_table.append({
                    'subject': subject.name,
                    'subject_code': subject.code,
                    'marks_obtained': marks_value,
                    'max_marks': subject.max_marks
                })
            except Subject.DoesNotExist:
                logger.warning(f"Subject {subject_code} not found, skipping")
                continue

        if not marks_table:
            raise ValueError("No valid subjects found in marks data")

        return {
            'student': {
                'id': student.id,
                'name': student.get_full_name(),
                'roll_number': student.roll_number,
                'class': f"{class_obj.name}{section_obj.name}"
            },
            'exam_type': {
                'id': exam_type.id,
                'name': exam_type.name
            },
            'marks_table': marks_table,
            'total_subjects': len(marks_table)
        }

    @classmethod
    @transaction.atomic
    def _execute_marks_entry(cls, entities, confirmation_data, user):
        """
        Execute marks entry command.
        """
        print("\n=== EXECUTING MARKS ENTRY ===")
        print(f"confirmation_data: {confirmation_data}")
        print(f"user: {user}")
        logger.info("=== EXECUTING MARKS ENTRY ===")
        logger.info(f"confirmation_data: {confirmation_data}")
        logger.info(f"user: {user}")

        student = Student.objects.get(id=confirmation_data['student']['id'])
        print(f"Found student: {student.get_full_name()} (ID: {student.id}, Roll: {student.roll_number})")
        logger.info(f"Found student: {student.get_full_name()} (ID: {student.id}, Roll: {student.roll_number})")

        exam_type = ExamType.objects.get(id=confirmation_data['exam_type']['id'])
        print(f"Using exam_type: {exam_type.name} (ID: {exam_type.id})")
        logger.info(f"Using exam_type: {exam_type.name} (ID: {exam_type.id})")

        created_marks = []
        updated_marks = []

        for mark_data in confirmation_data['marks_table']:
            print(f"Processing mark_data: {mark_data}")
            logger.info(f"Processing mark_data: {mark_data}")
            subject = Subject.objects.get(code=mark_data['subject_code'])
            print(f"Found subject: {subject.name} (Code: {subject.code})")
            logger.info(f"Found subject: {subject.name} (Code: {subject.code})")

            # Create or update marks
            mark, created = Marks.objects.update_or_create(
                student=student,
                subject=subject,
                exam_type=exam_type,
                defaults={
                    'marks_obtained': mark_data['marks_obtained'],
                    'max_marks': mark_data['max_marks'],
                    'entered_by': user
                }
            )

            print(f"Mark {'CREATED' if created else 'UPDATED'}: Student={student.roll_number}, Subject={subject.name}, Marks={mark.marks_obtained}/{mark.max_marks}")
            logger.info(f"Mark {'CREATED' if created else 'UPDATED'}: Student={student.roll_number}, Subject={subject.name}, Marks={mark.marks_obtained}/{mark.max_marks}")

            if created:
                created_marks.append(mark)
            else:
                updated_marks.append(mark)

            # Create audit log
            AuditLog.objects.create(
                user=user,
                action='CREATE' if created else 'UPDATE',
                model_name='Marks',
                object_id=str(mark.id),
                new_values={
                    'student': student.get_full_name(),
                    'subject': subject.name,
                    'marks': float(mark.marks_obtained),
                    'exam_type': exam_type.name
                },
                description=f"{'Created' if created else 'Updated'} marks for {student.get_full_name()} in {subject.name}"
            )

        # Calculate and update student grade
        student_grade = calculate_student_grade(student, exam_type)

        result = {
            'success': True,
            'created_count': len(created_marks),
            'updated_count': len(updated_marks),
            'total_marks': sum(m.marks_obtained for m in created_marks + updated_marks),
            'percentage': float(student_grade.percentage) if student_grade else 0,
            'grade': student_grade.grade if student_grade else None
        }

        print(f"=== MARKS ENTRY COMPLETE ===")
        print(f"Result: {result}")
        print(f"Transaction committed successfully!\n")
        logger.info(f"=== MARKS ENTRY COMPLETE ===")
        logger.info(f"Result: {result}")

        return result

    @classmethod
    def _prepare_attendance_confirmation(cls, entities, user):
        """
        Prepare attendance confirmation.
        """
        # Validate required entities
        required = ['class', 'section']
        missing = [field for field in required if field not in entities]

        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        # Get class section
        try:
            class_obj = Class.objects.get(grade_number=entities['class'])
            section_obj = Section.objects.get(name=entities['section'])

            class_section = ClassSection.objects.filter(
                class_obj=class_obj,
                section=section_obj
            ).order_by('-academic_year').first()

            if not class_section:
                raise ValueError(f"Class {entities['class']}{entities['section']} not found")

        except Class.DoesNotExist:
            raise ValueError(f"Class {entities['class']} not found")
        except Section.DoesNotExist:
            raise ValueError(f"Section {entities['section']} not found")

        # Check teacher permissions
        if user.role == 'TEACHER':
            teacher_profile = getattr(user, 'teacher_profile', None)
            if teacher_profile:
                assigned_classes = teacher_profile.assigned_classes.all()
                if class_section not in assigned_classes:
                    raise PermissionError(f"You are not assigned to class {entities['class']}{entities['section']}")

        # Get students count
        students = Student.objects.filter(class_section=class_section, is_active=True)
        student_count = students.count()

        # Check if attendance already marked today
        today = date.today()
        existing_session = AttendanceSession.objects.filter(
            class_section=class_section,
            date=today
        ).exists()

        # Calculate actual student count (excluding the excluded rolls)
        excluded_rolls = entities.get('excluded_rolls', [])

        # If marking individual student, count is 1
        if 'roll_number' in entities:
            actual_count = 1
        else:
            actual_count = student_count - len(excluded_rolls) if excluded_rolls else student_count

        result = {
            'class_section': {
                'id': class_section.id,
                'name': f"{class_obj.name}{section_obj.name}"
            },
            'date': today.isoformat(),
            'total_students': student_count,  # Total students in class
            'student_count': actual_count,    # Students to be marked (after exclusions)
            'mark_all': entities.get('mark_all', False),
            'status': entities.get('status', 'PRESENT'),
            'excluded_rolls': excluded_rolls,
            'already_marked': existing_session,
            'action': 'update' if existing_session else 'create'
        }

        # Add roll_number if marking individual student
        if 'roll_number' in entities:
            result['roll_number'] = entities['roll_number']

        return result

    @classmethod
    @transaction.atomic
    def _execute_attendance(cls, entities, confirmation_data, user):
        """
        Execute attendance marking command.
        """
        class_section = ClassSection.objects.get(id=confirmation_data['class_section']['id'])
        today = date.today()

        # Create or get attendance session
        session, session_created = AttendanceSession.objects.get_or_create(
            class_section=class_section,
            date=today,
            defaults={'marked_by': user}
        )

        # Get all students
        students = Student.objects.filter(class_section=class_section, is_active=True)

        marked_count = 0
        excluded_rolls = confirmation_data.get('excluded_rolls', [])

        if confirmation_data['mark_all']:
            # Mark all students with specified status
            status = confirmation_data['status']

            for student in students:
                # Skip excluded roll numbers
                if student.roll_number in excluded_rolls:
                    continue

                _, created = AttendanceRecord.objects.update_or_create(
                    session=session,
                    student=student,
                    defaults={'status': status}
                )
                marked_count += 1

        elif 'roll_number' in confirmation_data:
            # Mark individual student
            roll_number = confirmation_data['roll_number']
            status = confirmation_data['status']

            student = students.filter(roll_number=roll_number).first()
            if student:
                _, created = AttendanceRecord.objects.update_or_create(
                    session=session,
                    student=student,
                    defaults={'status': status}
                )
                marked_count = 1
            else:
                raise ValueError(f"Student with roll number {roll_number} not found")

        # Create audit log
        AuditLog.objects.create(
            user=user,
            action='CREATE' if session_created else 'UPDATE',
            model_name='AttendanceSession',
            object_id=str(session.id),
            new_values={
                'class': confirmation_data['class_section']['name'],
                'date': str(today),
                'student_count': marked_count
            },
            description=f"Marked attendance for {confirmation_data['class_section']['name']} on {today}"
        )

        return {
            'success': True,
            'session_id': session.id,
            'marked_count': marked_count,
            'date': str(today)
        }

    @classmethod
    def _prepare_student_view_confirmation(cls, entities, user):
        """
        Prepare student view confirmation.
        """
        # Validate required entities
        required = ['roll_number', 'class', 'section']
        missing = [field for field in required if field not in entities]

        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        # Get student
        try:
            class_obj = Class.objects.get(grade_number=entities['class'])
            section_obj = Section.objects.get(name=entities['section'])

            class_section = ClassSection.objects.filter(
                class_obj=class_obj,
                section=section_obj
            ).order_by('-academic_year').first()

            if not class_section:
                raise ValueError(f"Class {entities['class']}{entities['section']} not found")

            student = Student.objects.get(
                roll_number=entities['roll_number'],
                class_section=class_section,
                is_active=True
            )

        except (Class.DoesNotExist, Section.DoesNotExist, Student.DoesNotExist) as e:
            raise ValueError(f"Student not found: {str(e)}")

        # Get student marks summary
        from apps.marks.utils import get_student_marks_summary
        marks_summary = get_student_marks_summary(student)

        # Get attendance percentage
        total_sessions = AttendanceSession.objects.filter(
            class_section=class_section
        ).count()

        present_count = AttendanceRecord.objects.filter(
            student=student,
            status='PRESENT'
        ).count()

        attendance_percentage = (present_count / total_sessions * 100) if total_sessions > 0 else 0

        return {
            'student': {
                'id': student.id,
                'name': student.get_full_name(),
                'roll_number': student.roll_number,
                'class': f"{class_obj.name}{section_obj.name}",
                'dob': student.date_of_birth.isoformat(),
                'gender': student.gender
            },
            'marks_summary': marks_summary,
            'attendance': {
                'total_sessions': total_sessions,
                'present_count': present_count,
                'percentage': round(attendance_percentage, 2)
            }
        }

    @classmethod
    def _execute_student_view(cls, entities, confirmation_data, user):
        """
        Execute student view command (read-only, no database changes).
        """
        # Create audit log for view action
        AuditLog.objects.create(
            user=user,
            action='VIEW',
            model_name='Student',
            object_id=str(confirmation_data['student']['id']),
            description=f"Viewed details of student {confirmation_data['student']['name']}"
        )

        return {
            'success': True,
            'message': 'Student details retrieved successfully'
        }

    @classmethod
    def _prepare_navigation_confirmation(cls, page_type, entities, user):
        """
        Prepare navigation confirmation for marks/attendance pages.

        Args:
            page_type (str): 'marks' or 'attendance'
            entities (dict): Extracted entities (None for simple navigation, contains class/section for specific sheet)
            user: User who issued the command
        """
        if entities and 'class' in entities and 'section' in entities:
            # Navigate to specific class sheet
            try:
                class_obj = Class.objects.get(grade_number=entities['class'])
                section_obj = Section.objects.get(name=entities['section'])

                class_section = ClassSection.objects.filter(
                    class_obj=class_obj,
                    section=section_obj
                ).order_by('-academic_year').first()

                if not class_section:
                    raise ValueError(f"Class {entities['class']}{entities['section']} not found")

                # Check teacher permissions
                if user.role == 'TEACHER':
                    teacher_profile = getattr(user, 'teacher_profile', None)
                    if teacher_profile:
                        assigned_classes = teacher_profile.assigned_classes.all()
                        if class_section not in assigned_classes:
                            raise PermissionError(f"You are not assigned to class {entities['class']}{entities['section']}")

                # Build URL with optional exam type parameter
                base_url = f"/{page_type}/{entities['class']}/{entities['section']}"
                exam_type = entities.get('exam_type')
                exam_type_display = entities.get('exam_type_display', '')

                if exam_type and page_type == 'marks':
                    url = f"{base_url}?examType={exam_type}"
                    message = f"Navigate to {page_type} sheet for class {class_obj.name}{section_obj.name} ({exam_type_display})"
                else:
                    url = base_url
                    message = f"Navigate to {page_type} sheet for class {class_obj.name}{section_obj.name}"

                result = {
                    'navigation_type': 'sheet',
                    'page_type': page_type,
                    'class': entities['class'],
                    'section': entities['section'],
                    'class_name': f"{class_obj.name}{section_obj.name}",
                    'url': url,
                    'message': message
                }

                # Include exam type info if present
                if exam_type:
                    result['exam_type'] = exam_type
                    result['exam_type_display'] = exam_type_display

                return result

            except Class.DoesNotExist:
                raise ValueError(f"Class {entities['class']} not found")
            except Section.DoesNotExist:
                raise ValueError(f"Section {entities['section']} not found")
        elif entities and 'tab' in entities:
            # Navigation to specific tab (for reports page)
            tab = entities['tab']
            tab_names = {
                'overview': 'Overview',
                'class': 'Class Reports',
                'student': 'Student Reports',
                'attendance': 'Attendance'
            }
            tab_display = tab_names.get(tab, tab.capitalize())
            return {
                'navigation_type': 'tab',
                'page_type': page_type,
                'tab': tab,
                'url': f"/{page_type}?tab={tab}",
                'message': f"Navigate to {tab_display} in Reports & Analytics"
            }
        else:
            # Simple navigation to list page
            return {
                'navigation_type': 'list',
                'page_type': page_type,
                'url': f"/{page_type}",
                'message': f"Navigate to {page_type} management page"
            }

    @classmethod
    def _prepare_exam_type_selection(cls, entities, user):
        """
        Prepare navigation to marks page with specific exam type selected.

        Args:
            entities (dict): Contains exam_type (UNIT_TEST, MIDTERM, FINAL)
            user: User who issued the command
        """
        exam_type = entities.get('exam_type', 'MIDTERM')
        exam_type_display = entities.get('exam_type_display', 'Midterm Exam')

        return {
            'navigation_type': 'exam_type',
            'page_type': 'marks',
            'exam_type': exam_type,
            'exam_type_display': exam_type_display,
            'url': f"/marks?examType={exam_type}",
            'message': f"Navigate to marks page with {exam_type_display} selected"
        }

    @classmethod
    def _prepare_question_sheet_navigation(cls, entities, user):
        """
        Prepare navigation to question-wise marks page.

        Expected entities:
        - roll_number: Student roll number
        - subject_code: Subject code (MATH, HINDI, etc.)
        - class/section: From context (optional)
        """
        # Validate required entities
        required = ['roll_number', 'subject_code']
        missing = [field for field in required if field not in entities or not entities[field]]

        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        # Map subject code to ID
        subject_mapping = {
            'MATH': 1,
            'HINDI': 2,
            'ENGLISH': 3,
            'SCIENCE': 4,
            'SOCIAL': 5,
        }

        subject_id = subject_mapping.get(entities['subject_code'])
        if not subject_id:
            raise ValueError(f"Unknown subject code: {entities['subject_code']}")

        # Get subject name
        try:
            subject = Subject.objects.get(id=subject_id)
        except Subject.DoesNotExist:
            raise ValueError(f"Subject not found")

        # Get student to verify existence and get class/section
        roll_number = entities['roll_number']

        # If class/section provided, use them
        if 'class' in entities and 'section' in entities:
            try:
                class_obj = Class.objects.get(grade_number=entities['class'])
                section_obj = Section.objects.get(name=entities['section'])

                class_section = ClassSection.objects.filter(
                    class_obj=class_obj,
                    section=section_obj
                ).order_by('-academic_year').first()

                if not class_section:
                    raise ValueError(f"Class {entities['class']}{entities['section']} not found")

                student = Student.objects.filter(
                    class_section=class_section,
                    roll_number=roll_number
                ).first()

                if not student:
                    raise ValueError(f"Student with roll number {roll_number} not found in class {entities['class']}{entities['section']}")

                class_num = entities['class']
                section = entities['section']

            except (Class.DoesNotExist, Section.DoesNotExist) as e:
                raise ValueError(f"Class or section not found: {str(e)}")
        else:
            # Try to find student without class context (search all active classes)
            student = Student.objects.filter(roll_number=roll_number).first()
            if not student:
                raise ValueError(f"Student with roll number {roll_number} not found")

            class_num = student.class_section.class_obj.grade_number
            section = student.class_section.section.name

        return {
            'navigation_type': 'question_sheet',
            'page_type': 'marks',
            'roll_number': roll_number,
            'subject_id': subject_id,
            'subject_name': subject.name,
            'class': class_num,
            'section': section,
            'student_name': student.name,
            'url': f"/marks/{class_num}/{section}/question/{roll_number}/{subject_id}",
            'message': f"Navigate to question-wise marks for {student.name} (Roll {roll_number}) in {subject.name}"
        }

    @classmethod
    def _execute_navigation(cls, intent, confirmation_data, user):
        """
        Execute navigation command (create audit log for tracking).
        """
        # Create audit log for navigation
        AuditLog.objects.create(
            user=user,
            action='VOICE_COMMAND',
            model_name='VoiceCommand',
            description=f"Voice navigation: {confirmation_data['message']}"
        )

        return {
            'success': True,
            'navigation': {
                'url': confirmation_data['url'],
                'type': confirmation_data['navigation_type'],
                'page_type': confirmation_data['page_type']
            },
            'message': confirmation_data['message']
        }

    @classmethod
    def _prepare_marks_update_confirmation(cls, entities, user):
        """
        Prepare marks update confirmation (similar to ENTER_MARKS but for updating existing marks).
        """
        # Use the same logic as marks entry
        return cls._prepare_marks_confirmation(entities, user)

    @classmethod
    def _execute_marks_update(cls, entities, confirmation_data, user):
        """
        Execute marks update command (same as marks entry, uses update_or_create).
        """
        # Use the same logic as marks entry (it already handles updates)
        return cls._execute_marks_entry(entities, confirmation_data, user)

    @classmethod
    def _prepare_question_marks_confirmation(cls, entities, user):
        """
        Prepare confirmation for question-wise marks update.
        """
        # Validate required entities
        required = ['roll_number', 'question_number', 'subject_code', 'marks_obtained']
        missing = [field for field in required if field not in entities]

        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        # Use context for class/section if not in entities
        if 'class' not in entities or 'section' not in entities:
            raise ValueError("Class and section must be provided or available from context")

        # Get student
        try:
            from apps.marks.models import QuestionWiseMarks

            class_obj = Class.objects.get(grade_number=entities['class'])
            section_obj = Section.objects.get(name=entities['section'])

            class_section = ClassSection.objects.filter(
                class_obj=class_obj,
                section=section_obj
            ).order_by('-academic_year').first()

            if not class_section:
                raise ValueError(f"Class {entities['class']}{entities['section']} not found")

            student = Student.objects.get(
                roll_number=entities['roll_number'],
                class_section=class_section,
                is_active=True
            )

            # Get subject
            subject = Subject.objects.get(code=entities['subject_code'])

            # Get or create Marks record
            exam_type = ExamType.objects.filter(
                code=settings.DEFAULT_EXAM_TYPE,
                is_active=True
            ).first()

            if not exam_type:
                raise ValueError("Default exam type not configured")

            marks_obj, _ = Marks.objects.get_or_create(
                student=student,
                subject=subject,
                exam_type=exam_type,
                defaults={
                    'marks_obtained': 0,
                    'max_marks': subject.max_marks,
                    'entered_by': user
                }
            )

            # Get existing question mark if any
            existing_question = QuestionWiseMarks.objects.filter(
                marks=marks_obj,
                question_number=entities['question_number']
            ).first()

            return {
                'student': {
                    'id': student.id,
                    'name': student.get_full_name(),
                    'roll_number': student.roll_number,
                    'class': f"{class_obj.name}{section_obj.name}"
                },
                'subject': {
                    'name': subject.name,
                    'code': subject.code
                },
                'question': {
                    'number': entities['question_number'],
                    'marks_obtained': entities['marks_obtained'],
                    'old_marks': float(existing_question.marks_obtained) if existing_question else 0,
                    'max_marks': float(existing_question.max_marks) if existing_question else 10
                },
                'marks_id': marks_obj.id,
                'exam_type': {
                    'id': exam_type.id,
                    'name': exam_type.name
                }
            }

        except Class.DoesNotExist:
            raise ValueError(f"Class {entities['class']} not found")
        except Section.DoesNotExist:
            raise ValueError(f"Section {entities['section']} not found")
        except Student.DoesNotExist:
            raise ValueError(f"Student with roll number {entities['roll_number']} not found in class {entities['class']}{entities['section']}")
        except Subject.DoesNotExist:
            raise ValueError(f"Subject {entities['subject_code']} not found")

    @classmethod
    @transaction.atomic
    def _execute_question_marks_update(cls, entities, confirmation_data, user):
        """
        Execute question-wise marks update command.
        """
        from apps.marks.models import QuestionWiseMarks
        from decimal import Decimal

        print("\n=== EXECUTING QUESTION MARKS UPDATE ===")
        print(f"confirmation_data: {confirmation_data}")
        print(f"entities: {entities}")

        marks_obj = Marks.objects.get(id=confirmation_data['marks_id'])
        question_number = confirmation_data['question']['number']
        marks_obtained = Decimal(str(entities['marks_obtained']))

        # Get max_marks from confirmation or use default
        max_marks = Decimal(str(confirmation_data['question'].get('max_marks', 10)))

        # Create or update question mark
        question_mark, created = QuestionWiseMarks.objects.update_or_create(
            marks=marks_obj,
            question_number=question_number,
            defaults={
                'max_marks': max_marks,
                'marks_obtained': marks_obtained,
                'entered_by': user
            }
        )

        print(f"Question mark {'CREATED' if created else 'UPDATED'}: Q{question_number} = {marks_obtained}/{max_marks}")

        # Recalculate total marks from all questions
        all_questions = QuestionWiseMarks.objects.filter(marks=marks_obj)
        total_obtained = sum(q.marks_obtained for q in all_questions)

        marks_obj.marks_obtained = total_obtained
        marks_obj.save()

        print(f"Recalculated total marks: {total_obtained}")
        print(f"=== QUESTION MARKS UPDATE COMPLETE ===\n")

        # Create audit log
        AuditLog.objects.create(
            user=user,
            action='UPDATE' if not created else 'CREATE',
            model_name='QuestionWiseMarks',
            object_id=str(question_mark.id),
            new_values={
                'question_number': question_number,
                'marks_obtained': float(marks_obtained),
                'max_marks': float(max_marks)
            },
            description=f"{'Updated' if not created else 'Created'} question {question_number} marks for {marks_obj.student.get_full_name()} - {marks_obj.subject.name}"
        )

        return {
            'success': True,
            'question_number': question_number,
            'marks_obtained': float(marks_obtained),
            'max_marks': float(max_marks),
            'total_marks': float(total_obtained),
            'action': 'created' if created else 'updated'
        }

    @classmethod
    def _prepare_batch_question_marks_confirmation(cls, entities, user):
        """
        Prepare confirmation for BATCH question-wise marks update.
        """
        # Validate required entities
        if 'updates' not in entities or not entities['updates']:
            raise ValueError("No updates found in batch request")

        if 'roll_number' not in entities:
            raise ValueError("Roll number required for batch update")

        if 'subject_code' not in entities:
            raise ValueError("Subject code required for batch update")

        # Use context for class/section if not in entities
        if 'class' not in entities or 'section' not in entities:
            raise ValueError("Class and section must be provided or available from context")

        # Get student and subject
        try:
            from apps.marks.models import QuestionWiseMarks

            class_obj = Class.objects.get(grade_number=entities['class'])
            section_obj = Section.objects.get(name=entities['section'])

            class_section = ClassSection.objects.filter(
                class_obj=class_obj,
                section=section_obj
            ).order_by('-academic_year').first()

            if not class_section:
                raise ValueError(f"Class {entities['class']}{entities['section']} not found")

            student = Student.objects.get(
                roll_number=entities['roll_number'],
                class_section=class_section,
                is_active=True
            )

            # Get subject
            subject = Subject.objects.get(code=entities['subject_code'])

            # Get or create Marks record
            exam_type = ExamType.objects.filter(
                code=settings.DEFAULT_EXAM_TYPE,
                is_active=True
            ).first()

            if not exam_type:
                raise ValueError("Default exam type not configured")

            marks_obj, _ = Marks.objects.get_or_create(
                student=student,
                subject=subject,
                exam_type=exam_type,
                defaults={
                    'marks_obtained': 0,
                    'max_marks': subject.max_marks,
                    'entered_by': user
                }
            )

            # Get existing question marks for all questions in the batch
            existing_questions = {
                q.question_number: float(q.marks_obtained)
                for q in QuestionWiseMarks.objects.filter(marks=marks_obj)
            }

            # Prepare update data with old values
            updates_with_old = []
            for update in entities['updates']:
                q_num = update['question_number']
                updates_with_old.append({
                    'question_number': q_num,
                    'marks_obtained': update['marks_obtained'],
                    'old_marks': existing_questions.get(q_num, 0),
                    'max_marks': 10  # Default, can be customized
                })

            return {
                'student': {
                    'id': student.id,
                    'name': student.get_full_name(),
                    'roll_number': student.roll_number,
                    'class': f"{class_obj.name}{section_obj.name}"
                },
                'subject': {
                    'name': subject.name,
                    'code': subject.code
                },
                'updates': updates_with_old,
                'marks_id': marks_obj.id,
                'exam_type': {
                    'id': exam_type.id,
                    'name': exam_type.name
                }
            }

        except Class.DoesNotExist:
            raise ValueError(f"Class {entities['class']} not found")
        except Section.DoesNotExist:
            raise ValueError(f"Section {entities['section']} not found")
        except Student.DoesNotExist:
            raise ValueError(f"Student with roll number {entities['roll_number']} not found")
        except Subject.DoesNotExist:
            raise ValueError(f"Subject {entities['subject_code']} not found")

    @classmethod
    @transaction.atomic
    def _execute_batch_question_marks_update(cls, entities, confirmation_data, user):
        """
        Execute BATCH question-wise marks update command.
        """
        from apps.marks.models import QuestionWiseMarks
        from decimal import Decimal

        print("\n=== EXECUTING BATCH QUESTION MARKS UPDATE ===")
        print(f"Number of updates: {len(confirmation_data['updates'])}")

        marks_obj = Marks.objects.get(id=confirmation_data['marks_id'])
        results = []

        # Apply all updates
        for update in confirmation_data['updates']:
            question_number = update['question_number']
            marks_obtained = Decimal(str(update['marks_obtained']))
            max_marks = Decimal(str(update.get('max_marks', 10)))

            # Create or update question mark
            question_mark, created = QuestionWiseMarks.objects.update_or_create(
                marks=marks_obj,
                question_number=question_number,
                defaults={
                    'max_marks': max_marks,
                    'marks_obtained': marks_obtained,
                    'entered_by': user
                }
            )

            results.append({
                'question_number': question_number,
                'marks_obtained': float(marks_obtained),
                'max_marks': float(max_marks),
                'action': 'created' if created else 'updated'
            })

            print(f"Q{question_number}: {marks_obtained}/{max_marks} ({'CREATED' if created else 'UPDATED'})")

            # Create audit log for each question
            AuditLog.objects.create(
                user=user,
                action='UPDATE' if not created else 'CREATE',
                model_name='QuestionWiseMarks',
                object_id=str(question_mark.id),
                new_values={
                    'question_number': question_number,
                    'marks_obtained': float(marks_obtained),
                    'max_marks': float(max_marks)
                },
                description=f"Batch: {'Updated' if not created else 'Created'} Q{question_number} for {marks_obj.student.get_full_name()}"
            )

        # Recalculate total marks from all questions
        all_questions = QuestionWiseMarks.objects.filter(marks=marks_obj)
        total_obtained = sum(q.marks_obtained for q in all_questions)

        marks_obj.marks_obtained = total_obtained
        marks_obj.save()

        print(f"Recalculated total marks: {total_obtained}")
        print(f"=== BATCH UPDATE COMPLETE ===\n")

        return {
            'success': True,
            'updates': results,
            'total_marks': float(total_obtained),
            'count': len(results)
        }

    @classmethod
    def _prepare_progress_report_confirmation(cls, entities, user):
        """
        Prepare confirmation for downloading student progress report.
        """
        # Validate required entities
        required = ['roll_number', 'class', 'section']
        missing = [field for field in required if field not in entities or not entities[field]]

        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}. Please specify student roll number, class and section.")

        # Get student
        try:
            class_obj = Class.objects.get(grade_number=entities['class'])
            section_obj = Section.objects.get(name=entities['section'])

            class_section = ClassSection.objects.filter(
                class_obj=class_obj,
                section=section_obj
            ).order_by('-academic_year').first()

            if not class_section:
                raise ValueError(f"Class {entities['class']}{entities['section']} not found")

            student = Student.objects.get(
                roll_number=entities['roll_number'],
                class_section=class_section,
                is_active=True
            )

        except Class.DoesNotExist:
            raise ValueError(f"Class {entities['class']} not found")
        except Section.DoesNotExist:
            raise ValueError(f"Section {entities['section']} not found")
        except Student.DoesNotExist:
            raise ValueError(f"Student with roll number {entities['roll_number']} not found in class {entities['class']}{entities['section']}")

        # Get student marks summary from database
        from apps.marks.utils import get_student_marks_summary, calculate_grade
        raw_marks_summary = get_student_marks_summary(student)

        # Transform marks_summary to format expected by frontend
        # The raw format is: {"Unit Test": {"marks": [...], "total_obtained": ..., ...}}
        # Frontend expects: {"subjects": [...], "total_obtained": ..., ...}
        marks_summary = {
            'subjects': [],
            'total_obtained': 0,
            'total_max': 0,
            'percentage': 0,
            'grade': None
        }

        # Aggregate marks from all exam types (or use specific exam type)
        for exam_name, exam_data in raw_marks_summary.items():
            # Add subjects from each exam
            for mark in exam_data.get('marks', []):
                marks_summary['subjects'].append({
                    'name': mark['subject'],
                    'marks_obtained': mark['marks_obtained'],
                    'max_marks': mark['max_marks'],
                    'exam_type': exam_name
                })

            # Add to totals
            marks_summary['total_obtained'] += exam_data.get('total_obtained', 0)
            marks_summary['total_max'] += exam_data.get('total_max', 0)

        # Calculate overall percentage and grade
        if marks_summary['total_max'] > 0:
            marks_summary['percentage'] = round(
                (marks_summary['total_obtained'] / marks_summary['total_max']) * 100, 2
            )
            marks_summary['grade'] = calculate_grade(marks_summary['percentage'])

        logger.info(f"Transformed marks_summary for progress report: {marks_summary}")

        # Get attendance summary
        total_sessions = AttendanceSession.objects.filter(
            class_section=class_section
        ).count()

        present_count = AttendanceRecord.objects.filter(
            student=student,
            status='PRESENT'
        ).count()

        attendance_percentage = (present_count / total_sessions * 100) if total_sessions > 0 else 0

        return {
            'action_type': 'download',
            'student': {
                'id': student.id,
                'name': student.get_full_name(),
                'roll_number': student.roll_number,
                'class': entities['class'],
                'section': entities['section'],
                'class_name': f"{class_obj.name}{section_obj.name}"
            },
            'marks_summary': marks_summary,
            'attendance': {
                'total_sessions': total_sessions,
                'present_count': present_count,
                'percentage': round(attendance_percentage, 2)
            },
            'message': f"Download progress report for {student.get_full_name()} (Roll {student.roll_number}, Class {class_obj.name}{section_obj.name})"
        }

    @classmethod
    def _execute_progress_report_download(cls, entities, confirmation_data, user):
        """
        Execute progress report download (returns data for frontend to generate PDF).
        """
        # Create audit log for download action
        AuditLog.objects.create(
            user=user,
            action='VIEW',
            model_name='ProgressReport',
            object_id=str(confirmation_data['student']['id']),
            new_values={
                'student': confirmation_data['student']['name'],
                'class': confirmation_data['student']['class_name'],
                'roll_number': confirmation_data['student']['roll_number']
            },
            description=f"Downloaded progress report for {confirmation_data['student']['name']}"
        )

        # Return all data needed for the frontend to generate PDF
        return {
            'success': True,
            'action': 'download_progress_report',
            'student': confirmation_data['student'],
            'marks_summary': confirmation_data['marks_summary'],
            'attendance': confirmation_data['attendance'],
            'message': f"Progress report ready for {confirmation_data['student']['name']}"
        }

    # ============================================================
    # FEE MANAGEMENT METHODS
    # ============================================================

    @classmethod
    def _prepare_fee_collection_confirmation(cls, entities, user):
        """
        Prepare fee collection confirmation — looks up student, validates amount.
        """
        from apps.fees.models import FeeStructure, FeePayment, FeeDiscount
        from django.db.models.functions import Coalesce
        from django.db.models import Sum
        from decimal import Decimal

        # Require either roll_number or student_name, plus amount
        has_roll = 'roll_number' in entities and entities['roll_number']
        has_name = 'student_name' in entities and entities['student_name']
        if not has_roll and not has_name:
            raise ValueError("Missing student identifier. Provide roll number or student name.")
        if 'amount' not in entities or not entities['amount']:
            raise ValueError("Missing required field: amount")

        from django.db.models import Q

        has_class = 'class' in entities and entities['class']
        has_section = 'section' in entities and entities['section']

        try:
            if has_class and has_section:
                # Class and section provided — scoped lookup
                class_obj = Class.objects.get(grade_number=entities['class'])
                section_obj = Section.objects.get(name=entities['section'])
                class_section = ClassSection.objects.filter(
                    class_obj=class_obj, section=section_obj
                ).order_by('-academic_year').first()

                if not class_section:
                    raise ValueError(f"Class {entities['class']}{entities['section']} not found")

                if has_roll:
                    student = Student.objects.get(
                        roll_number=entities['roll_number'],
                        class_section=class_section,
                        is_active=True
                    )
                else:
                    # Name search within class
                    name_parts = entities['student_name'].strip().split()
                    if len(name_parts) >= 2:
                        first, last = name_parts[0], ' '.join(name_parts[1:])
                        students = Student.objects.filter(
                            Q(first_name__iexact=first, last_name__iexact=last) |
                            Q(first_name__icontains=first, last_name__icontains=last),
                            class_section=class_section, is_active=True
                        ).distinct()
                    else:
                        students = Student.objects.filter(
                            Q(first_name__iexact=name_parts[0]) | Q(last_name__iexact=name_parts[0]),
                            class_section=class_section, is_active=True
                        )
                    if students.count() == 0:
                        raise ValueError(f"No student named '{entities['student_name']}' in Class {entities['class']}{entities['section']}")
                    elif students.count() > 1:
                        names_list = ', '.join(f"{s.get_full_name()} (Roll {s.roll_number})" for s in students[:5])
                        raise ValueError(f"Multiple students match '{entities['student_name']}': {names_list}. Please specify roll number.")
                    student = students.first()
            else:
                # No class/section — search across all classes
                if has_roll:
                    students = Student.objects.filter(
                        roll_number=entities['roll_number'], is_active=True
                    ).select_related('class_section__class_obj', 'class_section__section')
                else:
                    name_parts = entities['student_name'].strip().split()
                    if len(name_parts) >= 2:
                        first, last = name_parts[0], ' '.join(name_parts[1:])
                        students = Student.objects.filter(
                            Q(first_name__iexact=first, last_name__iexact=last) |
                            Q(first_name__icontains=first, last_name__icontains=last),
                            is_active=True
                        ).select_related('class_section__class_obj', 'class_section__section').distinct()
                    else:
                        students = Student.objects.filter(
                            Q(first_name__iexact=name_parts[0]) | Q(last_name__iexact=name_parts[0]),
                            is_active=True
                        ).select_related('class_section__class_obj', 'class_section__section')

                if students.count() == 0:
                    identifier = entities.get('student_name') or f"roll {entities.get('roll_number')}"
                    raise ValueError(f"No student found matching '{identifier}'")
                elif students.count() == 1:
                    student = students.first()
                    class_section = student.class_section
                    class_obj = class_section.class_obj
                    section_obj = class_section.section
                else:
                    # Multiple matches — return list for user to select
                    student_list = []
                    for s in students.order_by('class_section__class_obj__grade_number', 'class_section__section__name'):
                        cs = s.class_section
                        student_list.append({
                            'id': s.id,
                            'name': s.get_full_name(),
                            'roll_number': s.roll_number,
                            'class': f"{cs.class_obj.name}{cs.section.name}",
                            'class_grade': cs.class_obj.grade_number,
                            'section_name': cs.section.name,
                            'father_name': s.father_name or '',
                        })
                    identifier = entities.get('student_name') or f"Roll {entities.get('roll_number')}"
                    return {
                        'navigation_type': 'student_select',
                        'message': f"Multiple students found for '{identifier}'. Please select one:",
                        'students': student_list,
                        'amount': entities['amount'],
                        'payment_method': entities.get('payment_method', 'CASH'),
                    }

        except Class.DoesNotExist:
            raise ValueError(f"Class {entities.get('class')} not found")
        except Section.DoesNotExist:
            raise ValueError(f"Section {entities.get('section')} not found")
        except Student.DoesNotExist:
            raise ValueError(f"Student with roll {entities.get('roll_number')} not found in {entities.get('class')}{entities.get('section')}")

        # Get fee structures and balance
        all_structures = FeeStructure.objects.filter(
            class_obj=class_obj, is_active=True,
            academic_year=class_section.academic_year
        )
        total_fees = all_structures.aggregate(
            total=Coalesce(Sum('amount'), Decimal('0'))
        )['total']

        paid = FeePayment.objects.filter(
            student=student,
            fee_structure__class_obj=class_obj,
            fee_structure__academic_year=class_section.academic_year,
            payment_status__in=['PAID', 'PARTIAL'],
        ).aggregate(total=Coalesce(Sum('amount_paid'), Decimal('0')))['total']

        discount = FeeDiscount.objects.filter(
            student=student,
            fee_structure__class_obj=class_obj,
            fee_structure__academic_year=class_section.academic_year,
            is_active=True,
        ).aggregate(total=Coalesce(Sum('discount_amount'), Decimal('0')))['total']

        balance = total_fees - paid - discount

        # If fee_type specified, prefer that structure; otherwise pick first
        requested_fee_type = entities.get('fee_type')
        fee_structure = None
        fee_type_display = None

        if requested_fee_type:
            fee_structure = all_structures.filter(fee_type=requested_fee_type).first()
            if fee_structure:
                fee_type_display = fee_structure.get_fee_type_display()
            else:
                # Fee type not found for this class — fall back to first
                fee_structure = all_structures.first()

        if not fee_structure:
            fee_structure = all_structures.first()

        if fee_structure and not fee_type_display:
            fee_type_display = fee_structure.get_fee_type_display()

        return {
            'student': {
                'id': student.id,
                'name': student.get_full_name(),
                'roll_number': student.roll_number,
                'class': f"{class_obj.name}{section_obj.name}",
            },
            'fee_structure_id': fee_structure.id if fee_structure else None,
            'fee_type': requested_fee_type or (fee_structure.fee_type if fee_structure else None),
            'fee_type_display': fee_type_display,
            'amount': entities['amount'],
            'payment_method': entities.get('payment_method', 'CASH'),
            'total_fees': float(total_fees),
            'already_paid': float(paid),
            'balance_before': float(balance),
            'balance_after': float(balance - entities['amount']),
            'navigation_type': 'fee_collection',
            'page_type': 'fees',
            'url': f"/fees/{entities['class']}/{entities['section']}",
            'message': f"Collect Rs. {entities['amount']} from {student.get_full_name()} (Roll {student.roll_number}, Class {class_obj.name}{section_obj.name}) via {entities.get('payment_method', 'CASH')}",
        }

    @classmethod
    @transaction.atomic
    def _execute_fee_collection(cls, entities, confirmation_data, user):
        """
        Execute fee collection — creates FeePayment record with receipt.
        """
        from apps.fees.models import FeeStructure, FeePayment
        from decimal import Decimal

        student = Student.objects.get(id=confirmation_data['student']['id'])
        fee_structure = FeeStructure.objects.get(id=confirmation_data['fee_structure_id'])

        amount = Decimal(str(confirmation_data['amount']))
        payment_method = confirmation_data.get('payment_method', 'CASH')

        balance_before = Decimal(str(confirmation_data['balance_before']))
        if amount >= balance_before:
            payment_status = 'PAID'
        else:
            payment_status = 'PARTIAL'

        payment = FeePayment.objects.create(
            student=student,
            fee_structure=fee_structure,
            amount_paid=amount,
            payment_method=payment_method,
            payment_status=payment_status,
            collected_by=user,
            remarks=f"Collected via voice command",
        )

        # Audit log
        AuditLog.objects.create(
            user=user,
            action='CREATE',
            model_name='FeePayment',
            object_id=str(payment.id),
            description=f"Voice fee collection: Rs. {amount} from {student.get_full_name()} ({payment.receipt_number})"
        )

        return {
            'success': True,
            'action': 'fee_collected',
            'receipt_number': payment.receipt_number,
            'amount': float(amount),
            'student_name': student.get_full_name(),
            'roll_number': student.roll_number,
            'class_name': f"{student.class_section.class_obj.name}{student.class_section.section.name}",
            'payment_method': payment.get_payment_method_display(),
            'fee_type_display': fee_structure.get_fee_type_display(),
            'term_display': fee_structure.get_term_display(),
            'collected_by_name': user.get_full_name() if hasattr(user, 'get_full_name') else str(user),
            'payment_date': payment.payment_date.strftime('%d/%m/%Y'),
            'payment_time': payment.payment_date.strftime('%I:%M %p'),
            'payment_status': payment_status,
            'message': f"Rs. {amount} collected. Receipt: {payment.receipt_number}",
        }

    @classmethod
    def _prepare_fee_details_confirmation(cls, entities, user):
        """
        Prepare fee details view for a specific student.
        Shows total fees, paid, balance, payment history.
        """
        from apps.fees.models import FeeStructure, FeePayment, FeeDiscount
        from django.db.models.functions import Coalesce
        from django.db.models import Sum
        from decimal import Decimal

        roll_number = entities.get('roll_number')
        if not roll_number:
            raise ValueError("Missing roll number. Example: 'Show fee details of student 5 class 4B'")

        # Get class/section from entities or context
        grade = entities.get('class')
        section_name = entities.get('section')

        try:
            if grade and section_name:
                # Class and section provided — direct lookup
                class_obj = Class.objects.get(grade_number=grade)
                section_obj = Section.objects.get(name=section_name)
                class_section = ClassSection.objects.filter(
                    class_obj=class_obj, section=section_obj
                ).order_by('-academic_year').first()

                if not class_section:
                    raise ValueError(f"Class {grade}{section_name} not found")

                student = Student.objects.get(
                    roll_number=roll_number,
                    class_section=class_section,
                    is_active=True
                )
            else:
                # Class/section not provided — search across all active classes
                students = Student.objects.filter(
                    roll_number=roll_number,
                    is_active=True
                ).select_related('class_section__class_obj', 'class_section__section')

                if students.count() == 0:
                    raise ValueError(f"Student with roll {roll_number} not found")
                elif students.count() > 1:
                    # Multiple students with same roll in different classes — show selection list
                    student_list = []
                    for s in students.order_by('class_section__class_obj__grade_number', 'class_section__section__name'):
                        cs = s.class_section
                        student_list.append({
                            'id': s.id,
                            'name': s.get_full_name(),
                            'roll_number': s.roll_number,
                            'class': f"{cs.class_obj.name}{cs.section.name}",
                            'class_grade': cs.class_obj.grade_number,
                            'section_name': cs.section.name,
                            'father_name': s.father_name or '',
                        })
                    return {
                        'navigation_type': 'student_select',
                        'message': f"Multiple students found with roll {roll_number}. Please select one:",
                        'students': student_list,
                        'intent_type': 'SHOW_FEE_DETAILS',
                    }
                else:
                    student = students.first()

                class_section = student.class_section
                class_obj = class_section.class_obj
                section_obj = class_section.section

        except Class.DoesNotExist:
            raise ValueError(f"Class {grade} not found")
        except Section.DoesNotExist:
            raise ValueError(f"Section {section_name} not found")
        except Student.DoesNotExist:
            raise ValueError(f"Student with roll {roll_number} not found in {grade}{section_name}")

        # Get fee structures
        structures = FeeStructure.objects.filter(
            class_obj=class_obj, is_active=True,
            academic_year=class_section.academic_year
        )
        total_fees = structures.aggregate(
            total=Coalesce(Sum('amount'), Decimal('0'))
        )['total']

        # Get payments
        payments = FeePayment.objects.filter(
            student=student,
            fee_structure__class_obj=class_obj,
            fee_structure__academic_year=class_section.academic_year,
            payment_status__in=['PAID', 'PARTIAL'],
        ).order_by('-payment_date')

        total_paid = payments.aggregate(
            total=Coalesce(Sum('amount_paid'), Decimal('0'))
        )['total']

        # Get discounts
        discount = FeeDiscount.objects.filter(
            student=student,
            fee_structure__class_obj=class_obj,
            fee_structure__academic_year=class_section.academic_year,
            is_active=True,
        ).aggregate(total=Coalesce(Sum('discount_amount'), Decimal('0')))['total']

        balance = total_fees - total_paid - discount

        # Recent payments for history
        recent_payments = []
        for p in payments[:5]:
            recent_payments.append({
                'receipt_number': p.receipt_number,
                'amount': float(p.amount_paid),
                'method': p.payment_method,
                'date': p.payment_date.strftime('%d/%m/%Y') if p.payment_date else '',
                'status': p.payment_status,
            })

        # Fee structure breakdown
        fee_breakdown = []
        for fs in structures:
            struct_paid = FeePayment.objects.filter(
                student=student, fee_structure=fs,
                payment_status__in=['PAID', 'PARTIAL'],
            ).aggregate(total=Coalesce(Sum('amount_paid'), Decimal('0')))['total']
            fee_breakdown.append({
                'name': fs.get_fee_type_display(),
                'amount': float(fs.amount),
                'paid': float(struct_paid),
                'balance': float(fs.amount - struct_paid),
            })

        # Determine status
        if balance <= 0:
            fee_status = 'PAID'
        elif total_paid > 0:
            fee_status = 'PARTIAL'
        else:
            fee_status = 'UNPAID'

        return {
            'navigation_type': 'fee_details',
            'page_type': 'fees',
            'student': {
                'id': student.id,
                'name': student.get_full_name(),
                'roll_number': student.roll_number,
                'class': f"{class_obj.name}{section_obj.name}",
            },
            'total_fees': float(total_fees),
            'total_paid': float(total_paid),
            'discount': float(discount),
            'balance': float(balance),
            'fee_status': fee_status,
            'fee_breakdown': fee_breakdown,
            'recent_payments': recent_payments,
            'url': f"/fees/{grade}/{section_name}",
            'message': f"Fee details for {student.get_full_name()} (Roll {roll_number}, Class {class_obj.name}{section_obj.name})",
        }

    @classmethod
    def _prepare_fee_page_navigation(cls, entities, user):
        """
        Prepare navigation to fee page (list or specific class).
        """
        if 'class' in entities and 'section' in entities:
            try:
                class_obj = Class.objects.get(grade_number=entities['class'])
                section_obj = Section.objects.get(name=entities['section'])
                return {
                    'navigation_type': 'sheet',
                    'page_type': 'fees',
                    'class': entities['class'],
                    'section': entities['section'],
                    'url': f"/fees/{entities['class']}/{entities['section']}",
                    'message': f"Navigate to fees for class {class_obj.name}{section_obj.name}",
                }
            except (Class.DoesNotExist, Section.DoesNotExist):
                pass

        # Class specified but no section — show available sections to pick from
        if 'class' in entities:
            grade = entities['class']
            try:
                class_obj = Class.objects.get(grade_number=grade)
                sections = Section.objects.all().order_by('name')
                section_options = [
                    {'name': s.name, 'url': f"/fees/{grade}/{s.name}"}
                    for s in sections
                ]
                return {
                    'navigation_type': 'section_select',
                    'page_type': 'fees',
                    'class': grade,
                    'class_name': class_obj.name,
                    'sections': section_options,
                    'message': f"Select a section for class {class_obj.name} fee collection",
                }
            except Class.DoesNotExist:
                pass

        return {
            'navigation_type': 'list',
            'page_type': 'fees',
            'url': '/fees',
            'message': 'Navigate to fee management page',
        }

    @classmethod
    def _prepare_defaulters_confirmation(cls, entities, user):
        """
        Prepare defaulters list for confirmation dialog.
        """
        from apps.fees.models import FeeStructure, FeePayment, FeeDiscount
        from django.db.models.functions import Coalesce
        from django.db.models import Sum
        from decimal import Decimal

        class_filter = entities.get('class')
        students = Student.objects.filter(is_active=True)
        if class_filter:
            students = students.filter(class_section__class_obj__grade_number=class_filter)

        defaulter_list = []
        for student in students[:100]:  # Limit for performance
            class_obj = student.class_section.class_obj
            academic_year = student.class_section.academic_year

            total_fees = FeeStructure.objects.filter(
                class_obj=class_obj, is_active=True, academic_year=academic_year
            ).aggregate(total=Coalesce(Sum('amount'), Decimal('0')))['total']

            if total_fees == 0:
                continue

            paid = FeePayment.objects.filter(
                student=student,
                fee_structure__class_obj=class_obj,
                fee_structure__academic_year=academic_year,
                payment_status__in=['PAID', 'PARTIAL'],
            ).aggregate(total=Coalesce(Sum('amount_paid'), Decimal('0')))['total']

            discount = FeeDiscount.objects.filter(
                student=student,
                fee_structure__class_obj=class_obj,
                fee_structure__academic_year=academic_year,
                is_active=True,
            ).aggregate(total=Coalesce(Sum('discount_amount'), Decimal('0')))['total']

            balance = total_fees - paid - discount
            if balance > 0:
                cs = student.class_section
                defaulter_list.append({
                    'student_id': student.id,
                    'name': student.get_full_name(),
                    'roll_number': student.roll_number,
                    'class_name': f"{cs.class_obj.name}{cs.section.name}",
                    'total_fees': float(total_fees),
                    'paid': float(paid),
                    'balance': float(balance),
                })

        defaulter_list.sort(key=lambda x: x['balance'], reverse=True)

        class_label = f" Class {class_filter}" if class_filter else ""
        return {
            'navigation_type': 'defaulters',
            'page_type': 'fees',
            'defaulters': defaulter_list[:20],
            'total_count': len(defaulter_list),
            'url': '/fee-reports?tab=defaulters',
            'message': f"Found {len(defaulter_list)} students with pending fees{class_label}",
        }

    @classmethod
    def _prepare_today_collection_confirmation(cls, entities, user):
        """
        Prepare today's collection summary.
        """
        from apps.fees.models import FeePayment
        from django.db.models.functions import Coalesce
        from django.db.models import Sum
        from decimal import Decimal

        today_payments = FeePayment.objects.filter(payment_date__date=date.today())

        total = today_payments.aggregate(
            total=Coalesce(Sum('amount_paid'), Decimal('0'))
        )['total']

        by_method = list(today_payments.values('payment_method').annotate(
            total=Sum('amount_paid'),
            count=models.Count('id'),
        ).order_by('payment_method'))

        return {
            'navigation_type': 'today_collection',
            'page_type': 'fees',
            'total_collected': float(total),
            'transaction_count': today_payments.count(),
            'by_payment_method': by_method,
            'date': date.today().isoformat(),
            'url': '/fee-reports?tab=today',
            'message': f"Today's collection: Rs. {total} ({today_payments.count()} transactions)",
        }
