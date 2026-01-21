"""
API views for voice processing.
"""
import logging
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
        voice_command.intent = intent
        voice_command.save()

        if intent == 'UNKNOWN':
            # CRITICAL: Return CLARIFY intent instead of 400 error
            # This allows frontend to show helpful message instead of crashing
            voice_command.status = VoiceCommand.Status.PENDING_CONFIRMATION
            voice_command.save()

            return Response(
                {
                    'command_id': voice_command.id,
                    'transcription': voice_command.transcription,
                    'intent': 'CLARIFY',
                    'confirmation_data': {
                        'message': 'I could not understand your command. Please try again with one of these formats:',
                        'examples': [
                            'Single question: "Update question 3 to 8 marks"',
                            'Batch update: "Questions 1, 2, 3 AS 4, 5, 6"',
                            'Natural speech: "For question 1 give 5, for question 2 give 6"',
                            'Range: "Questions 1 to 10 AS 7, 8, 9, 1, 2, 3, 4, 5, 6, 8"'
                        ],
                        'needs_confirmation': False
                    },
                    'needs_confirmation': False
                },
                status=status.HTTP_200_OK  # 200 OK, not 400!
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
            logger.error(f"Invalid data: {str(e)}")
            voice_command.status = VoiceCommand.Status.FAILED
            voice_command.error_message = str(e)
            voice_command.save()
            return Response(
                {
                    'error': 'Invalid command data',
                    'details': str(e),
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
    """
    try:
        # Get voice command
        voice_command = get_object_or_404(
            VoiceCommand,
            id=command_id,
            user=request.user,
            status=VoiceCommand.Status.PENDING_CONFIRMATION
        )

        # Update status to confirmed
        voice_command.status = VoiceCommand.Status.CONFIRMED
        voice_command.save()

        # Execute command
        try:
            result = CommandExecutor.execute(
                voice_command.intent,
                voice_command.entities,
                voice_command.confirmation_data,
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
