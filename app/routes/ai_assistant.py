from flask import Blueprint, render_template, request, jsonify, session, abort
from flask_login import login_required, current_user
from app.extensions import db, csrf
from app.models.baby import BabyProfile
from app.models.ai_chat import AIConversation, AIMessage
from app.services.ai_service import ask_ai_assistant
from app.utils import parent_required, get_active_baby, log_audit

ai_bp = Blueprint('ai', __name__, url_prefix='/ai-assistant')


@ai_bp.route('/')
@login_required
@parent_required
def index():
    """Module 6: AI Healthcare Assistant Interface"""
    babies = current_user.baby_profiles.filter_by(is_active=True).all()
    active_baby = get_active_baby()

    # Get or create active conversation
    conv_id = request.args.get('conv_id', type=int)
    conversation = None
    if conv_id:
        conversation = AIConversation.query.filter_by(id=conv_id, parent_id=current_user.id).first()

    if not conversation:
        conversation = AIConversation.query.filter_by(parent_id=current_user.id).order_by(AIConversation.updated_at.desc()).first()

    past_conversations = AIConversation.query.filter_by(parent_id=current_user.id).order_by(AIConversation.updated_at.desc()).limit(10).all()

    return render_template(
        'ai/assistant.html',
        babies=babies,
        active_baby=active_baby,
        conversation=conversation,
        past_conversations=past_conversations
    )


@ai_bp.route('/ask', methods=['POST'])
@login_required
@parent_required
@csrf.exempt
def ask():
    """Module 6: AI Chat API Endpoint with Context Retrieval and Safety Verification"""
    data = request.get_json(force=True, silent=True) or {}
    user_prompt = data.get('message', '').strip()
    # Safely cast baby_id and conversation_id to int (dict.get() doesn't accept type= kwarg)
    try:
        baby_id = int(data.get('baby_id') or 0) or None
    except (ValueError, TypeError):
        baby_id = None
    authorize_records = bool(data.get('authorize_records', False))
    try:
        conv_id = int(data.get('conversation_id') or 0) or None
    except (ValueError, TypeError):
        conv_id = None

    if not user_prompt:
        return jsonify({'error': 'Please enter a message or question.'}), 400

    # Retrieve baby profile if specified
    baby = None
    if baby_id:
        baby = BabyProfile.query.filter_by(id=baby_id, parent_id=current_user.id, is_active=True).first()

    # Retrieve or create conversation
    if conv_id:
        conversation = AIConversation.query.filter_by(id=conv_id, parent_id=current_user.id).first()
    else:
        conversation = None

    if not conversation:
        title = (user_prompt[:45] + '...') if len(user_prompt) > 45 else user_prompt
        conversation = AIConversation(
            parent_id=current_user.id,
            baby_id=baby.id if baby else None,
            title=title,
            authorized_record_access=authorize_records
        )
        db.session.add(conversation)
        db.session.commit()
    else:
        conversation.authorized_record_access = authorize_records
        if baby:
            conversation.baby_id = baby.id

    # Save User message
    user_msg = AIMessage(
        conversation_id=conversation.id,
        sender='user',
        content=user_prompt
    )
    db.session.add(user_msg)
    db.session.commit()

    # Audit log if sensitive health records were accessed
    if authorize_records and baby:
        log_audit(
            current_user.id,
            'AI_RECORD_CONTEXT_RETRIEVAL',
            f"Authorized AI context retrieval for baby {baby.name} (ID: {baby.id})",
            request.remote_addr
        )

    # Get conversation history for multi-turn context
    history = conversation.messages.order_by(AIMessage.created_at.asc()).all()

    # Call AI service
    ai_result = ask_ai_assistant(
        user_prompt=user_prompt,
        baby=baby,
        authorize_records=authorize_records,
        conversation_history=history
    )

    # Save Assistant message
    assistant_msg = AIMessage(
        conversation_id=conversation.id,
        sender='assistant',
        content=ai_result['answer']
    )
    assistant_msg.suggested_actions = ai_result['suggested_actions']
    db.session.add(assistant_msg)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'conversation_id': conversation.id,
        'answer': ai_result['answer'],
        'articles': ai_result['articles'],
        'suggested_actions': ai_result['suggested_actions'],
        'source': ai_result['source'],
        'baby_name': baby.name if baby else None
    })


@ai_bp.route('/conversations/new', methods=['POST'])
@login_required
@parent_required
@csrf.exempt
def new_conversation():
    """Module 6: Start a Fresh AI Consultation Session"""
    baby = get_active_baby()
    conversation = AIConversation(
        parent_id=current_user.id,
        baby_id=baby.id if baby else None,
        title='New Pediatric Inquiry',
        authorized_record_access=True
    )
    db.session.add(conversation)
    db.session.commit()
    return jsonify({'status': 'success', 'conversation_id': conversation.id})
