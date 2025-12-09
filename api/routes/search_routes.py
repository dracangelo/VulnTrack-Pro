from flask import Blueprint, jsonify, request
from api.services.search_service import SearchService
from api.models.search import SavedSearch
from api.extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity

search_bp = Blueprint('search', __name__, url_prefix='/api/search')

@search_bp.route('/', methods=['GET'])
@jwt_required()
def global_search():
    """
    Global search endpoint.
    Query params:
        q: Search query string
    """
    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'Missing query parameter'}), 400
        
    # Save to history
    current_user_id = get_jwt_identity()
    history_entry = SavedSearch(
        user_id=current_user_id,
        query=query,
        is_history=True
    )
    db.session.add(history_entry)
    db.session.commit()
    
    # Perform search
    results = SearchService.global_search(query)
    return jsonify(results)

@search_bp.route('/saved', methods=['GET'])
@jwt_required()
def get_saved_searches():
    """Get user's saved searches (not history)."""
    current_user_id = get_jwt_identity()
    searches = SavedSearch.query.filter_by(
        user_id=current_user_id,
        is_history=False
    ).order_by(SavedSearch.created_at.desc()).all()
    
    return jsonify([s.to_dict() for s in searches])

@search_bp.route('/saved', methods=['POST'])
@jwt_required()
def create_saved_search():
    """Save a search query/filter."""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'error': 'Missing name'}), 400
        
    saved_search = SavedSearch(
        user_id=current_user_id,
        name=data['name'],
        query=data.get('query'),
        filters=data.get('filters'),
        is_history=False
    )
    db.session.add(saved_search)
    db.session.commit()
    
    return jsonify(saved_search.to_dict()), 201

@search_bp.route('/saved/<int:search_id>', methods=['DELETE'])
@jwt_required()
def delete_saved_search(search_id):
    """Delete a saved search."""
    current_user_id = get_jwt_identity()
    saved_search = SavedSearch.query.filter_by(
        id=search_id,
        user_id=current_user_id
    ).first_or_404()
    
    db.session.delete(saved_search)
    db.session.commit()
    
    return jsonify({'message': 'Saved search deleted'})

@search_bp.route('/history', methods=['GET'])
@jwt_required()
def get_search_history():
    """Get recent search history."""
    current_user_id = get_jwt_identity()
    history = SavedSearch.query.filter_by(
        user_id=current_user_id,
        is_history=True
    ).order_by(SavedSearch.created_at.desc()).limit(10).all()
    
    return jsonify([h.to_dict() for h in history])
