"""
API views for voice processing.
"""
import logging
import re
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import VoiceCommand
from .serializers import (
    VoiceCommandUploadSerializer,
    VoiceCommandSerializer,
    VoiceCommandConfirmSerializer,
    VoiceCommandListSerializer
)
from .speech_to_text import WhisperTranscriber
from .intent_extractor import IntentExtractor, EntityExtractor
from .command_executor import CommandExecutor

logger = logging.getLogger(__name__)


class VoiceCommandViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for voice command history.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = VoiceCommandListSerializer

    def get_queryset(self):
        """Filter commands to only show user's own commands."""
        return VoiceCommand.objects.filter(user=self.request.user)

    def retrieve(self, request, pk=None):
        """Get detailed view of a voice command."""
        command = get_object_or_404(VoiceCommand, pk=pk, user=request.user)
        serializer = VoiceCommandSerializer(command)
        return Response(serializer.data)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_voice_command(request):
    """
    Upload and process a voice command audio file.

    Steps:
    1. Validate audio file
    2. Transcribe using Whisper
    3. Extract intent and entities
    4. Prepare confirmation data
    5. Return confirmation data for user approval
    """
    try:
        # Validate request
        serializer = VoiceCommandUploadSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Validation failed: {serializer.errors}")
            logger.error(f"Request data keys: {request.data.keys()}")
            logger.error(f"Request FILES keys: {request.FILES.keys()}")
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        audio_file = serializer.validated_data['audio_file']

        # Get context information (current page context)
        context_class = request.data.get('context_class')
        context_section = request.data.get('context_section')
        context_roll_number = request.data.get('context_roll_number')
        context_subject_id = request.data.get('context_subject_id')
        context_page = request.data.get('context_page', '')

        # Get live transcript from Web Speech API (if available)
        live_transcript = request.data.get('live_transcript')

        # Create voice command record
        voice_command = VoiceCommand.objects.create(
            user=request.user,
            audio_file=audio_file,
            status=VoiceCommand.Status.PENDING_CONFIRMATION
        )

        # Step 1: Transcribe audio
        try:
            # Use live transcript from frontend if available, otherwise use Whisper
            if live_transcript and live_transcript.strip():
                logger.info(f"Using live transcript from Web Speech API: {live_transcript}")
                voice_command.transcription = live_transcript.strip()
                voice_command.save()
            else:
                logger.info("No live transcript, using Whisper for transcription")
                transcription_result = WhisperTranscriber.transcribe(
                    voice_command.audio_file.path
                )
                voice_command.transcription = transcription_result['text']
                voice_command.save()

        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            voice_command.status = VoiceCommand.Status.FAILED
            voice_command.error_message = f"Transcription failed: {str(e)}"
            voice_command.save()
            return Response(
                {'error': 'Failed to transcribe audio', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Step 2: Extract intent
        import sys
        print(f"\n=== VOICE COMMAND PROCESSING ===", flush=True)
        print(f"Transcription text: '{voice_command.transcription}'", flush=True)
        sys.stdout.flush()
        logger.info(f"=== VOICE COMMAND PROCESSING ===")
        logger.info(f"Transcription text: '{voice_command.transcription}'")

        # CRITICAL: Normalize text BEFORE intent extraction
        normalized_text = IntentExtractor.normalize_stt_text(voice_command.transcription)
        print(f"Normalized text: '{normalized_text}'", flush=True)
        sys.stdout.flush()
        logger.info(f"Normalized text: '{normalized_text}'")

        # Use normalized text for intent extraction
        intent = IntentExtractor.extract_intent(normalized_text)
        print(f"Detected intent: {intent}", flush=True)
        sys.stdout.flush()
        logger.info(f"Detected intent: {intent}")

        # ============================================================
        # ROLE-BASED INTENT ENFORCEMENT
        # Accountants can only use fee-related intents
        # Teachers can only use marks/attendance-related intents
        # ============================================================
        user_role = getattr(request.user, 'role', 'TEACHER')

        ACCOUNTANT_INTENTS = {
            'COLLECT_FEE', 'SHOW_FEE_DETAILS', 'OPEN_FEE_PAGE',
            'SHOW_DEFAULTERS', 'TODAY_COLLECTION', 'NAVIGATE_FEE_REPORTS',
            'NAVIGATE_DASHBOARD', 'CANCEL', 'UNKNOWN', 'SELECT_SECTION', 'SELECT_STUDENT',
        }
        TEACHER_INTENTS = {
            'UPDATE_MARKS', 'ENTER_MARKS', 'BATCH_UPDATE_MARKS', 'MARK_ATTENDANCE', 'VIEW_STUDENT',
            'NAVIGATE_MARKS', 'NAVIGATE_ATTENDANCE', 'NAVIGATE_REPORTS',
            'NAVIGATE_CLASS_REPORT', 'NAVIGATE_STUDENT_REPORT', 'NAVIGATE_ATTENDANCE_REPORT',
            'OPEN_MARKS_SHEET', 'OPEN_ATTENDANCE_SHEET', 'SELECT_EXAM_TYPE',
            'DOWNLOAD_PROGRESS_REPORT', 'BATCH_UPDATE_QUESTION_MARKS',
            'UPDATE_QUESTION_MARKS', 'OPEN_QUESTION_SHEET',
            'NAVIGATE_DASHBOARD', 'CANCEL', 'UNKNOWN', 'SELECT_SECTION',
        }

        if user_role == 'ACCOUNTANT' and intent not in ACCOUNTANT_INTENTS:
            logger.info(f"[ROLE-BLOCK] Accountant tried teacher intent '{intent}', blocking")
            # Redirect generic navigation to fee equivalents
            if intent == 'NAVIGATE_REPORTS':
                intent = 'NAVIGATE_FEE_REPORTS'
            elif intent in ('NAVIGATE_MARKS', 'OPEN_MARKS_SHEET'):
                intent = 'OPEN_FEE_PAGE'
            elif intent == 'NAVIGATE_ATTENDANCE':
                # Accountants don't have attendance — redirect to dashboard
                intent = 'NAVIGATE_DASHBOARD'
            else:
                intent = 'NAVIGATE_DASHBOARD'
        elif user_role != 'ACCOUNTANT' and intent in ('COLLECT_FEE', 'SHOW_FEE_DETAILS', 'OPEN_FEE_PAGE', 'SHOW_DEFAULTERS', 'TODAY_COLLECTION', 'NAVIGATE_FEE_REPORTS'):
            logger.info(f"[ROLE-BLOCK] Teacher tried accountant intent '{intent}', blocking")
            intent = 'NAVIGATE_DASHBOARD'

        # Page-aware: "go to reports" from fee page → fee reports
        if intent == 'NAVIGATE_REPORTS':
            fee_pages = ['/fees', '/fee-reports']
            on_fee_page = context_page and any(context_page.startswith(p) for p in fee_pages)
            if on_fee_page or user_role == 'ACCOUNTANT':
                logger.info(f"[PAGE-CONTEXT] Redirecting NAVIGATE_REPORTS → NAVIGATE_FEE_REPORTS")
                intent = 'NAVIGATE_FEE_REPORTS'

        # Page-aware: generic open/navigate from attendance page → stay in attendance context
        if context_page and context_page.startswith('/attendance'):
            if intent == 'OPEN_MARKS_SHEET':
                logger.info(f"[PAGE-CONTEXT] Redirecting OPEN_MARKS_SHEET → OPEN_ATTENDANCE_SHEET (user is on attendance page)")
                intent = 'OPEN_ATTENDANCE_SHEET'
            elif intent == 'NAVIGATE_MARKS':
                logger.info(f"[PAGE-CONTEXT] Redirecting NAVIGATE_MARKS → NAVIGATE_ATTENDANCE (user is on attendance page)")
                intent = 'NAVIGATE_ATTENDANCE'

        voice_command.intent = intent
        voice_command.save()

        # Handle CANCEL intent - user wants to cancel/stop/undo
        if intent == 'CANCEL':
            logger.info("Cancel command received")
            voice_command.status = VoiceCommand.Status.REJECTED
            voice_command.save()

            return Response(
                {
                    'command_id': voice_command.id,
                    'transcription': voice_command.transcription,
                    'intent': 'CANCEL',
                    'confirmation_data': {
                        'message': 'Command cancelled.',
                        'action': 'close',  # Tell frontend to close dialog
                        'needs_confirmation': False
                    },
                    'needs_confirmation': False
                },
                status=status.HTTP_200_OK
            )

        if intent == 'UNKNOWN':
            # CRITICAL: Return CLARIFY intent instead of 400 error
            # This allows frontend to show helpful message instead of crashing
            voice_command.status = VoiceCommand.Status.PENDING_CONFIRMATION
            voice_command.save()

            # Role-aware examples so users only see relevant commands
            user_role = getattr(request.user, 'role', 'TEACHER')
            if user_role == 'ACCOUNTANT':
                examples = [
                    'Fee: "Collect 5000 from roll 12 class 6A cash"',
                    'Reports: "Show defaulters" or "Today\'s collection"',
                    'Navigate: "Open fee collections" or "Open fee reports"',
                    'Inquiry: "Show fee details of student 12345"',
                ]
            else:
                examples = [
                    'Navigate: "Open class 1A marks" or "Go to class 2B attendance"',
                    'Subject marks: "Update marks for student 1 maths 90 hindi 80"',
                    'Question marks: "Update question 3 to 8 marks"',
                    'Attendance: "Mark all present" or "Mark attendance for class 8B"',
                    'Fee: "Collect 5000 from roll 12 class 6A cash"',
                    'Reports: "Show defaulters" or "Today\'s collection"',
                ]

            return Response(
                {
                    'command_id': voice_command.id,
                    'transcription': voice_command.transcription,
                    'intent': 'CLARIFY',
                    'confirmation_data': {
                        'message': 'I could not understand your command. Please try again with one of these formats:',
                        'examples': examples,
                        'needs_confirmation': False
                    },
                    'needs_confirmation': False
                },
                status=status.HTTP_200_OK  # 200 OK, not 400!
            )

        # Handle SELECT_SECTION intent - user specified class but not section
        if intent == 'SELECT_SECTION':
            from apps.academics.models import Class, Section, ClassSection

            # Extract class number from normalized text
            class_number = None

            # Check for word forms (first, second, third)
            word_to_num = {'first': 1, 'second': 2, 'third': 3}
            for word, num in word_to_num.items():
                if word in normalized_text.lower():
                    class_number = num
                    break

            # Check for numeric forms if not found
            if class_number is None:
                import re
                # Match patterns like "1st", "2nd", "class 1", etc.
                match = re.search(r'(\d+)', normalized_text)
                if match:
                    class_number = int(match.group(1))

            if class_number:
                try:
                    # Get the class object
                    class_obj = Class.objects.filter(grade_number=class_number).first()

                    if class_obj:
                        # Get all sections available for this class
                        class_sections = ClassSection.objects.filter(
                            class_obj=class_obj
                        ).select_related('section').order_by('section__name')

                        # Context-aware URL: use current page to determine target
                        if user_role == 'ACCOUNTANT':
                            url_prefix = '/fees'
                            page_label = 'fee collection'
                        elif context_page and context_page.startswith('/attendance'):
                            url_prefix = '/attendance'
                            page_label = 'attendance'
                        else:
                            url_prefix = '/marks'
                            page_label = 'marks'

                        available_sections = [
                            {
                                'name': cs.section.name,
                                'display': f"Section {cs.section.name}",
                                'url': f"{url_prefix}/{class_number}/{cs.section.name}"
                            }
                            for cs in class_sections
                        ]

                        if available_sections:
                            voice_command.status = VoiceCommand.Status.PENDING_CONFIRMATION
                            voice_command.save()

                            return Response(
                                {
                                    'command_id': voice_command.id,
                                    'transcription': voice_command.transcription,
                                    'intent': 'SELECT_SECTION',
                                    'confirmation_data': {
                                        'message': f"Select a section for Class {class_obj.name} {page_label}",
                                        'class_number': class_number,
                                        'class_name': class_obj.name,
                                        'sections': available_sections,
                                        'needs_confirmation': False
                                    },
                                    'needs_confirmation': False
                                },
                                status=status.HTTP_200_OK
                            )
                        else:
                            # No sections found for this class
                            voice_command.status = VoiceCommand.Status.PENDING_CONFIRMATION
                            voice_command.save()

                            return Response(
                                {
                                    'command_id': voice_command.id,
                                    'transcription': voice_command.transcription,
                                    'intent': 'CLARIFY',
                                    'confirmation_data': {
                                        'message': f'No sections found for Class {class_obj.name}. Please try a different class.',
                                        'needs_confirmation': False
                                    },
                                    'needs_confirmation': False
                                },
                                status=status.HTTP_200_OK
                            )
                    else:
                        # Class not found
                        voice_command.status = VoiceCommand.Status.PENDING_CONFIRMATION
                        voice_command.save()

                        return Response(
                            {
                                'command_id': voice_command.id,
                                'transcription': voice_command.transcription,
                                'intent': 'CLARIFY',
                                'confirmation_data': {
                                    'message': f'Class {class_number} not found. Please try again.',
                                    'needs_confirmation': False
                                },
                                'needs_confirmation': False
                            },
                            status=status.HTTP_200_OK
                        )
                except Exception as e:
                    logger.error(f"Error fetching sections: {str(e)}")

            # Fallback if class number couldn't be extracted
            voice_command.status = VoiceCommand.Status.PENDING_CONFIRMATION
            voice_command.save()

            return Response(
                {
                    'command_id': voice_command.id,
                    'transcription': voice_command.transcription,
                    'intent': 'CLARIFY',
                    'confirmation_data': {
                        'message': 'Please specify a class number. For example: "Open class 1A marks"',
                        'needs_confirmation': False
                    },
                    'needs_confirmation': False
                },
                status=status.HTTP_200_OK
            )

        # Step 2.5: Check for incomplete commands (Section 6 Edge Case)
        completeness = IntentExtractor.check_command_completeness(normalized_text, intent)
        if not completeness['is_complete']:
            logger.warning(f"Incomplete command detected: {completeness['missing']}")
            print(f"Incomplete command: {completeness}", flush=True)

            voice_command.status = VoiceCommand.Status.PENDING_CONFIRMATION
            voice_command.save()

            # Role-aware examples for incomplete commands
            user_role = getattr(request.user, 'role', 'TEACHER')
            if user_role == 'ACCOUNTANT':
                incomplete_examples = [
                    'Fee: "Collect 5000 from roll 12 class 6A cash"',
                    'Reports: "Today\'s collection" or "Show defaulters"',
                    'Navigate: "Open fee collections"',
                ]
            else:
                incomplete_examples = [
                    'Marks: "Update marks for roll 1 maths 90"',
                    'Question: "Question 3 to 8 marks"',
                    'Attendance: "Mark all present"',
                    'Navigate: "Open class 2C marks"',
                ]

            return Response(
                {
                    'command_id': voice_command.id,
                    'transcription': voice_command.transcription,
                    'intent': 'INCOMPLETE',
                    'confirmation_data': {
                        'message': completeness['suggestion'] or 'Your command seems incomplete.',
                        'missing': completeness['missing'],
                        'examples': incomplete_examples,
                        'needs_confirmation': False
                    },
                    'needs_confirmation': False
                },
                status=status.HTTP_200_OK
            )

        # Step 3: Extract entities
        try:
            # Pass context (current page context) to entity extractor
            context = {}
            if context_class and context_section:
                context['class'] = int(context_class)
                context['section'] = context_section.upper()
                logger.info(f"Using page context: class={context_class}, section={context_section}")

            if context_roll_number:
                context['roll_number'] = int(context_roll_number)
                logger.info(f"Using roll_number from context: {context_roll_number}")

            if context_subject_id:
                context['subject_id'] = int(context_subject_id)
                logger.info(f"Using subject_id from context: {context_subject_id}")

            # CRITICAL: Use normalized text for entity extraction
            entities = EntityExtractor.extract_entities(
                normalized_text,
                intent,
                context=context
            )
            logger.info(f"Extracted entities: {entities}")
            voice_command.entities = entities
            voice_command.save()

            # SECTION 14: Check for incomplete batch (some marks missing)
            if 'incomplete' in entities:
                incomplete = entities['incomplete']
                logger.info(f"Batch incomplete: {incomplete}")

                # Return the paired data with info about missing items
                # This allows the user to fill in missing marks without repeating
                return Response(
                    {
                        'command_id': voice_command.id,
                        'transcription': voice_command.transcription,
                        'intent': 'BATCH_INCOMPLETE',
                        'confirmation_data': {
                            'message': incomplete.get('message'),
                            'incomplete_type': incomplete.get('type'),
                            'paired_updates': incomplete.get('paired_updates', []),
                            'missing_questions': incomplete.get('missing_questions', []),
                            'extra_marks': incomplete.get('extra_marks', []),
                            'needs_confirmation': True,
                            'allow_partial_confirm': True,
                        },
                        'needs_confirmation': True
                    },
                    status=status.HTTP_200_OK
                )

        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            voice_command.status = VoiceCommand.Status.FAILED
            voice_command.error_message = f"Entity extraction failed: {str(e)}"
            voice_command.save()
            return Response(
                {'error': 'Failed to extract entities', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Step 4: Prepare confirmation data
        try:
            confirmation_data = CommandExecutor.prepare_confirmation(
                intent,
                entities,
                request.user
            )

            # If the fee page navigation needs section selection, return SELECT_SECTION
            if confirmation_data.get('navigation_type') == 'section_select':
                voice_command.intent = 'SELECT_SECTION'
                voice_command.confirmation_data = confirmation_data
                voice_command.save()

                # Add display field for frontend section buttons
                for sec in confirmation_data.get('sections', []):
                    if 'display' not in sec:
                        sec['display'] = f"Section {sec['name']}"

                return Response(
                    {
                        'command_id': voice_command.id,
                        'transcription': voice_command.transcription,
                        'intent': 'SELECT_SECTION',
                        'confirmation_data': {
                            'message': confirmation_data['message'],
                            'class_number': confirmation_data.get('class'),
                            'class_name': confirmation_data.get('class_name'),
                            'sections': confirmation_data['sections'],
                            'needs_confirmation': False
                        },
                        'needs_confirmation': False
                    },
                    status=status.HTTP_200_OK
                )

            # If fee operation needs student selection, return SELECT_STUDENT
            if confirmation_data.get('navigation_type') == 'student_select':
                voice_command.intent = 'SELECT_STUDENT'
                voice_command.confirmation_data = confirmation_data
                voice_command.save()

                select_data = {
                    'message': confirmation_data['message'],
                    'students': confirmation_data['students'],
                    'needs_confirmation': False,
                }
                # Pass through intent-specific fields
                if 'amount' in confirmation_data:
                    select_data['amount'] = confirmation_data['amount']
                if 'payment_method' in confirmation_data:
                    select_data['payment_method'] = confirmation_data['payment_method']
                if 'intent_type' in confirmation_data:
                    select_data['intent_type'] = confirmation_data['intent_type']

                return Response(
                    {
                        'command_id': voice_command.id,
                        'transcription': voice_command.transcription,
                        'intent': 'SELECT_STUDENT',
                        'confirmation_data': select_data,
                        'needs_confirmation': False
                    },
                    status=status.HTTP_200_OK
                )

            voice_command.confirmation_data = confirmation_data
            voice_command.save()

        except PermissionError as e:
            logger.error(f"Permission denied: {str(e)}")
            voice_command.status = VoiceCommand.Status.FAILED
            voice_command.error_message = str(e)
            voice_command.save()
            return Response(
                {'error': 'Permission denied', 'details': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except ValueError as e:
            error_message = str(e)
            logger.warning(f"Data validation issue: {error_message}")

            # Check if it's a "not found" error - show friendly warning instead of error
            if 'not found' in error_message.lower():
                # Return a friendly warning dialog instead of error
                voice_command.status = VoiceCommand.Status.PENDING_CONFIRMATION
                voice_command.intent = 'DATA_NOT_FOUND'
                voice_command.save()

                return Response(
                    {
                        'command_id': voice_command.id,
                        'transcription': voice_command.transcription,
                        'intent': 'DATA_NOT_FOUND',
                        'confirmation_data': {
                            'message': error_message,
                            'warning_type': 'NOT_FOUND',
                            'suggestions': [
                                'Check if the student/roll number exists in this class',
                                'Make sure you are on the correct class page',
                                'Try saying the command again with the correct details',
                            ],
                            'needs_confirmation': False
                        },
                        'needs_confirmation': False
                    },
                    status=status.HTTP_200_OK
                )

            # For other validation errors, return 400
            voice_command.status = VoiceCommand.Status.FAILED
            voice_command.error_message = error_message
            voice_command.save()
            return Response(
                {
                    'error': 'Invalid command data',
                    'details': error_message,
                    'transcription': voice_command.transcription
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Confirmation preparation failed: {str(e)}")
            voice_command.status = VoiceCommand.Status.FAILED
            voice_command.error_message = f"Preparation failed: {str(e)}"
            voice_command.save()
            return Response(
                {'error': 'Failed to prepare confirmation', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Return success with confirmation data
        return Response(
            {
                'success': True,
                'command_id': voice_command.id,
                'transcription': voice_command.transcription,
                'intent': voice_command.intent,
                'confirmation_data': confirmation_data,
                'message': 'Please review and confirm the command'
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        logger.error(f"Unexpected error in upload_voice_command: {str(e)}")
        return Response(
            {'error': 'Unexpected error occurred', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_voice_command(request, command_id):
    """
    Confirm and execute a voice command.
    Accepts optional 'edited_data' in request body for user-edited marks.
    """
    try:
        # Get voice command
        voice_command = get_object_or_404(
            VoiceCommand,
            id=command_id,
            user=request.user,
            status=VoiceCommand.Status.PENDING_CONFIRMATION
        )

        # Check for edited data from frontend
        edited_data = request.data.get('edited_data')
        if edited_data:
            logger.info(f"Using edited confirmation data: {edited_data}")
            # Merge edited data with original (edited data takes priority)
            confirmation_data = {**voice_command.confirmation_data, **edited_data}
            # Save the edited data for audit trail
            voice_command.confirmation_data = confirmation_data
        else:
            confirmation_data = voice_command.confirmation_data

        # Update status to confirmed
        voice_command.status = VoiceCommand.Status.CONFIRMED
        voice_command.save()

        # Execute command
        try:
            result = CommandExecutor.execute(
                voice_command.intent,
                voice_command.entities,
                confirmation_data,
                request.user
            )

            # Update status to executed
            voice_command.status = VoiceCommand.Status.EXECUTED
            voice_command.save()

            return Response(
                {
                    'success': True,
                    'result': result,
                    'message': 'Command executed successfully'
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            voice_command.status = VoiceCommand.Status.FAILED
            voice_command.error_message = f"Execution failed: {str(e)}"
            voice_command.save()
            return Response(
                {'error': 'Failed to execute command', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except Exception as e:
        logger.error(f"Error in confirm_voice_command: {str(e)}")
        return Response(
            {'error': 'Failed to confirm command', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_voice_command(request, command_id):
    """
    Reject a voice command.
    """
    try:
        voice_command = get_object_or_404(
            VoiceCommand,
            id=command_id,
            user=request.user,
            status=VoiceCommand.Status.PENDING_CONFIRMATION
        )

        voice_command.status = VoiceCommand.Status.REJECTED
        voice_command.save()

        return Response(
            {
                'success': True,
                'message': 'Command rejected'
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        logger.error(f"Error in reject_voice_command: {str(e)}")
        return Response(
            {'error': 'Failed to reject command', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
