"""
Command executor for voice commands.
Prepares confirmation data and executes confirmed commands.
"""
import logging
from django.db import transaction
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
        elif intent == 'OPEN_MARKS_SHEET':
            return cls._prepare_navigation_confirmation('marks', entities, user)
        elif intent == 'OPEN_ATTENDANCE_SHEET':
            return cls._prepare_navigation_confirmation('attendance', entities, user)
        elif intent == 'UPDATE_MARKS':
            return cls._prepare_marks_update_confirmation(entities, user)
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
        elif intent in ['NAVIGATE_MARKS', 'NAVIGATE_ATTENDANCE', 'OPEN_MARKS_SHEET', 'OPEN_ATTENDANCE_SHEET']:
            return cls._execute_navigation(intent, confirmation_data, user)
        elif intent == 'UPDATE_MARKS':
            return cls._execute_marks_update(entities, confirmation_data, user)
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
            'student_count': actual_count,
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

                return {
                    'navigation_type': 'sheet',
                    'page_type': page_type,
                    'class': entities['class'],
                    'section': entities['section'],
                    'class_name': f"{class_obj.name}{section_obj.name}",
                    'url': f"/{page_type}/{entities['class']}/{entities['section']}",
                    'message': f"Navigate to {page_type} sheet for class {class_obj.name}{section_obj.name}"
                }

            except Class.DoesNotExist:
                raise ValueError(f"Class {entities['class']} not found")
            except Section.DoesNotExist:
                raise ValueError(f"Section {entities['section']} not found")
        else:
            # Simple navigation to list page
            return {
                'navigation_type': 'list',
                'page_type': page_type,
                'url': f"/{page_type}",
                'message': f"Navigate to {page_type} management page"
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
            action='NAVIGATE',
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
